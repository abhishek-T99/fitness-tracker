from django.conf import settings
from django.db import models


def xp_for_level(n: int) -> int:
    """Total XP required to *reach* level n (1-indexed, n >= 1)."""
    if n <= 1:
        return 0
    return int(100 * (n - 1) ** 1.6)


class UserLevel(models.Model):
    class Tier(models.TextChoices):
        ROOKIE   = "rookie",   "Rookie"
        AMATEUR  = "amateur",  "Amateur"
        ATHLETE  = "athlete",  "Athlete"
        WARRIOR  = "warrior",  "Warrior"
        LEGEND   = "legend",   "Legend"
        ELITE    = "elite",    "Elite"
        IMMORTAL = "immortal", "Immortal"

    class AthleteClass(models.TextChoices):
        ROOKIE            = "rookie",            "Rookie"
        IRON_WARRIOR      = "iron_warrior",      "Iron Warrior"
        ROAD_WARRIOR      = "road_warrior",      "Road Warrior"
        FIRE_BREATHER     = "fire_breather",     "Fire Breather"
        SCULPTOR          = "sculptor",          "Sculptor"
        WELLNESS_CHAMPION = "wellness_champion", "Wellness Champion"

    user          = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="level_profile"
    )
    total_xp      = models.PositiveBigIntegerField(default=0)
    level         = models.PositiveIntegerField(default=1)
    tier          = models.CharField(max_length=20, choices=Tier.choices, default=Tier.ROOKIE)
    athlete_class = models.CharField(
        max_length=30, choices=AthleteClass.choices, default=AthleteClass.ROOKIE
    )
    prestige_count = models.PositiveSmallIntegerField(default=0)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Level"

    def __str__(self):
        return f"{self.user} — Lv.{self.level} ({self.tier})"

    @property
    def xp_in_current_level(self) -> int:
        return self.total_xp - xp_for_level(self.level)

    @property
    def xp_for_next_level(self) -> int:
        return xp_for_level(self.level + 1) - xp_for_level(self.level)

    @property
    def xp_progress_pct(self) -> float:
        nxt = self.xp_for_next_level
        if nxt == 0:
            return 100.0
        return round(self.xp_in_current_level / nxt * 100, 1)


class XPTransaction(models.Model):
    class SourceType(models.TextChoices):
        WORKOUT         = "workout",         "Workout"
        PERSONAL_RECORD = "personal_record", "Personal Record"
        NUTRITION       = "nutrition",       "Nutrition"
        MEASUREMENT     = "measurement",     "Measurement"
        GOAL            = "goal",            "Goal"
        ACHIEVEMENT     = "achievement",     "Achievement"
        SOCIAL          = "social",          "Social"
        CHALLENGE       = "challenge",       "Challenge"
        STREAK_BONUS    = "streak_bonus",    "Streak Bonus"

    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="xp_transactions"
    )
    amount      = models.IntegerField(help_text="Final XP after multiplier")
    base_amount = models.IntegerField(help_text="XP before multiplier")
    multiplier  = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    reason      = models.CharField(max_length=200)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    source_id   = models.PositiveIntegerField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "source_type"]),
        ]

    def __str__(self):
        return f"{self.user} +{self.amount} XP — {self.reason}"


class WeeklyChallenge(models.Model):
    class ChallengeType(models.TextChoices):
        COMPLETE_WORKOUTS = "complete_workouts", "Complete workouts"
        LOG_MEALS         = "log_meals",         "Log meals"
        LOG_WATER         = "log_water",         "Log water"
        LOG_MEASUREMENT   = "log_measurement",   "Log measurement"
        RECORD_PR         = "record_pr",         "Set a PR"

    week_start     = models.DateField()
    challenge_type = models.CharField(max_length=30, choices=ChallengeType.choices)
    target_value   = models.PositiveIntegerField(default=1)
    xp_reward      = models.PositiveIntegerField(default=200)
    description    = models.CharField(max_length=200)

    class Meta:
        unique_together = [["week_start", "challenge_type"]]
        ordering = ["week_start", "challenge_type"]

    def __str__(self):
        return f"{self.week_start} — {self.description}"


class UserWeeklyChallenge(models.Model):
    user          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_challenges"
    )
    challenge     = models.ForeignKey(WeeklyChallenge, on_delete=models.CASCADE, related_name="user_progress")
    current_value = models.PositiveIntegerField(default=0)
    completed     = models.BooleanField(default=False)
    completed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [["user", "challenge"]]
        ordering = ["challenge__challenge_type"]

    def __str__(self):
        return (
            f"{self.user} — {self.challenge.description} "
            f"({self.current_value}/{self.challenge.target_value})"
        )
