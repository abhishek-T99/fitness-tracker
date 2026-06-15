import datetime as dt

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import MealPlan, MealPlanItem
from .serializers import MealPlanItemSerializer, MealPlanSerializer
from .services import generate_plan


@extend_schema(tags=["Meal Plans"])
class MealPlanViewSet(viewsets.ModelViewSet):
    serializer_class   = MealPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = MealPlan.objects.filter(user=self.request.user).prefetch_related("items__food")
        week_start = self.request.query_params.get("week_start")
        if week_start:
            qs = qs.filter(week_start=week_start)
        return qs

    # ── Generate ──────────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        plan = self.get_object()
        try:
            generate_plan(plan)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        plan.refresh_from_db()
        return Response(self.get_serializer(plan).data)

    # ── Log day ───────────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="log-day")
    def log_day(self, request, pk=None):
        from nutrition.models import Meal, MealItem

        plan = self.get_object()
        day  = request.data.get("day")

        if day is None:
            return Response({"detail": "day is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            day = int(day)
        except (TypeError, ValueError):
            return Response({"detail": "day must be 0–6."}, status=status.HTTP_400_BAD_REQUEST)

        items = plan.items.filter(day=day).select_related("food")
        if not items.exists():
            return Response(
                {"detail": f"No items planned for day {day}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine date: override or derive from week_start
        date_str = request.data.get("date")
        if date_str:
            try:
                log_date = dt.date.fromisoformat(date_str)
            except ValueError:
                return Response({"detail": "Invalid date."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            log_date = plan.week_start + dt.timedelta(days=day)

        meal_hours = {"breakfast": 7, "lunch": 12, "dinner": 19, "snack": 16}
        groups: dict = {}
        for item in items:
            groups.setdefault(item.meal_type, []).append(item)

        meal_ids = []
        for meal_type, plan_items in groups.items():
            consumed_at = timezone.make_aware(
                dt.datetime.combine(log_date, dt.time(hour=meal_hours.get(meal_type, 12)))
            )
            meal = Meal.objects.create(
                user=request.user, meal_type=meal_type, consumed_at=consumed_at
            )
            for pi in plan_items:
                MealItem.objects.create(meal=meal, food=pi.food, servings=pi.servings)
            meal_ids.append(meal.id)

        return Response(
            {"detail": f"Logged {len(meal_ids)} meals.", "meal_ids": meal_ids},
            status=status.HTTP_201_CREATED,
        )

    # ── Summary (heatmap data) ────────────────────────────────────────────────

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        plan    = self.get_object()
        profile = getattr(request.user, "profile", None)
        cal_target  = float(getattr(profile, "daily_calorie_goal", None) or 2000)
        prot_target = cal_target * 0.30 / 4

        items = list(plan.items.select_related("food"))
        days  = []
        for d in range(7):
            di = [it for it in items if it.day == d]
            cal  = sum(it.calories  for it in di)
            prot = sum(it.protein_g for it in di)
            carb = sum(it.carbs_g   for it in di)
            fat  = sum(it.fat_g     for it in di)
            days.append({
                "day":         d,
                "calories":    round(cal,  1),
                "protein_g":   round(prot, 1),
                "carbs_g":     round(carb, 1),
                "fat_g":       round(fat,  1),
                "calorie_pct": round(cal  / cal_target  * 100, 1) if cal_target  else 0,
                "protein_pct": round(prot / prot_target * 100, 1) if prot_target else 0,
            })

        return Response({
            "plan_id":        plan.id,
            "cal_target":     cal_target,
            "protein_target": round(prot_target, 1),
            "days":           days,
        })


@extend_schema(tags=["Meal Plans"])
class MealPlanItemViewSet(viewsets.ModelViewSet):
    """Nested: add/list items for a specific plan."""

    serializer_class   = MealPlanItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names  = ["get", "post", "patch", "delete", "head", "options"]

    def _get_plan(self):
        try:
            return MealPlan.objects.get(pk=self.kwargs["plan_pk"], user=self.request.user)
        except MealPlan.DoesNotExist:
            raise NotFound()

    def get_queryset(self):
        return self._get_plan().items.select_related("food")

    def perform_create(self, serializer):
        serializer.save(plan=self._get_plan())


@extend_schema(tags=["Meal Plans"])
class StandaloneMealPlanItemViewSet(viewsets.ModelViewSet):
    """Flat PATCH / DELETE on a single item — used for inline edit and drag-drop."""

    serializer_class   = MealPlanItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names  = ["patch", "delete", "head", "options"]

    def get_queryset(self):
        return MealPlanItem.objects.filter(
            plan__user=self.request.user
        ).select_related("food")
