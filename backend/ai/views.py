from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .budgets import BudgetExceeded
from .client import AIUnavailable
from .prompts.nutrition_parse import SYSTEM_PROMPT as NUTRITION_PARSE_PROMPT
from .runner import run_agent
from .serializers import (
    NutritionParseRequestSerializer,
    NutritionParseResponseSerializer,
)


NUTRITION_TOOLS = [
    "get_current_datetime",
    "search_foods",
    "create_food",
    "create_meal",
    "create_water_log",
]


@extend_schema(
    tags=["AI"],
    summary="Parse a natural-language nutrition message into log entries",
    request=NutritionParseRequestSerializer,
    responses={200: NutritionParseResponseSerializer},
)
class NutritionParseView(APIView):
    """POST a short message ('two boiled eggs and 500 ml water') and the
    agent will search the food catalogue and create the matching Meal and
    WaterLog records, returning IDs for optimistic UI updates and undo.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        req = NutritionParseRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        text = req.validated_data["text"].strip()
        date = req.validated_data.get("date")

        if not text:
            return Response(
                {"detail": "Empty input."}, status=status.HTTP_400_BAD_REQUEST
            )

        user_message = text
        if date is not None:
            user_message = f"target_date={date.isoformat()}\n\n{text}"

        try:
            result = run_agent(
                user=request.user,
                feature="nutrition_parse",
                system_prompt=NUTRITION_PARSE_PROMPT,
                user_message=user_message,
                tool_names=NUTRITION_TOOLS,
                max_tokens=4096,
                max_steps=10,
            )
        except AIUnavailable as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except BudgetExceeded as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        body = {
            "session_id": result.session_id,
            "status": result.status,
            "summary": result.summary or "Done.",
            "created": {
                "meal_ids": result.structured["created_meal_ids"],
                "water_log_ids": result.structured["created_water_log_ids"],
                "food_ids": result.structured["created_food_ids"],
            },
        }
        return Response(body, status=status.HTTP_200_OK)
