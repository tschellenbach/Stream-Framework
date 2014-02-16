import copy
import json
from time import sleep
from mock import patch, MagicMock
from cqlengine import Model, columns, SizeTieredCompactionStrategy, LeveledCompactionStrategy
from cqlengine.exceptions import CQLEngineException
from cqlengine.management import get_compaction_options, drop_table, sync_table, get_table_settings
from cqlengine.tests.base import BaseCassEngTestCase


class CompactionModel(Model):
    __compaction__ = None
    cid = columns.UUID(primary_key=True)
    name = columns.Text()


class BaseCompactionTest(BaseCassEngTestCase):
    def assert_option_fails(self, key):
        # key is a normal_key, converted to
        # __compaction_key__

        key = "__compaction_{}__".format(key)

        with patch.object(self.model, key, 10), \
             self.assertRaises(CQLEngineException):
            get_compaction_options(self.model)


class SizeTieredCompactionTest(BaseCompactionTest):

    def setUp(self):
        self.model = copy.deepcopy(CompactionModel)
        self.model.__compaction__ = SizeTieredCompactionStrategy

    def test_size_tiered(self):
        result = get_compaction_options(self.model)
        assert result['class'] == SizeTieredCompactionStrategy

    def test_min_threshold(self):
        self.model.__compaction_min_threshold__ = 2
        result = get_compaction_options(self.model)
        assert result['min_threshold'] == 2


class LeveledCompactionTest(BaseCompactionTest):
    def setUp(self):
        self.model = copy.deepcopy(CompactionLeveledStrategyModel)

    def test_simple_leveled(self):
        result = get_compaction_options(self.model)
        assert result['class'] == LeveledCompactionStrategy

    def test_bucket_high_fails(self):
        self.assert_option_fails('bucket_high')

    def test_bucket_low_fails(self):
        self.assert_option_fails('bucket_low')

    def test_max_threshold_fails(self):
        self.assert_option_fails('max_threshold')

    def test_min_threshold_fails(self):
        self.assert_option_fails('min_threshold')

    def test_min_sstable_size_fails(self):
        self.assert_option_fails('min_sstable_size')

    def test_sstable_size_in_mb(self):
        with patch.object(self.model, '__compaction_sstable_size_in_mb__', 32):
            result = get_compaction_options(self.model)

        assert result['sstable_size_in_mb'] == 32


class LeveledcompactionTestTable(Model):
    __compaction__ = LeveledCompactionStrategy
    __compaction_sstable_size_in_mb__ = 64

    user_id = columns.UUID(primary_key=True)
    name = columns.Text()

from cqlengine.management import schema_columnfamilies

class AlterTableTest(BaseCassEngTestCase):

    def test_alter_is_called_table(self):
        drop_table(LeveledcompactionTestTable)
        sync_table(LeveledcompactionTestTable)
        with patch('cqlengine.management.update_compaction') as mock:
            sync_table(LeveledcompactionTestTable)
        assert mock.called == 1

    def test_alter_actually_alters(self):
        tmp = copy.deepcopy(LeveledcompactionTestTable)
        drop_table(tmp)
        sync_table(tmp)
        tmp.__compaction__ = SizeTieredCompactionStrategy
        tmp.__compaction_sstable_size_in_mb__ = None
        sync_table(tmp)

        table_settings = get_table_settings(tmp)

        self.assertRegexpMatches(table_settings['compaction_strategy_class'], '.*SizeTieredCompactionStrategy$')


    def test_alter_options(self):

        class AlterTable(Model):
            __compaction__ = LeveledCompactionStrategy
            __compaction_sstable_size_in_mb__ = 64

            user_id = columns.UUID(primary_key=True)
            name = columns.Text()

        drop_table(AlterTable)
        sync_table(AlterTable)
        AlterTable.__compaction_sstable_size_in_mb__ = 128
        sync_table(AlterTable)



class EmptyCompactionTest(BaseCassEngTestCase):
    def test_empty_compaction(self):
        class EmptyCompactionModel(Model):
            __compaction__ = None
            cid = columns.UUID(primary_key=True)
            name = columns.Text()

        result = get_compaction_options(EmptyCompactionModel)
        self.assertEqual({}, result)


class CompactionLeveledStrategyModel(Model):
    __compaction__ = LeveledCompactionStrategy
    cid = columns.UUID(primary_key=True)
    name = columns.Text()


class CompactionSizeTieredModel(Model):
    __compaction__ = SizeTieredCompactionStrategy
    cid = columns.UUID(primary_key=True)
    name = columns.Text()



class OptionsTest(BaseCassEngTestCase):

    def test_all_size_tiered_options(self):
        class AllSizeTieredOptionsModel(Model):
            __compaction__ = SizeTieredCompactionStrategy
            __compaction_bucket_low__ = .3
            __compaction_bucket_high__ = 2
            __compaction_min_threshold__ = 2
            __compaction_max_threshold__ = 64
            __compaction_tombstone_compaction_interval__ = 86400

            cid = columns.UUID(primary_key=True)
            name = columns.Text()

        drop_table(AllSizeTieredOptionsModel)
        sync_table(AllSizeTieredOptionsModel)

        settings = get_table_settings(AllSizeTieredOptionsModel)
        options = json.loads(settings['compaction_strategy_options'])
        expected = {u'min_threshold': u'2',
                    u'bucket_low': u'0.3',
                    u'tombstone_compaction_interval': u'86400',
                    u'bucket_high': u'2',
                    u'max_threshold': u'64'}
        self.assertDictEqual(options, expected)


    def test_all_leveled_options(self):

        class AllLeveledOptionsModel(Model):
            __compaction__ = LeveledCompactionStrategy
            __compaction_sstable_size_in_mb__ = 64

            cid = columns.UUID(primary_key=True)
            name = columns.Text()

        drop_table(AllLeveledOptionsModel)
        sync_table(AllLeveledOptionsModel)

        settings = get_table_settings(AllLeveledOptionsModel)
        options = json.loads(settings['compaction_strategy_options'])
        self.assertDictEqual(options, {u'sstable_size_in_mb': u'64'})

