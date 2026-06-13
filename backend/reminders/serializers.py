from rest_framework import serializers

from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = [
            "id",
            "title",
            "reminder_type",
            "recurrence_type",
            # once-per-day
            "time_of_day",
            # interval
            "start_time",
            "end_time",
            "interval_minutes",
            # common
            "days_of_week",
            "is_active",
            "notes",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        recurrence = attrs.get(
            "recurrence_type",
            getattr(self.instance, "recurrence_type", Reminder.Recurrence.ONCE),
        )

        if recurrence == Reminder.Recurrence.ONCE:
            time_of_day = attrs.get("time_of_day") or getattr(self.instance, "time_of_day", None)
            if not time_of_day:
                raise serializers.ValidationError(
                    {"time_of_day": "Required for once-per-day reminders."}
                )

        elif recurrence == Reminder.Recurrence.INTERVAL:
            start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
            end   = attrs.get("end_time")   or getattr(self.instance, "end_time",   None)
            mins  = attrs.get("interval_minutes") or getattr(self.instance, "interval_minutes", None)

            errors = {}
            if not start:
                errors["start_time"] = "Required for interval reminders."
            if not end:
                errors["end_time"] = "Required for interval reminders."
            if not mins:
                errors["interval_minutes"] = "Required for interval reminders."
            if errors:
                raise serializers.ValidationError(errors)

            if start and end and start >= end:
                raise serializers.ValidationError(
                    {"end_time": "End time must be after start time."}
                )

        return attrs
