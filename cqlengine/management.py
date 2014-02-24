import json
import warnings
from cqlengine import SizeTieredCompactionStrategy, LeveledCompactionStrategy
from cqlengine.named import NamedTable

from cqlengine.connection import connection_manager, execute
from cqlengine.exceptions import CQLEngineException

import logging
from collections import namedtuple
Field = namedtuple('Field', ['name', 'type'])

logger = logging.getLogger(__name__)


# system keyspaces
schema_columnfamilies = NamedTable('system', 'schema_columnfamilies')


def create_keyspace(name, strategy_class='SimpleStrategy', replication_factor=3, durable_writes=True, **replication_values):
    """
    creates a keyspace

    :param name: name of keyspace to create
    :param strategy_class: keyspace replication strategy class
    :param replication_factor: keyspace replication factor
    :param durable_writes: 1.2 only, write log is bypassed if set to False
    :param **replication_values: 1.2 only, additional values to ad to the replication data map
    """
    with connection_manager() as con:
        keyspaces = con.execute(
            """SELECT keyspace_name FROM system.schema_keyspaces""", {})
        if name not in [r[0] for r in keyspaces]:
            # try the 1.2 method
            replication_map = {
                'class': strategy_class,
                'replication_factor': replication_factor
            }
            replication_map.update(replication_values)

            query = """
            CREATE KEYSPACE {}
            WITH REPLICATION = {}
            """.format(name, json.dumps(replication_map).replace('"', "'"))

            if strategy_class != 'SimpleStrategy':
                query += " AND DURABLE_WRITES = {}".format(
                    'true' if durable_writes else 'false')

            execute(query)


def delete_keyspace(name):
    with connection_manager() as con:
        _, keyspaces = con.execute(
            """SELECT keyspace_name FROM system.schema_keyspaces""", {})
        if name in [r[0] for r in keyspaces]:
            execute("DROP KEYSPACE {}".format(name))


def create_table(model, create_missing_keyspace=True):
    warnings.warn(
        "create_table has been deprecated in favor of sync_table and will be removed in a future release", DeprecationWarning)
    sync_table(model, create_missing_keyspace)


def sync_table(model, create_missing_keyspace=True):

    if model.__abstract__:
        raise CQLEngineException("cannot create table from abstract model")

    # construct query string
    cf_name = model.column_family_name()
    raw_cf_name = model.column_family_name(include_keyspace=False)

    ks_name = model._get_keyspace()
    # create missing keyspace
    if create_missing_keyspace:
        create_keyspace(ks_name)

    with connection_manager() as con:
        tables = con.execute(
            "SELECT columnfamily_name from system.schema_columnfamilies WHERE keyspace_name = %(ks_name)s",
            {'ks_name': ks_name}
        )
    tables = [x.columnfamily_name for x in tables]

    # check for an existing column family
    if raw_cf_name not in tables:
        qs = get_create_table(model)

        try:
            execute(qs)
        except CQLEngineException as ex:
            # 1.2 doesn't return cf names, so we have to examine the exception
            # and ignore if it says the column family already exists
            if "Cannot add already existing column family" not in unicode(ex):
                raise
    else:
        # see if we're missing any columns
        fields = get_fields(model)
        field_names = [x.name for x in fields]
        for name, col in model._columns.items():
            if col.primary_key or col.partition_key:
                continue  # we can't mess with the PK
            if col.db_field_name in field_names:
                continue  # skip columns already defined

            # add missing column using the column def
            query = "ALTER TABLE {} add {}".format(
                cf_name, col.get_column_def())
            logger.debug(query)
            execute(query)

        update_compaction(model)

    # get existing index names, skip ones that already exist
    with connection_manager() as con:
        idx_names = con.execute(
            "SELECT index_name from system.\"IndexInfo\" WHERE table_name=%(table_name)s",
            {'table_name': raw_cf_name}
        )

    idx_names = [i.index_name for i in idx_names]
    idx_names = filter(None, idx_names)

    indexes = [c for n, c in model._columns.items() if c.index]
    if indexes:
        for column in indexes:
            if column.db_index_name in idx_names:
                continue
            qs = ['CREATE INDEX index_{}_{}'.format(
                raw_cf_name, column.db_field_name)]
            qs += ['ON {}'.format(cf_name)]
            qs += ['("{}")'.format(column.db_field_name)]
            qs = ' '.join(qs)

            try:
                execute(qs)
            except CQLEngineException:
                # index already exists
                pass


def get_create_table(model):
    cf_name = model.column_family_name()
    qs = ['CREATE TABLE {}'.format(cf_name)]

    # add column types
    pkeys = []  # primary keys
    ckeys = []  # clustering keys
    qtypes = []  # field types

    def add_column(col):
        s = col.get_column_def()
        if col.primary_key:
            keys = (pkeys if col.partition_key else ckeys)
            keys.append('"{}"'.format(col.db_field_name))
        qtypes.append(s)
    for name, col in model._columns.items():
        add_column(col)

    qtypes.append('PRIMARY KEY (({}){})'.format(
        ', '.join(pkeys), ckeys and ', ' + ', '.join(ckeys) or ''))

    qs += ['({})'.format(', '.join(qtypes))]

    with_qs = ['read_repair_chance = {}'.format(model.__read_repair_chance__)]

    _order = ['"{}" {}'.format(c.db_field_name, c.clustering_order or 'ASC')
              for c in model._clustering_keys.values()]

    if _order:
        with_qs.append('clustering order by ({})'.format(', '.join(_order)))

    compaction_options = get_compaction_options(model)

    if compaction_options:
        compaction_options = json.dumps(compaction_options).replace('"', "'")
        with_qs.append("compaction = {}".format(compaction_options))

    # add read_repair_chance
    qs += ['WITH {}'.format(' AND '.join(with_qs))]

    qs = ' '.join(qs)
    return qs


def get_compaction_options(model):
    """
    Generates dictionary (later converted to a string) for creating and altering
    tables with compaction strategy

    :param model:
    :return:
    """
    if not model.__compaction__:
        return {}

    result = {'class': model.__compaction__}

    def setter(key, limited_to_strategy=None):
        """
        sets key in result, checking if the key is limited to either SizeTiered or Leveled
        :param key: one of the compaction options, like "bucket_high"
        :param limited_to_strategy: SizeTieredCompactionStrategy, LeveledCompactionStrategy
        :return:
        """
        mkey = "__compaction_{}__".format(key)
        tmp = getattr(model, mkey)
        if tmp and limited_to_strategy and limited_to_strategy != model.__compaction__:
            raise CQLEngineException(
                "{} is limited to {}".format(key, limited_to_strategy))

        if tmp:
            result[key] = tmp

    setter('tombstone_compaction_interval')

    setter('bucket_high', SizeTieredCompactionStrategy)
    setter('bucket_low', SizeTieredCompactionStrategy)
    setter('max_threshold', SizeTieredCompactionStrategy)
    setter('min_threshold', SizeTieredCompactionStrategy)
    setter('min_sstable_size', SizeTieredCompactionStrategy)

    setter("sstable_size_in_mb", LeveledCompactionStrategy)

    return result


def get_fields(model):
    # returns all fields that aren't part of the PK
    ks_name = model._get_keyspace()
    col_family = model.column_family_name(include_keyspace=False)

    with connection_manager() as con:
        query = "SELECT column_name, validator FROM system.schema_columns \
                 WHERE keyspace_name = %(ks_name)s AND columnfamily_name = %(col_family)s"

        logger.debug("get_fields %s %s", ks_name, col_family)

        results = con.execute(
            query, {'ks_name': ks_name, 'col_family': col_family})
    return [Field(x.column_name, x.validator) for x in results]
    # convert to Field named tuples


def get_table_settings(model):
    return schema_columnfamilies.get(keyspace_name=model._get_keyspace(),
                                     columnfamily_name=model.column_family_name(include_keyspace=False))


def update_compaction(model):
    logger.debug("Checking %s for compaction differences", model)
    row = get_table_settings(model)
    # check compaction_strategy_class
    if not model.__compaction__:
        return

    do_update = not row['compaction_strategy_class'].endswith(
        model.__compaction__)

    existing_options = row['compaction_strategy_options']
    existing_options = json.loads(existing_options)

    desired_options = get_compaction_options(model)
    desired_options.pop('class', None)

    for k, v in desired_options.items():
        val = existing_options.pop(k, None)
        if val != v:
            do_update = True

    # check compaction_strategy_options
    if do_update:
        options = get_compaction_options(model)
        # jsonify
        options = json.dumps(options).replace('"', "'")
        cf_name = model.column_family_name()
        query = "ALTER TABLE {} with compaction = {}".format(cf_name, options)
        logger.debug(query)
        execute(query)


def delete_table(model):
    warnings.warn(
        "delete_table has been deprecated in favor of drop_table()", DeprecationWarning)
    return drop_table(model)


def drop_table(model):

    # don't try to delete non existant tables
    ks_name = model._get_keyspace()
    with connection_manager() as con:
        tables = con.execute(
            "SELECT columnfamily_name from system.schema_columnfamilies WHERE keyspace_name = %(ks_name)s",
            {'ks_name': ks_name}
        )
    raw_cf_name = model.column_family_name(include_keyspace=False)
    if raw_cf_name not in [t[0] for t in tables]:
        return

    cf_name = model.column_family_name()
    execute('drop table {};'.format(cf_name))
