from django.contrib import admin
from django.utils.html import format_html

from .models import ExerciseSet, Routine, RoutineExercise, Workout, WorkoutExercise


class ExerciseSetInline(admin.TabularInline):
    model = ExerciseSet
    extra = 0
    fields = ("set_number", "reps", "weight", "duration_sec")


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 0
    fields = ("order", "exercise", "notes")
    autocomplete_fields = ("exercise",)


class RoutineExerciseInline(admin.TabularInline):
    model = RoutineExercise
    extra = 0
    fields = ("order", "exercise", "target_sets", "target_reps", "rest_sec")
    autocomplete_fields = ("exercise",)


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = (
        "name", "user", "status_badge", "started_at",
        "duration_min", "calories_burned",
    )
    list_filter = ("status",)
    search_fields = ("name", "user__username")
    autocomplete_fields = ("user",)
    date_hierarchy = "started_at"
    ordering = ("-started_at",)
    readonly_fields = ("started_at",)
    inlines = [WorkoutExerciseInline]
    fieldsets = (
        (None, {"fields": ("user", "name", "status")}),
        ("Stats", {"fields": ("started_at", "duration_min", "calories_burned", "notes")}),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            "in_progress": ("#f59e0b", "#fff"),
            "completed": ("#10b981", "#fff"),
            "cancelled": ("#ef4444", "#fff"),
        }
        bg, fg = colours.get(obj.status, ("#94a3b8", "#fff"))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;'
            'border-radius:9999px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display(),
        )


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ("workout", "exercise", "order")
    autocomplete_fields = ("workout", "exercise")
    inlines = [ExerciseSetInline]


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_public", "updated_at")
    list_filter = ("is_public",)
    search_fields = ("name", "user__username")
    autocomplete_fields = ("user",)
    ordering = ("-updated_at",)
    inlines = [RoutineExerciseInline]
