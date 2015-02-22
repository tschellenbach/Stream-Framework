from stream_framework.activity import Activity
from stream_framework.exceptions import SerializationException
from stream_framework.serializers.activity_serializer import ActivitySerializer
from stream_framework.serializers.utils import check_reserved
from stream_framework.utils import epoch_to_datetime, datetime_to_epoch
from stream_framework.serializers.base import BaseAggregatedSerializer
import six


class AggregatedActivitySerializer(BaseAggregatedSerializer):

    '''
    Optimized version of the Activity serializer for AggregatedActivities

    v3group;;created_at;;updated_at;;seen_at;;read_at;;aggregated_activities

    Main advantage is that it prevents you from increasing the storage of
    a notification without realizing you are adding the extra data

    Depending on dehydrate it will either dump dehydrated aggregated activities
    or store the full aggregated activity
    '''
    #: indicates if dumps returns dehydrated aggregated activities
    dehydrate = True
    identifier = 'v3'
    reserved_characters = [';', ',', ';;']
    date_fields = ['created_at', 'updated_at', 'seen_at', 'read_at']

    activity_serializer_class = ActivitySerializer

    def dumps(self, aggregated):
        self.check_type(aggregated)

        activity_serializer = self.activity_serializer_class(Activity)
        # start by storing the group
        parts = [aggregated.group]
        check_reserved(aggregated.group, [';;'])

        # store the dates
        for date_field in self.date_fields:
            value = getattr(aggregated, date_field)
            if value is not None:
                # keep the milliseconds
                epoch = '%.6f' % datetime_to_epoch(value)
            else:
                epoch = -1
            parts += [epoch]

        # add the activities serialization
        serialized_activities = []
        if self.dehydrate:
            if not aggregated.dehydrated:
                aggregated = aggregated.get_dehydrated()
            serialized_activities = map(str, aggregated._activity_ids)
        else:
            for activity in aggregated.activities:
                serialized = activity_serializer.dumps(activity)
                check_reserved(serialized, [';', ';;'])
                serialized_activities.append(serialized)

        serialized_activities_part = ';'.join(serialized_activities)
        parts.append(serialized_activities_part)

        # add the minified activities
        parts.append(aggregated.minimized_activities)

        # stick everything together
        serialized_aggregated = ';;'.join(map(str, parts))
        serialized = '%s%s' % (self.identifier, serialized_aggregated)
        return serialized

    def loads(self, serialized_aggregated):
        activity_serializer = self.activity_serializer_class(Activity)
        try:
            serialized_aggregated = serialized_aggregated[2:]
            parts = serialized_aggregated.split(';;')
            # start with the group
            group = parts[0]
            aggregated = self.aggregated_activity_class(group)

            # get the date and activities
            date_dict = dict(zip(self.date_fields, parts[1:5]))
            for k, v in date_dict.items():
                date_value = None
                if v != '-1':
                    date_value = epoch_to_datetime(float(v))
                setattr(aggregated, k, date_value)

            # write the activities
            serializations = parts[5].split(';')
            if self.dehydrate:
                activity_ids = list(map(int, serializations))
                aggregated._activity_ids = activity_ids
                aggregated.dehydrated = True
            else:
                activities = [activity_serializer.loads(s)
                              for s in serializations]
                aggregated.activities = activities
                aggregated.dehydrated = False

            # write the minimized activities
            minimized = int(parts[6])
            aggregated.minimized_activities = minimized

            return aggregated
        except Exception as e:
            msg = six.text_type(e)
            raise SerializationException(msg)


class NotificationSerializer(AggregatedActivitySerializer):
    #: indicates if dumps returns dehydrated aggregated activities
    dehydrate = False
