from cqlengine import columns
from cqlengine.models import Model
from cqlengine.exceptions import ValidationError


class VarInt(columns.Column):
    db_type = 'varint'

    def validate(self, value):
        val = super(VarInt, self).validate(value)
        if val is None:
            return
        try:
            return long(val)
        except (TypeError, ValueError):
            raise ValidationError(
                "{} can't be converted to integer value".format(value))

    def to_python(self, value):
        return self.validate(value)

    def to_database(self, value):
        return self.validate(value)


class Activity(Model):
    # partition key (1 row per user_id)
    feed_id = columns.Text(primary_key=True)
    # clustering key (used for sorting)
    activity_id = VarInt(primary_key=True)
    actor = columns.Integer(required=False)
    entity_id = columns.Integer(required=False)
    extra_context = columns.Bytes(required=False)
    object = columns.Integer(required=False)
    target = columns.Integer(required=False)
    time = columns.DateTime(required=False)
    verb = columns.Integer(required=False)
