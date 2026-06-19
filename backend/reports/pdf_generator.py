"""Generate a styled fitness report PDF using ReportLab Platypus."""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand palette ─────────────────────────────────────────────────────────────
BRAND     = colors.HexColor("#6366f1")   # indigo-500
BRAND_DRK = colors.HexColor("#4f46e5")   # indigo-600
BRAND_LT  = colors.HexColor("#e0e7ff")   # indigo-100
SLATE_800 = colors.HexColor("#1e293b")
SLATE_600 = colors.HexColor("#475569")
SLATE_400 = colors.HexColor("#94a3b8")
GREEN     = colors.HexColor("#22c55e")
RED       = colors.HexColor("#ef4444")
WHITE     = colors.white


def _styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Helvetica-Bold", fontSize=26,
            textColor=WHITE, alignment=TA_CENTER, leading=32,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="Helvetica", fontSize=12,
            textColor=colors.HexColor("#c7d2fe"), alignment=TA_CENTER, leading=18,
        ),
        "section_heading": ParagraphStyle(
            "section_heading", fontName="Helvetica-Bold", fontSize=13,
            textColor=BRAND_DRK, spaceBefore=16, spaceAfter=6,
        ),
        "stat_label": ParagraphStyle(
            "stat_label", fontName="Helvetica", fontSize=9,
            textColor=SLATE_600, alignment=TA_CENTER,
        ),
        "stat_value": ParagraphStyle(
            "stat_value", fontName="Helvetica-Bold", fontSize=20,
            textColor=SLATE_800, alignment=TA_CENTER, leading=24,
        ),
        "stat_unit": ParagraphStyle(
            "stat_unit", fontName="Helvetica", fontSize=9,
            textColor=SLATE_400, alignment=TA_CENTER,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10,
            textColor=SLATE_600, leading=14,
        ),
        "badge": ParagraphStyle(
            "badge", fontName="Helvetica-Bold", fontSize=9,
            textColor=BRAND_DRK,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=8,
            textColor=SLATE_400, alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "table_header", fontName="Helvetica-Bold", fontSize=9,
            textColor=WHITE,
        ),
        "table_cell": ParagraphStyle(
            "table_cell", fontName="Helvetica", fontSize=9,
            textColor=SLATE_800,
        ),
        "table_cell_right": ParagraphStyle(
            "table_cell_right", fontName="Helvetica", fontSize=9,
            textColor=SLATE_800, alignment=TA_RIGHT,
        ),
    }


def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"),
                      spaceAfter=4, spaceBefore=4)


def _stat_row(items: list[tuple], styles) -> Table:
    """Build a stat-card table with three dedicated rows: context / value / label.

    Each (value, label, unit) tuple maps to:
      row 0 — unit   (small gray, e.g. "completed", "burned")  → aligned to bottom
      row 1 — value  (big bold number)                          → vertically centred
      row 2 — label  (small gray description)                   → aligned to top
    """
    col_w = (A4[0] - 4 * cm) / len(items)
    col_widths = [col_w] * len(items)

    row_unit  = [Paragraph(u or "", styles["stat_unit"])  for _, _, u in items]
    row_value = [Paragraph(v or "", styles["stat_value"]) for v, _, _ in items]
    row_label = [Paragraph(l or "", styles["stat_label"]) for _, l, _ in items]

    t = Table([row_unit, row_value, row_label], colWidths=col_widths)
    t.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, 0),  "BOTTOM"),
        ("VALIGN",        (0, 1), (-1, 1),  "MIDDLE"),
        ("VALIGN",        (0, 2), (-1, 2),  "TOP"),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        # vertical dividers only — no horizontal lines between the three internal rows
        ("LINEAFTER",     (0, 0), (-2, -1), 0.3, colors.HexColor("#f1f5f9")),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING",    (0, 0), (-1, 0),  8),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  1),
        ("TOPPADDING",    (0, 1), (-1, 1),  2),
        ("BOTTOMPADDING", (0, 1), (-1, 1),  2),
        ("TOPPADDING",    (0, 2), (-1, 2),  1),
        ("BOTTOMPADDING", (0, 2), (-1, 2),  8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def _period_label(period_type: str, period_start: date, period_end: date) -> str:
    fmt = "%b %d, %Y"
    label = period_type.capitalize()
    return f"{label} Report: {period_start.strftime(fmt)} – {period_end.strftime(fmt)}"


def _cover_block(data: dict, styles: dict) -> list:
    """Full-width indigo header block."""
    user = data["user"]
    name = (user.get_full_name() or user.username).title()
    period_label = _period_label(
        data["period_type"] if "period_type" in data else "",
        data["period_start"],
        data["period_end"],
    )
    generated = date.today().strftime("%B %d, %Y")

    # Simulate a coloured background with a Table
    header_data = [
        [Paragraph("FitTrack", styles["cover_title"])],
        [Paragraph("Fitness Report", styles["cover_title"])],
        [Spacer(1, 6)],
        [Paragraph(period_label, styles["cover_sub"])],
        [Paragraph(f"Prepared for <b>{name}</b>", styles["cover_sub"])],
        [Paragraph(f"Generated {generated}", styles["cover_sub"])],
    ]
    t = Table(header_data, colWidths=[A4[0] - 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BRAND),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [8]),
    ]))
    return [t, Spacer(1, 0.5 * cm)]


def _workout_section(data: dict, styles: dict) -> list:
    w = data["workout"]
    s = data["streak"]
    story = [
        Paragraph("Workout Summary", styles["section_heading"]),
        _hr(),
    ]

    hours = int(w["total_minutes"] // 60)
    mins  = int(w["total_minutes"] % 60)
    time_str = f"{hours}h {mins}m" if hours else f"{mins}m"

    story.append(_stat_row([
        (str(w["count"]),               "Workouts",       "completed"),
        (time_str,                       "Training Time",  "total"),
        (f"{w['total_calories']:,}",     "Calories",       "burned"),
        (f"{w['total_volume_kg']:,.0f}", "Volume Lifted",  "kg"),
    ], styles))
    story.append(Spacer(1, 0.3 * cm))

    story.append(_stat_row([
        (f"{w['avg_duration_min']}",     "Avg Duration",   "min / session"),
        (str(s["current"]),              "Current Streak", "days"),
        (str(s["longest"]),              "Best Streak",    "days"),
        (
            f"{w['count']}/{w['goal_for_period']}",
            "Workout Goal",
            "met" if w["goal_met"] else "missed",
        ),
    ], styles))

    if w["top_muscles"]:
        story.append(Spacer(1, 0.3 * cm))
        muscles = ", ".join(f"{cat} ({cnt})" for cat, cnt in w["top_muscles"])
        story.append(Paragraph(f"<b>Top muscle groups:</b> {muscles}", styles["body"]))

    if w["total_distance_km"]:
        story.append(Paragraph(
            f"<b>Total distance:</b> {w['total_distance_km']:.1f} km",
            styles["body"],
        ))
    if w.get("avg_rpe"):
        story.append(Paragraph(
            f"<b>Average perceived exertion (RPE):</b> {w['avg_rpe']} / 10",
            styles["body"],
        ))
    return story


def _nutrition_section(data: dict, styles: dict) -> list:
    n = data["nutrition"]
    story = [
        Spacer(1, 0.4 * cm),
        Paragraph("Nutrition Overview", styles["section_heading"]),
        _hr(),
    ]

    goal_str = f"{n['calorie_goal']:,}" if n["calorie_goal"] else "—"
    story.append(_stat_row([
        (f"{n['avg_calories']:,.0f}",  "Avg Daily Calories", f"goal: {goal_str}"),
        (f"{n['avg_protein_g']:.0f}g", "Avg Protein",        "per day"),
        (f"{n['avg_carbs_g']:.0f}g",   "Avg Carbs",          "per day"),
        (f"{n['avg_fat_g']:.0f}g",     "Avg Fat",            "per day"),
    ], styles))
    story.append(Spacer(1, 0.3 * cm))

    story.append(_stat_row([
        (f"{n['avg_water_l']:.1f}L",      "Avg Daily Water",    "intake"),
        (f"{n['logged_days']}/{n['period_days']}", "Days Logged", "of period"),
        (str(n["days_on_target"]),         "Days on Target",     "±10% of goal"),
        (
            f"{round(n['days_on_target'] / max(n['logged_days'], 1) * 100)}%",
            "Goal Adherence",
            "",
        ),
    ], styles))
    return story


def _body_section(data: dict, styles: dict) -> list:
    b = data["body"]
    story = [
        Spacer(1, 0.4 * cm),
        Paragraph("Body Composition", styles["section_heading"]),
        _hr(),
    ]

    if b["weight_start"] is None:
        story.append(Paragraph(
            "No measurements recorded during this period.", styles["body"]
        ))
        return story

    unit = b["weight_unit"]
    change = b["weight_change"]
    if change is not None:
        sign = "+" if change > 0 else ""
        change_str = f"{sign}{change} {unit}"
    else:
        change_str = "—"

    items = [
        (f"{b['weight_start']} {unit}", "Starting Weight", ""),
        (f"{b['weight_end']} {unit}",   "Ending Weight",   ""),
        (change_str,                     "Weight Change",   ""),
    ]
    if b["bmi_end"] is not None:
        bmi_change = ""
        if b["bmi_start"] is not None and b["bmi_end"] is not None:
            delta = round(b["bmi_end"] - b["bmi_start"], 1)
            bmi_change = f"({'+'if delta>=0 else ''}{delta})"
        items.append((str(b["bmi_end"]), "BMI", bmi_change))

    story.append(_stat_row(items, styles))
    return story


def _goals_section(data: dict, styles: dict) -> list:
    g = data["goals"]
    story = [
        Spacer(1, 0.4 * cm),
        Paragraph("Goals Progress", styles["section_heading"]),
        _hr(),
    ]

    story.append(_stat_row([
        (str(g["active_count"]),          "Active Goals",   ""),
        (f"{g['avg_progress_percent']}%", "Avg Progress",   "across active goals"),
        (str(g["achieved_in_period"]),    "Achieved",       "this period"),
    ], styles))

    if g["active_goals"]:
        story.append(Spacer(1, 0.3 * cm))
        s = styles
        header = [
            Paragraph("Goal", s["table_header"]),
            Paragraph("Type", s["table_header"]),
            Paragraph("Current", s["table_header"]),
            Paragraph("Target", s["table_header"]),
            Paragraph("Progress", s["table_header"]),
        ]
        rows = [header]
        for goal in g["active_goals"]:
            rows.append([
                Paragraph(goal["title"][:28], s["table_cell"]),
                Paragraph(goal["goal_type"].replace("_", " ").title(), s["table_cell"]),
                Paragraph(f"{goal['current_value']:.1f} {goal['unit']}", s["table_cell_right"]),
                Paragraph(f"{goal['target_value']:.1f} {goal['unit']}", s["table_cell_right"]),
                Paragraph(f"{goal['progress_percent']}%", s["table_cell_right"]),
            ])
        col_widths = [5.5 * cm, 3.5 * cm, 3 * cm, 3 * cm, 2.5 * cm]
        t = Table(rows, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), BRAND),
            ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("ALIGN",         (2, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(t)

    if g["achieved_titles"]:
        story.append(Spacer(1, 0.3 * cm))
        joined = ", ".join(g["achieved_titles"])
        story.append(Paragraph(f"<b>Goals achieved this period:</b> {joined}", styles["body"]))
    return story


def _achievements_section(data: dict, styles: dict) -> list:
    a = data["achievements"]
    story = [
        Spacer(1, 0.4 * cm),
        Paragraph("Achievements", styles["section_heading"]),
        _hr(),
    ]
    story.append(_stat_row([
        (str(a["new_count"]),   "New Badges",        "this period"),
        (str(a["total_count"]), "Total Achievements", "all time"),
    ], styles))

    if a["new_badges"]:
        story.append(Spacer(1, 0.3 * cm))
        for badge in a["new_badges"]:
            story.append(Paragraph(f"★  {badge}", styles["badge"]))
    return story


def _footer(styles: dict) -> list:
    return [
        Spacer(1, 0.6 * cm),
        _hr(),
        Paragraph(
            "© FitTrack — helping you reach your fitness goals. "
            "This report was generated automatically based on your logged activity.",
            styles["footer"],
        ),
    ]


def generate_pdf(data: dict, period_type: str) -> bytes:
    """Return PDF bytes for the given data dict (from collect_report_data)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
    )

    data = {**data, "period_type": period_type}
    s = _styles()

    story = []
    story += _cover_block(data, s)
    story += _workout_section(data, s)
    story += _nutrition_section(data, s)
    story += _body_section(data, s)
    story += _goals_section(data, s)
    story += _achievements_section(data, s)
    story += _footer(s)

    doc.build(story)
    return buf.getvalue()
