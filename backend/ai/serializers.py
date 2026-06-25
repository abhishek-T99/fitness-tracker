from rest_framework import serializers


class NutritionParseRequestSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)
    date = serializers.DateField(required=False, allow_null=True)


class CreatedIdsSerializer(serializers.Serializer):
    meal_ids = serializers.ListField(child=serializers.IntegerField())
    water_log_ids = serializers.ListField(child=serializers.IntegerField())
    food_ids = serializers.ListField(child=serializers.IntegerField())


class NutritionParseResponseSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    status = serializers.CharField()
    summary = serializers.CharField(allow_blank=True)
    created = CreatedIdsSerializer()
