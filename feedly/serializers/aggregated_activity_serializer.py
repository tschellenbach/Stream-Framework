from feedly.activity import Activity, AggregatedActivity
from feedly.serializers.love_activity_serializer import LoveActivitySerializer
from feedly.utils import epoch_to_datetime, datetime_to_epoch
from feedly.serializers.utils import check_reserved


class AggregatedActivitySerializer(LoveActivitySerializer):
    '''
    Optimized version of the Activity serializer for AggregatedActivities
    
    v3group;;first_seen;;last_seen;;seen_at;;read_at;;aggregated_activities
    
    Main advantage is that it prevents you from increasing the storage of
    a notification without realizing you are adding the extra data
    '''
    identifier = 'v3'
    reserved_characters = [';', ',', ';;']
    date_fields = ['first_seen', 'last_seen', 'seen_at', 'read_at']
    
    def dumps(self, aggregated):
        #start by storing the group
        parts = [aggregated.group]
        check_reserved(aggregated.group, [';;'])
        
        #store the dates
        for date_field in self.date_fields:
            value = getattr(aggregated, date_field)
            epoch = datetime_to_epoch(value) if value is not None else -1
            parts += [epoch]
            
        # add the activities serialization
        serialized_activities = []
        for activity in aggregated.activities:
            serialized = LoveActivitySerializer.dumps(self, activity)
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
        serialized_aggregated = serialized_aggregated[2:]
        parts = serialized_aggregated.split(';;')
        # start with the group
        group = parts[0]
        aggregated = AggregatedActivity(group)
        
        # get the date and activities
        date_dict = dict(zip(self.date_fields, parts[1:5]))
        for k, v in date_dict.items():
            date_value = None
            if v != '-1':
                date_value = epoch_to_datetime(float(v))
            setattr(aggregated, k, date_value)
        
        # write the activities
        serializations = parts[5].split(';')
        activities = [LoveActivitySerializer.loads(self, s) for s in serializations]
        aggregated.activities = activities
        
        # write the minimized activities
        minimized = int(parts[6])
        aggregated.minimized_activities = minimized
        
        return aggregated
