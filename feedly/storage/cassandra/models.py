from cqlengine import columns
from cqlengine.models import Model

class Activity(Model):
	read_repair_chance = 0.05
	user_id = columns.Text(primary_key=True)
	activity_id = columns.Integer(primary_key=True)
	actor = columns.Text(required=False)
	entity_id = columns.Text(required=False)
	extra_context = columns.Text(required=False)
	object = columns.Text(required=False)
	target = columns.Text(required=False)
	time = columns.Text(required=False)
	verb = columns.Text(required=False)
