from cqlengine import columns
from cqlengine.models import Model

class Activity(Model):
    user_id = columns.Text(primary_key=True)        # partition key (1 row per user_id)
    activity_id = columns.Integer(primary_key=True) # clustering key (used for sorting)
    actor = columns.Text(required=False)
    entity_id = columns.Text(required=False)
    extra_context = columns.Text(required=False)
    object = columns.Text(required=False)
    target = columns.Text(required=False)
    time = columns.Text(required=False)
    verb = columns.Text(required=False)
