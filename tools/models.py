from django.db import models


class ToolUsage(models.Model):
    tool_id = models.CharField(max_length=50)
    session_key = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tool Usage"
        verbose_name_plural = "Tool Usages"

    def __str__(self):
        return f"{self.tool_id} @ {self.created_at:%Y-%m-%d %H:%M}"


class HabitEntry(models.Model):
    session_key = models.CharField(max_length=100)
    habit_id = models.CharField(max_length=50)
    habit_name = models.CharField(max_length=200)
    day = models.PositiveSmallIntegerField()  # 1–30
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('session_key', 'habit_id', 'day')
        verbose_name = "Habit Entry"

    def __str__(self):
        return f"{self.habit_id} day {self.day} – {'✓' if self.done else '✗'}"


class TelemedicineConsultation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'অপেক্ষমান'),
        ('confirmed', 'নিশ্চিত'),
        ('completed', 'সম্পন্ন'),
        ('cancelled', 'বাতিল'),
    ]
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    age = models.CharField(max_length=10, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    chief_complaint = models.TextField(help_text="সমস্যা বা লক্ষণ")
    preferred_time = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Telemedicine Consultation"
        verbose_name_plural = "Telemedicine Consultations"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.status}"
