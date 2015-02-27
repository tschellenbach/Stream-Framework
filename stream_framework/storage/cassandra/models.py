from cqlengine import columns
from cqlengine.models import Model
from cqlengine.exceptions import ValidationError
from stream_framework.utils.five import long_t


class VarInt(columns.Column):
    db_type = 'varint'

    def validate(self, value):
        val = super(VarInt, self).validate(value)
        if val is None:
            return
        try:
            return long_t(val)
        except (TypeError, ValueError):
            raise ValidationError(
                "{} can't be converted to integer value".format(value))

    def to_python(self, value):
        return self.validate(value)

    def to_database(self, value):
        return self.validate(value)


class BaseActivity(Model):
    feed_id = columns.Ascii(primary_key=True, partition_key=True)
    activity_id = VarInt(primary_key=True, clustering_order='desc')


class Activity(BaseActivity):
    actor = columns.Integer(required=False)
    extra_context = columns.Bytes(required=False)
    object = columns.Integer(required=False)
    target = columns.Integer(required=False)
    time = columns.DateTime(required=False)
    verb = columns.Integer(required=False)


class AggregatedActivity(BaseActivity):
    activities = columns.Bytes(required=False)
    created_at = columns.DateTime(required=False)
    group = columns.Ascii(required=False)
    updated_at = columns.DateTime(required=False)
