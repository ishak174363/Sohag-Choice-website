from django.contrib import admin
from .models import ToolUsage, HabitEntry, TelemedicineConsultation


@admin.register(ToolUsage)
class ToolUsageAdmin(admin.ModelAdmin):
    list_display = ('tool_id', 'session_key', 'created_at')
    list_filter = ('tool_id', 'created_at')
    search_fields = ('tool_id', 'session_key')


@admin.register(HabitEntry)
class HabitEntryAdmin(admin.ModelAdmin):
    list_display = ('habit_id', 'habit_name', 'day', 'done', 'updated_at')
    list_filter = ('habit_id', 'done')
    search_fields = ('habit_name', 'session_key')


@admin.register(TelemedicineConsultation)
class TelemedicineConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'age', 'gender', 'preferred_time', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'chief_complaint')
    list_editable = ('status',)
