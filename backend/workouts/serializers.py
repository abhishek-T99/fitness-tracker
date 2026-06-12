from django.db import transaction
from rest_framework import serializers

from exercises.serializers import ExerciseSerializer

from .models import ExerciseSet, Routine, RoutineExercise, Workout, WorkoutExercise


class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = [
            "id",
            "set_number",
            "reps",
            "weight",
            "duration_sec",
            "distance_m",
            "rpe",
            "is_warmup",
            "completed",
        ]


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source="exercise", read_only=True)
    sets = ExerciseSetSerializer(many=True)

    class Meta:
        model = WorkoutExercise
        fields = ["id", "exercise", "exercise_detail", "order", "notes", "sets"]


class WorkoutSerializer(serializers.ModelSerializer):
    exercises = WorkoutExerciseSerializer(many=True)
    total_volume = serializers.FloatField(read_only=True)

    class Meta:
        model = Workout
        fields = [
            "id",
            "routine",
            "name",
            "notes",
            "started_at",
            "ended_at",
            "duration_min",
            "calories_burned",
            "perceived_exertion",
            "status",
            "total_volume",
            "exercises",
            "created_at",
        ]
        read_only_fields = ["created_at", "total_volume"]

    def _write_exercises(self, workout, exercises_data):
        for ex_idx, ex_data in enumerate(exercises_data):
            sets_data = ex_data.pop("sets", [])
            we = WorkoutExercise.objects.create(
                workout=workout,
                order=ex_data.get("order", ex_idx),
                **{k: v for k, v in ex_data.items() if k != "order"},
            )
            for set_idx, set_data in enumerate(sets_data):
                ExerciseSet.objects.create(
                    workout_exercise=we,
                    set_number=set_data.get("set_number", set_idx + 1),
                    **{k: v for k, v in set_data.items() if k != "set_number"},
                )

    @transaction.atomic
    def create(self, validated_data):
        exercises_data = validated_data.pop("exercises", [])
        workout = Workout.objects.create(user=self.context["request"].user, **validated_data)
        self._write_exercises(workout, exercises_data)
        return workout

    @transaction.atomic
    def update(self, instance, validated_data):
        exercises_data = validated_data.pop("exercises", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if exercises_data is not None:
            instance.exercises.all().delete()
            self._write_exercises(instance, exercises_data)
        return instance


class RoutineExerciseSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source="exercise", read_only=True)

    class Meta:
        model = RoutineExercise
        fields = [
            "id",
            "exercise",
            "exercise_detail",
            "order",
            "target_sets",
            "target_reps",
            "target_weight",
            "target_duration_sec",
            "rest_sec",
            "notes",
        ]


class RoutineSerializer(serializers.ModelSerializer):
    items = RoutineExerciseSerializer(many=True)

    class Meta:
        model = Routine
        fields = [
            "id",
            "name",
            "description",
            "is_public",
            "estimated_duration_min",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def _write_items(self, routine, items_data):
        for idx, item in enumerate(items_data):
            RoutineExercise.objects.create(
                routine=routine,
                order=item.get("order", idx),
                **{k: v for k, v in item.items() if k != "order"},
            )

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        routine = Routine.objects.create(user=self.context["request"].user, **validated_data)
        self._write_items(routine, items_data)
        return routine

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            self._write_items(instance, items_data)
        return instance
