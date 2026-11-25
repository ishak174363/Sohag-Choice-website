from rest_framework import serializers
from .models import HabitEntry, TelemedicineConsultation


class HabitEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitEntry
        fields = ['habit_id', 'habit_name', 'day', 'done']


class TelemedicineConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineConsultation
        fields = ['id', 'name', 'phone', 'age', 'gender', 'chief_complaint', 'preferred_time', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
