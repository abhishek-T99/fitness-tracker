from django.contrib import admin

from .models import ExerciseSet, Routine, RoutineExercise, Workout, WorkoutExercise


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 0


class ExerciseSetInline(admin.TabularInline):
    model = ExerciseSet
    extra = 0


class RoutineExerciseInline(admin.TabularInline):
    model = RoutineExercise
    extra = 0


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "started_at", "status", "duration_min")
    list_filter = ("status",)
    search_fields = ("name", "user__username")
    inlines = [WorkoutExerciseInline]


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ("workout", "exercise", "order")
    inlines = [ExerciseSetInline]


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_public", "updated_at")
    list_filter = ("is_public",)
    inlines = [RoutineExerciseInline]
