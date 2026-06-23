from django.core.management.base import BaseCommand
from django.utils.text import slugify

from exercises.models import Category, Equipment, Exercise, MuscleGroup

S = Category.STRENGTH
C = Category.CARDIO
F = Category.FLEXIBILITY
B = Category.BALANCE

BB = Equipment.BARBELL
DB = Equipment.DUMBBELL
BW = Equipment.BODYWEIGHT
CB = Equipment.CABLE
MA = Equipment.MACHINE
KB = Equipment.KETTLEBELL
BA = Equipment.BAND
CV = Equipment.CARDIO
OT = Equipment.OTHER

CHEST   = MuscleGroup.CHEST
BACK    = MuscleGroup.BACK
SHLD    = MuscleGroup.SHOULDERS
BICE    = MuscleGroup.BICEPS
TRIC    = MuscleGroup.TRICEPS
FORE    = MuscleGroup.FOREARMS
QUAD    = MuscleGroup.QUADS
HAMS    = MuscleGroup.HAMSTRINGS
GLUT    = MuscleGroup.GLUTES
CALV    = MuscleGroup.CALVES
CORE    = MuscleGroup.CORE
FULL    = MuscleGroup.FULL_BODY
CARD    = MuscleGroup.CARDIO

EXERCISES = [

    # ══════════════════════════════════════════════════════════════════════════
    # CHEST
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Bench Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps", "shoulders"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Lie flat, grip just wider than shoulder-width. Lower bar to mid-chest under control, press to lockout. Keep feet flat, arch natural, wrists straight."},

    {"name": "Incline Barbell Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders", "triceps"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Set bench to 30–45°. Unrack bar, lower to upper chest, press to lockout. Incline shifts emphasis to the upper pec and front deltoid."},

    {"name": "Decline Bench Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Set bench to −15–30°. Lower bar to lower chest, press to lockout. Targets the lower portion of the pec major."},

    {"name": "Incline Dumbbell Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders", "triceps"],
     "equipment": DB, "is_compound": True, "met_value": "5.0",
     "instructions": "Bench at 30–45°. Press dumbbells up and slightly inward, squeeze at the top. Greater range of motion vs barbell."},

    {"name": "Dumbbell Bench Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps", "shoulders"],
     "equipment": DB, "is_compound": True, "met_value": "5.0",
     "instructions": "Lie flat, dumbbells at chest level. Press to lockout, slight inward arc at the top. Allows independent arm movement to fix imbalances."},

    {"name": "Push-up",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps", "core"],
     "equipment": BW, "is_compound": True, "met_value": "3.8",
     "instructions": "Hands shoulder-width apart, body rigid. Lower chest to an inch from the floor, push back up. Scale with knee push-ups or feet elevated."},

    {"name": "Cable Fly",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders"],
     "equipment": CB, "met_value": "4.0",
     "instructions": "Set pulleys to chest height. Bring handles together in a hugging arc, squeeze the pec, slow return. Keeps constant tension through the range."},

    {"name": "Low Cable Fly",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders"],
     "equipment": CB, "met_value": "4.0",
     "instructions": "Pulleys at floor level. Drive handles upward and inward toward eye level. Emphasises upper chest."},

    {"name": "Dumbbell Fly",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders"],
     "equipment": DB, "met_value": "4.0",
     "instructions": "Lie flat, slight bend in elbows. Lower to a stretch, bring dumbbells back together over the chest. Do not go so low it stresses the shoulder."},

    {"name": "Chest Dip",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps", "shoulders"],
     "equipment": BW, "is_compound": True, "met_value": "4.5",
     "instructions": "Lean torso forward 20–30° on parallel bars. Lower until elbows reach 90°, press back up. Lean dictates how much chest vs tricep is involved."},

    {"name": "Machine Chest Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps"],
     "equipment": MA, "is_compound": True, "met_value": "4.5",
     "instructions": "Adjust seat so handles are at mid-chest. Press to near-lockout, controlled return. Good for beginners or drop sets at end of a session."},

    # ══════════════════════════════════════════════════════════════════════════
    # BACK
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Deadlift",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["glutes", "hamstrings", "core"],
     "equipment": BB, "is_compound": True, "met_value": "6.0",
     "instructions": "Bar over mid-foot. Hip-hinge to grip, neutral spine, big breath. Drive through the floor, push hips forward to lockout. Hinge back down."},

    {"name": "Sumo Deadlift",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["glutes", "hamstrings", "quads"],
     "equipment": BB, "is_compound": True, "met_value": "6.0",
     "instructions": "Wide stance, toes pointed out ~45°, grip inside the legs. Keep chest up, drive knees out as you pull. More glute/quad, less lower back than conventional."},

    {"name": "Trap Bar Deadlift",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["quads", "glutes", "hamstrings"],
     "equipment": BB, "is_compound": True, "met_value": "6.0",
     "instructions": "Stand inside the hex bar, neutral spine, grip handles. Drive through the floor. More quad-dominant and joint-friendly than straight bar."},

    {"name": "Pull-up",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps"],
     "equipment": BW, "is_compound": True, "met_value": "4.5",
     "instructions": "Overhand grip, slightly wider than shoulders. Pull chin above bar, control descent. Dead hang at bottom for full range. Use band for assistance or add weight for progression."},

    {"name": "Chin-up",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps"],
     "equipment": BW, "is_compound": True, "met_value": "4.5",
     "instructions": "Underhand grip, shoulder-width. Pull chin above bar, leads with elbows. More bicep involvement than pull-up."},

    {"name": "Bent-Over Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps", "core"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Hinge 45° with neutral spine, bar below the knee. Row to lower chest/upper abs, lead with elbows, squeeze shoulder blades together. Control the descent."},

    {"name": "Pendlay Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps", "core"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Bar starts on floor. Hinge parallel to floor, explosively row to lower chest, return to floor. Strict form teaches power off the floor."},

    {"name": "Dumbbell Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Brace on bench with one hand and knee. Row dumbbell to hip, elbow close to body. Full stretch at bottom, full squeeze at top."},

    {"name": "Lat Pulldown",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps"],
     "equipment": CB, "is_compound": True, "met_value": "4.5",
     "instructions": "Wide overhand grip. Lean back slightly, pull bar to upper chest, lead elbows down and back. Slow eccentric to feel the lat."},

    {"name": "Seated Cable Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps"],
     "equipment": CB, "met_value": "4.5",
     "instructions": "Sit tall, feet braced. Pull handle to lower ribs with elbows tight, squeeze shoulder blades. Avoid rocking the torso."},

    {"name": "Chest-Supported Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps", "rear delts"],
     "equipment": DB, "met_value": "4.5",
     "instructions": "Lie prone on incline bench. Row dumbbells to hip level, elbows out ~45°. Chest support eliminates lower back involvement."},

    {"name": "Face Pull",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["back"],
     "equipment": CB, "met_value": "3.5",
     "instructions": "Set pulley at face height, rope attachment. Pull to face with elbows high, externally rotate at the top. Great shoulder health exercise."},

    {"name": "Good Morning",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["hamstrings", "glutes"],
     "equipment": BB, "is_compound": True, "met_value": "4.5",
     "instructions": "Bar on upper back. Hinge at the hips with soft knees, lower until torso is near parallel. Drive hips forward to return. Keep spine neutral throughout."},

    {"name": "Back Extension",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["glutes", "hamstrings"],
     "equipment": BW, "met_value": "3.5",
     "instructions": "Lie face-down on hyperextension bench. Hinge at the hip to lower torso, drive hips forward to raise. Can hold plate for added load."},

    # ══════════════════════════════════════════════════════════════════════════
    # SHOULDERS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Overhead Press",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["triceps", "core"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Bar at shoulder height, grip just outside shoulders. Brace core, press overhead to full lockout, bar finishes over the back of the head. Lower under control."},

    {"name": "Seated Dumbbell Press",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["triceps"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Sit upright, dumbbells at ear height. Press overhead, slight inward arc. Seated removes leg drive, isolates the shoulder girdle."},

    {"name": "Arnold Press",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["triceps"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Start with palms facing you, dumbbells at chin. Rotate palms outward as you press overhead. Works all three deltoid heads through rotation."},

    {"name": "Lateral Raise",
     "category": S, "primary_muscle": SHLD,
     "equipment": DB, "met_value": "3.5",
     "instructions": "Slight forward lean. Raise dumbbells to side until arms are parallel to floor, lead with elbows, thumbs slightly down. Control the descent; avoid shrugging."},

    {"name": "Cable Lateral Raise",
     "category": S, "primary_muscle": SHLD,
     "equipment": CB, "met_value": "3.5",
     "instructions": "Single cable at hip height. Raise across body or to the side. Cable provides constant tension unlike dumbbells at the bottom of the range."},

    {"name": "Rear Delt Fly",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["back"],
     "equipment": DB, "met_value": "3.5",
     "instructions": "Hinge forward 45–90°. Raise dumbbells out to the side, lead with elbows, squeeze rear delts. Avoid using momentum."},

    {"name": "Upright Row",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["biceps", "traps"],
     "equipment": BB, "is_compound": True, "met_value": "4.0",
     "instructions": "Overhand grip shoulder-width. Pull bar straight up to chin, elbows lead and flare. Control descent. Keep elbows above wrists throughout."},

    {"name": "Shrug",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["neck"],
     "equipment": BB, "met_value": "3.5",
     "instructions": "Hold bar at hip width. Elevate shoulders straight up as high as possible, pause, lower fully. Do not roll the shoulders."},

    # ══════════════════════════════════════════════════════════════════════════
    # ARMS — BICEPS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Barbell Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": BB, "met_value": "3.5",
     "instructions": "Underhand grip shoulder-width. Curl bar to upper chest keeping elbows pinned to ribs. Lower under control — the eccentric builds the most size."},

    {"name": "Dumbbell Curl",
     "category": S, "primary_muscle": BICE, "secondary_muscles": ["forearms"],
     "equipment": DB, "met_value": "3.5",
     "instructions": "Supinate wrist at the bottom of each rep. Curl one or both arms at a time. Allows natural wrist rotation for full range."},

    {"name": "Hammer Curl",
     "category": S, "primary_muscle": BICE, "secondary_muscles": ["forearms"],
     "equipment": DB, "met_value": "3.5",
     "instructions": "Neutral grip (thumbs up). Curl both dumbbells simultaneously. Targets the brachialis and brachioradialis as well as the bicep."},

    {"name": "Incline Dumbbell Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": DB, "met_value": "3.5",
     "instructions": "Lie back on 45° bench, arms hanging. Curl dumbbells up, elbows stay back. Stretched starting position hits the long head of the bicep hard."},

    {"name": "Preacher Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": BB, "met_value": "3.5",
     "instructions": "Brace upper arms on preacher pad. Curl bar to full contraction, lower under control to near-full extension. Isolates the bicep by removing cheat."},

    {"name": "Cable Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": CB, "met_value": "3.5",
     "instructions": "Low pulley, straight bar or EZ bar. Curl to full contraction, constant tension throughout range. Can use single handle for unilateral work."},

    # ══════════════════════════════════════════════════════════════════════════
    # ARMS — TRICEPS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Tricep Pushdown",
     "category": S, "primary_muscle": TRIC,
     "equipment": CB, "met_value": "3.5",
     "instructions": "High pulley, rope or bar. Elbows at sides. Extend arms fully, squeeze triceps at the bottom. Resist the cable on the way up."},

    {"name": "Skull Crusher",
     "category": S, "primary_muscle": TRIC,
     "equipment": BB, "met_value": "3.5",
     "instructions": "Lie on bench, EZ bar over chest. Lower bar to forehead by bending only at the elbows. Extend back to start. Keep upper arms vertical."},

    {"name": "Overhead Tricep Extension",
     "category": S, "primary_muscle": TRIC,
     "equipment": DB, "met_value": "3.5",
     "instructions": "Hold one dumbbell with both hands overhead. Bend elbows to lower behind head, extend back up. Fully stretches the long head of the tricep."},

    {"name": "Close-Grip Bench Press",
     "category": S, "primary_muscle": TRIC, "secondary_muscles": ["chest", "shoulders"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Grip inside shoulder-width. Press as normal but keep elbows closer to the body. Shifts emphasis from chest to triceps. Use controlled tempo."},

    {"name": "Tricep Dip",
     "category": S, "primary_muscle": TRIC, "secondary_muscles": ["chest", "shoulders"],
     "equipment": BW, "is_compound": True, "met_value": "4.0",
     "instructions": "Upright torso on parallel bars (vs forward lean for chest dips). Lower until elbows reach 90°, press back to lockout. Add weight via belt for progression."},

    {"name": "Diamond Push-up",
     "category": S, "primary_muscle": TRIC, "secondary_muscles": ["chest"],
     "equipment": BW, "is_compound": True, "met_value": "3.8",
     "instructions": "Hands form a diamond shape directly under the sternum. Lower chest toward hands, push back up. Very effective bodyweight tricep builder."},

    # ══════════════════════════════════════════════════════════════════════════
    # ARMS — FOREARMS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Wrist Curl",
     "category": S, "primary_muscle": FORE,
     "equipment": BB, "met_value": "2.5",
     "instructions": "Sit with forearms on thighs, palms up. Curl bar by flexing wrists only. Lower fully for full range."},

    {"name": "Reverse Wrist Curl",
     "category": S, "primary_muscle": FORE,
     "equipment": BB, "met_value": "2.5",
     "instructions": "Same setup, palms down. Extend wrist to raise bar, lower under control. Targets the extensor muscles of the forearm."},

    {"name": "Farmer's Carry",
     "category": S, "primary_muscle": FORE, "secondary_muscles": ["core", "traps"],
     "equipment": DB, "is_compound": True, "met_value": "5.0",
     "instructions": "Hold heavy dumbbells at sides. Walk for time or distance, keeping shoulders packed down and back, spine tall. Exceptional grip builder."},

    # ══════════════════════════════════════════════════════════════════════════
    # LEGS — QUADS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Back Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "hamstrings", "core"],
     "equipment": BB, "is_compound": True, "met_value": "6.0",
     "instructions": "High-bar or low-bar on upper back. Brace, hinge knees and hips simultaneously, descend below parallel, drive through the whole foot back to lockout."},

    {"name": "Front Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["core", "glutes"],
     "equipment": BB, "is_compound": True, "met_value": "6.0",
     "instructions": "Bar rests on front deltoids, elbows high. Squat with very upright torso. Far more quad-dominant than back squat. Requires good wrist/shoulder mobility."},

    {"name": "Goblet Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "core"],
     "equipment": KB, "is_compound": True, "met_value": "5.0",
     "instructions": "Hold kettlebell at chest. Squat between the knees, elbows inside legs at the bottom. Excellent teaching tool for squat pattern; great for warm-ups."},

    {"name": "Hack Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes"],
     "equipment": MA, "is_compound": True, "met_value": "5.0",
     "instructions": "Feet shoulder-width on platform. Lower until hips are below knees, push plate to lockout. Machine removes balance demand, allowing more quad focus."},

    {"name": "Leg Press",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes"],
     "equipment": MA, "met_value": "4.5",
     "instructions": "Feet shoulder-width. Lower sled until hips are below knees or just before lower back rounds. Press to near-lockout. Foot placement adjusts emphasis."},

    {"name": "Bulgarian Split Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "hamstrings"],
     "equipment": DB, "is_compound": True, "met_value": "5.5",
     "instructions": "Rear foot elevated on bench. Lower front leg until knee approaches floor. Keep torso upright. Brutal unilateral quad/glute developer."},

    {"name": "Walking Lunge",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Step forward, lower back knee toward floor, drive off front heel into the next step. Can hold dumbbells or add barbell."},

    {"name": "Step-Up",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Step onto a bench or box with the working leg, fully extend the hip to stand, lower back down. Keep torso upright, do not push off the back foot."},

    {"name": "Leg Extension",
     "category": S, "primary_muscle": QUAD,
     "equipment": MA, "met_value": "3.5",
     "instructions": "Sit in machine, pad on lower shins. Extend knees to lockout, pause, lower under control. Pure quad isolation; great finisher."},

    {"name": "Sissy Squat",
     "category": S, "primary_muscle": QUAD,
     "equipment": BW, "met_value": "4.0",
     "instructions": "Hold for balance, lean back as knees travel forward and down, lower heels off floor. One of the most intense bodyweight quad exercises; build up gradually."},

    # ══════════════════════════════════════════════════════════════════════════
    # LEGS — HAMSTRINGS & GLUTES
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Romanian Deadlift",
     "category": S, "primary_muscle": HAMS, "secondary_muscles": ["glutes", "back"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Hip-hinge with soft knees, bar slides down thighs. Lower until hamstrings are fully stretched (mid-shin), drive hips forward. Do not round the lower back."},

    {"name": "Nordic Hamstring Curl",
     "category": S, "primary_muscle": HAMS,
     "equipment": BW, "met_value": "4.5",
     "instructions": "Kneel with ankles held. Lower torso toward floor as slowly as possible, catching with hands at the bottom. Push back to start. High injury prevention value."},

    {"name": "Leg Curl (Lying)",
     "category": S, "primary_muscle": HAMS,
     "equipment": MA, "met_value": "3.5",
     "instructions": "Lie face down, pad just above heels. Curl heels toward glutes, squeeze, lower slowly. Keep hips pressed into pad throughout."},

    {"name": "Leg Curl (Seated)",
     "category": S, "primary_muscle": HAMS,
     "equipment": MA, "met_value": "3.5",
     "instructions": "Sit upright, pad just above shins. Curl heels down and back. Seated position keeps hip flexors out of the movement."},

    {"name": "Hip Thrust",
     "category": S, "primary_muscle": GLUT, "secondary_muscles": ["hamstrings"],
     "equipment": BB, "is_compound": True, "met_value": "4.5",
     "instructions": "Upper back on bench, bar across hip crease with pad. Drive hips to full extension, squeeze glutes hard, lower under control. Most research-backed glute builder."},

    {"name": "Glute Bridge",
     "category": S, "primary_muscle": GLUT, "secondary_muscles": ["hamstrings", "core"],
     "equipment": BW, "met_value": "3.5",
     "instructions": "Lie on floor, feet flat. Drive hips up to full extension, squeeze, lower. Add dumbbell on lap for load. Gateway to hip thrusts for beginners."},

    {"name": "Cable Kickback",
     "category": S, "primary_muscle": GLUT,
     "equipment": CB, "met_value": "3.5",
     "instructions": "Attach ankle cuff to low pulley. Brace on the frame, kick leg back and up with slight knee bend, squeeze glute at the top. Controlled return."},

    {"name": "Sumo Squat",
     "category": S, "primary_muscle": GLUT, "secondary_muscles": ["quads", "inner thigh"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Very wide stance, toes out 45°. Hold one heavy dumbbell between legs. Squat between the knees, drive through the whole foot. Strong glute/adductor emphasis."},

    # ══════════════════════════════════════════════════════════════════════════
    # LEGS — CALVES
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Calf Raise (Standing)",
     "category": S, "primary_muscle": CALV,
     "equipment": MA, "met_value": "3.0",
     "instructions": "Press through balls of feet to full extension, pause 1 s, lower heel all the way down for full stretch. Do not bounce. Slow reps outperform heavy reps."},

    {"name": "Calf Raise (Seated)",
     "category": S, "primary_muscle": CALV,
     "equipment": MA, "met_value": "3.0",
     "instructions": "Seated position preferentially loads the soleus (deeper calf muscle). Full range, full pause at top and bottom."},

    {"name": "Single-Leg Calf Raise",
     "category": S, "primary_muscle": CALV,
     "equipment": BW, "met_value": "3.0",
     "instructions": "Stand on one foot on a step edge. Lower heel below the step level for full stretch, rise to full extension. Double the stimulus with no extra load."},

    # ══════════════════════════════════════════════════════════════════════════
    # CORE
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Plank",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.5",
     "instructions": "Forearms and toes on floor. Keep hips level, glutes and abs braced, neck neutral. Avoid letting the hips sag or pike up."},

    {"name": "Side Plank",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.5",
     "instructions": "On one forearm and the side of one foot. Raise hips to form a straight line. Hold or add hip dips for difficulty."},

    {"name": "Hanging Leg Raise",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "4.0",
     "instructions": "Dead hang from bar. Raise straight legs (or bent knees as a regression) to horizontal or above. Control the descent; do not swing."},

    {"name": "Cable Crunch",
     "category": S, "primary_muscle": CORE,
     "equipment": CB, "met_value": "3.5",
     "instructions": "Kneel facing cable, rope behind the head. Crunch the lower ribs toward the hips, not the head toward the knees. Weight-loadable ab exercise."},

    {"name": "Ab Wheel Rollout",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["back", "shoulders"],
     "equipment": OT, "met_value": "4.0",
     "instructions": "Kneel and roll wheel forward until hips are fully extended, keep core braced throughout. Pull back with abs. Start with half rollouts; builds to standing over time."},

    {"name": "Russian Twist",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.5",
     "instructions": "Sit with knees bent, lean back 45°, rotate torso side to side. Add weight plate or medicine ball for load. Targets the obliques."},

    {"name": "Bicycle Crunch",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.8",
     "instructions": "Lie on back, hands behind head. Alternate bringing opposite elbow to opposite knee while cycling the legs. Slow and deliberate beats fast and sloppy."},

    {"name": "Dead Bug",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.0",
     "instructions": "Lie on back, arms extended up, knees over hips 90°. Lower opposite arm and leg toward floor simultaneously, lower back stays pinned. Excellent for stability."},

    {"name": "Pallof Press",
     "category": S, "primary_muscle": CORE,
     "equipment": CB, "met_value": "3.5",
     "instructions": "Stand perpendicular to cable, handle at chest. Press out and hold, resisting rotation. Trains anti-rotation which transfers directly to most compound lifts."},

    {"name": "V-Up",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "4.0",
     "instructions": "Lie flat, raise straight legs and upper body simultaneously to form a V. Lower with control. Harder than sit-ups; great for hip flexor + ab integration."},

    # ══════════════════════════════════════════════════════════════════════════
    # KETTLEBELL
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Kettlebell Swing",
     "category": S, "primary_muscle": GLUT, "secondary_muscles": ["hamstrings", "core", "back"],
     "equipment": KB, "is_compound": True, "met_value": "8.0",
     "instructions": "Hinge, hike KB back, drive hips forward explosively. Let the bell float to chest height. This is a hip-hinge power exercise, not a squat. Keep spine neutral."},

    {"name": "Kettlebell Turkish Get-Up",
     "category": S, "primary_muscle": FULL, "secondary_muscles": ["core", "shoulders"],
     "equipment": KB, "is_compound": True, "met_value": "5.0",
     "instructions": "From lying with arm extended, move through six positions to standing — all while keeping the KB overhead. Full-body coordination, stability and strength."},

    {"name": "Kettlebell Clean",
     "category": S, "primary_muscle": FULL, "secondary_muscles": ["back", "core"],
     "equipment": KB, "is_compound": True, "met_value": "6.0",
     "instructions": "Hike KB, drive hips, keep bell close and guide to rack position at shoulder. Punch hand through, do not let it crash on the forearm."},

    {"name": "Kettlebell Goblet Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "core"],
     "equipment": KB, "is_compound": True, "met_value": "5.0",
     "instructions": "Hold bell by horns at chest. Squat between knees, elbows inside legs at bottom. Upright torso, full depth. Ideal teaching tool."},

    # ══════════════════════════════════════════════════════════════════════════
    # CARDIO
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Running",
     "category": C, "primary_muscle": CARD,
     "equipment": CV, "met_value": "9.8",
     "instructions": "Steady-state or interval running. Land mid-foot under your centre of mass. Arm swing drives pace. Easy runs should allow a full sentence without breathlessness."},

    {"name": "Treadmill Run",
     "category": C, "primary_muscle": CARD,
     "equipment": CV, "met_value": "9.0",
     "instructions": "Set your target pace, slight incline (1–2%) compensates for lack of wind resistance. Same cues as outdoor running. Use for controlled interval training."},

    {"name": "Cycling (Outdoor)",
     "category": C, "primary_muscle": CARD,
     "equipment": CV, "met_value": "8.0",
     "instructions": "Pedal at 80–100 rpm cadence. Moderate resistance. Engage core to protect the lower back. Excellent low-impact cardio."},

    {"name": "Stationary Bike",
     "category": C, "primary_muscle": CARD,
     "equipment": CV, "met_value": "7.0",
     "instructions": "Adjust seat so knee is slightly bent at the bottom. Keep 80–100 rpm. Great for LISS cardio or high-intensity intervals."},

    {"name": "Rowing (Ergometer)",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["back", "core", "legs"],
     "equipment": CV, "met_value": "8.5",
     "instructions": "Sequence: legs, lean, pull. Drive legs, lean back to 11 o'clock, row handle to lower chest. Full leg extension before the lean. Reverse to recover. Full-body."},

    {"name": "Stairmaster",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["glutes", "quads"],
     "equipment": CV, "met_value": "9.0",
     "instructions": "Set a sustainable step rate. Keep body upright — do not lean on the rails. Excellent glute and cardiovascular stimulus."},

    {"name": "Elliptical",
     "category": C, "primary_muscle": CARD,
     "equipment": CV, "met_value": "7.0",
     "instructions": "Push and pull the handles for full-body engagement. Minimal joint impact — good for recovery days or those with knee issues."},

    {"name": "Jump Rope",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["calves", "shoulders"],
     "equipment": OT, "met_value": "12.3",
     "instructions": "Light bounce on balls of feet, rotate rope with wrists. Start with basic two-foot jump. Advance to single-leg, double-unders, criss-cross."},

    {"name": "Burpees",
     "category": C, "primary_muscle": FULL,
     "equipment": BW, "met_value": "8.0",
     "instructions": "Squat, kick back to push-up position, push-up (optional), jump feet to hands, jump and clap overhead. Modify by removing the jump or push-up as needed."},

    {"name": "Box Jump",
     "category": C, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "calves"],
     "equipment": BW, "is_compound": True, "met_value": "8.0",
     "instructions": "Athletic stance, arm swing. Jump onto box, land softly with knees tracking toes, hips below parallel. Step down — do not jump down. Plyometric power builder."},

    {"name": "Mountain Climbers",
     "category": C, "primary_muscle": CORE, "secondary_muscles": ["shoulders", "full_body"],
     "equipment": BW, "met_value": "8.0",
     "instructions": "Plank position, alternate driving knees to chest as fast as possible. Keep hips level. Can be done slow (core focus) or fast (cardio focus)."},

    {"name": "Battle Ropes",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["shoulders", "core"],
     "equipment": OT, "met_value": "10.0",
     "instructions": "Anchor ropes, stand in athletic stance. Alternate waves, slams, circles. 20–30 s bursts with short rest. Devastating conditioning tool."},

    {"name": "Assault Bike",
     "category": C, "primary_muscle": FULL,
     "equipment": CV, "met_value": "12.0",
     "instructions": "Push/pull handles while pedalling. Even 20 s at max effort is brutal. Excellent for conditioning blocks and metabolic finishers."},

    {"name": "Sled Push",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["quads", "glutes"],
     "equipment": OT, "is_compound": True, "met_value": "9.0",
     "instructions": "Hands on handles, lean forward 45°. Drive through the whole foot in short fast steps. Load depends on goal (heavy and slow vs light and fast)."},

    # ══════════════════════════════════════════════════════════════════════════
    # FLEXIBILITY / MOBILITY
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Yoga Flow",
     "category": F, "primary_muscle": FULL,
     "equipment": BW, "met_value": "3.0",
     "instructions": "Linked postures synchronised with breath. Sun salutation, warrior poses, pigeon, downward dog. Improves mobility, balance and parasympathetic recovery."},

    {"name": "Foam Rolling",
     "category": F, "primary_muscle": FULL,
     "equipment": OT, "met_value": "2.5",
     "instructions": "Roll slowly over major muscle groups (quads, hamstrings, IT band, upper back). Pause on tender spots for 30–60 s. Aids myofascial release and recovery."},

    {"name": "Hip Flexor Stretch",
     "category": F, "primary_muscle": FULL,
     "equipment": BW, "met_value": "2.0",
     "instructions": "Kneeling lunge position. Drive front hip forward, tuck tailbone under. Hold 30–60 s each side. Critical for anyone sitting for long periods."},

    {"name": "Hamstring Stretch",
     "category": F, "primary_muscle": HAMS,
     "equipment": BW, "met_value": "2.0",
     "instructions": "Lie on back, loop band or towel over one foot. Straighten leg and gently pull. Or seated forward fold. Hold 30–60 s. Avoid aggressive bouncing."},

    {"name": "Thoracic Mobility Drill",
     "category": F, "primary_muscle": BACK,
     "equipment": OT, "met_value": "2.5",
     "instructions": "Foam roller placed horizontally across mid/upper back. Arch over it at each vertebral level. Restores extension mobility lost through desk posture."},

    {"name": "Cat-Cow",
     "category": F, "primary_muscle": CORE, "secondary_muscles": ["back"],
     "equipment": BW, "met_value": "2.0",
     "instructions": "On hands and knees. Alternate arching the back (cow) and rounding it (cat) in sync with breath. Excellent warm-up and lower back relief."},

    {"name": "World's Greatest Stretch",
     "category": F, "primary_muscle": FULL,
     "equipment": BW, "met_value": "3.0",
     "instructions": "Lunge forward, place same-side hand inside foot, rotate opposite arm to sky. Then straighten the front leg for hamstring stretch. 3 movements in one. Best warm-up drill."},

    {"name": "Pigeon Pose",
     "category": F, "primary_muscle": GLUT, "secondary_muscles": ["hip flexors"],
     "equipment": BW, "met_value": "2.0",
     "instructions": "Front shin across the mat, rear leg extended. Fold forward to deepen. Held 60–120 s per side. Deep hip opener essential for squats and runners."},

    # ══════════════════════════════════════════════════════════════════════════
    # BALANCE
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Single-Leg Deadlift",
     "category": B, "primary_muscle": HAMS, "secondary_muscles": ["glutes", "core"],
     "equipment": DB, "is_compound": True, "met_value": "4.0",
     "instructions": "Balance on one leg. Hinge forward, letting free leg extend behind, until upper body and free leg form a T. Return to standing. Builds hip stability and hamstring strength."},

    {"name": "Bosu Ball Squat",
     "category": B, "primary_muscle": QUAD, "secondary_muscles": ["core", "ankles"],
     "equipment": OT, "is_compound": True, "met_value": "4.0",
     "instructions": "Stand on dome side of Bosu. Perform controlled squat. Instability demands more core and ankle proprioception than standard squat."},

    # ══════════════════════════════════════════════════════════════════════════
    # EXERCISES FROM THE YEAR PLAN (home barbell + dumbbell programme)
    # ══════════════════════════════════════════════════════════════════════════

    # ── Chest ─────────────────────────────────────────────────────────────────
    {"name": "Dumbbell Floor Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps", "shoulders"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Lie on the floor, dumbbells at chest level. Press to lockout. The floor acts as a natural depth stop — elbows touch down lightly, protecting the shoulder. "
                     "Excellent substitute when no bench is available. Keep feet flat or legs straight."},

    {"name": "Dumbbell Squeeze Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Lie on floor or bench, dumbbells pressed together throughout the entire set. Squeeze palms toward each other as hard as possible while pressing. "
                     "Constant inward force maximises inner-chest activation. Do not let the bells separate at any point."},

    {"name": "Decline Push-up",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps", "shoulders"],
     "equipment": BW, "is_compound": True, "met_value": "4.0",
     "instructions": "Place feet on a chair or box, hands on the floor shoulder-width apart. Lower chest toward the floor, push back up. "
                     "Feet-elevated angle shifts emphasis to upper chest and increases difficulty vs standard push-up."},

    # ── Back ──────────────────────────────────────────────────────────────────
    {"name": "Dumbbell Pullover",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["chest", "core"],
     "equipment": DB, "met_value": "4.0",
     "instructions": "Lie on floor or bench perpendicular (upper back only on surface). Hold one dumbbell with both hands above the chest. "
                     "Lower it back over your head in a wide arc until you feel a full lat stretch, then pull back to start. "
                     "Floor version: lie flat, lower until upper arms touch the ground. Slow eccentric (3–4 s) maximises stretch."},

    {"name": "Gorilla Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps", "core"],
     "equipment": DB, "is_compound": True, "met_value": "5.0",
     "instructions": "Place two dumbbells on the floor hip-width apart. Hinge over them, knees soft, and grip both handles. "
                     "Row one dumbbell to your hip while the other stays planted for balance, then switch. "
                     "The floor anchor allows heavier loads than standard rows. Keep hips square throughout."},

    # ── Shoulders ─────────────────────────────────────────────────────────────
    {"name": "Dumbbell Z-press",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["triceps", "core"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Sit on the floor with legs straight in front of you (no back support). Hold dumbbells at shoulder height and press overhead. "
                     "The seated position with no back rest removes any leg drive or lower-back lean — every watt comes from the shoulder girdle. "
                     "Requires and builds significant shoulder mobility and core stability."},

    {"name": "Half-kneeling Single-arm DB Press",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["core", "triceps"],
     "equipment": DB, "is_compound": True, "met_value": "4.0",
     "instructions": "Kneel on one knee (same side as the pressing arm). Hold dumbbell at shoulder. Press overhead while resisting the rotational pull through the core. "
                     "The split stance creates an anti-rotation challenge — the core has to fight to keep the torso square as the arm presses. "
                     "Switch sides between sets."},

    # ── Arms — Biceps ─────────────────────────────────────────────────────────
    {"name": "Concentration Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": DB, "met_value": "3.5",
     "instructions": "Sit on a bench or the floor, lean forward, brace the back of your upper arm against the inside of your thigh. "
                     "Curl the dumbbell slowly to full contraction, squeeze, lower fully. "
                     "The braced arm position eliminates all cheat — pure bicep isolation. Do not allow the elbow to drift."},

    # ── Arms — Triceps ────────────────────────────────────────────────────────
    {"name": "Triceps Kickback",
     "category": S, "primary_muscle": TRIC,
     "equipment": DB, "met_value": "3.0",
     "instructions": "Hinge forward 45°, upper arm pinned to the side parallel to the floor. Extend the forearm back to full lockout, squeeze the tricep at the top, "
                     "then lower slowly. The key: upper arm stays stationary — only the forearm moves. "
                     "Use lighter weight and focus on the squeeze; momentum kills this exercise."},

    {"name": "Lying DB Triceps Extension",
     "category": S, "primary_muscle": TRIC,
     "equipment": DB, "met_value": "3.5",
     "instructions": "Lie on the floor (or bench), dumbbells held above the chest with neutral grip. Bend only at the elbows, lowering dumbbells toward your temples or ears. "
                     "The floor stops elbow travel past 90°, reducing shoulder stress. Extend back to start without flaring elbows. "
                     "Also called 'floor skull crushers' with dumbbells."},

    {"name": "Close-grip Barbell Floor Press",
     "category": S, "primary_muscle": TRIC, "secondary_muscles": ["chest"],
     "equipment": BB, "is_compound": True, "met_value": "4.5",
     "instructions": "Lie on the floor, grip shoulder-width or slightly inside. Lower the bar until elbows touch the floor (natural depth stop), press back to lockout. "
                     "Close grip and the limited ROM combine to target the triceps hard without stressing the shoulder. "
                     "No rack needed — clean the bar from the floor or have a partner hand it off."},

    # ── Legs ──────────────────────────────────────────────────────────────────
    {"name": "Reverse Lunge",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "hamstrings"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Stand upright, step one foot backward and lower the back knee toward the floor. Front shin stays vertical. Drive through the front heel to return. "
                     "Easier on the knee than forward lunges because the front knee travels less over the toe. "
                     "Alternate legs or complete all reps on one side. Hold dumbbells at sides for load."},

    {"name": "B-stance Romanian Deadlift",
     "category": S, "primary_muscle": HAMS, "secondary_muscles": ["glutes", "back"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Stand with 70% of your weight on the working leg; the other foot is half a step back, toes lightly touching the floor for balance only. "
                     "Perform a Romanian deadlift as normal — hinge at the hips, bar or dumbbells trace the legs, feel the hamstring stretch, drive hips forward to return. "
                     "The staggered stance adds significant unilateral load without the balance demand of a full single-leg RDL."},

    {"name": "Single-leg Hip Thrust",
     "category": S, "primary_muscle": GLUT, "secondary_muscles": ["hamstrings", "core"],
     "equipment": BW, "met_value": "4.0",
     "instructions": "Set up as a standard hip thrust — upper back on bench, bar or weight across hips — but extend one leg straight out. "
                     "Drive the planted foot into the floor, lift hips to full extension, and squeeze the working glute hard. "
                     "Roughly doubles the demand on each glute vs the bilateral version. Keep the extended leg parallel to the floor."},

    {"name": "Cossack Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "hamstrings", "inner thigh"],
     "equipment": BW, "is_compound": True, "met_value": "4.5",
     "instructions": "Stand wide. Shift your weight onto one leg and squat deep to that side, keeping the heel flat. "
                     "The opposite leg extends straight with foot flat or heel up. Hold the bottom for a moment to stretch the inner thigh and hip. "
                     "Push through the bent-leg heel to rise. Simultaneously builds quad strength and hip mobility — especially useful for squat depth."},

    # ── Core ──────────────────────────────────────────────────────────────────
    {"name": "Hollow Hold",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.0",
     "instructions": "Lie on your back. Press your lower back firmly into the floor (no gap). Arms extend overhead, legs extend and lift so only the mid-back touches the floor. "
                     "The body forms a shallow dish or 'hollow'. Hold, breathing steadily. "
                     "Regress by bending the knees or lowering the arms. Progress by lowering the legs closer to the floor. "
                     "Foundational gymnastics core position — superior to sit-ups for spine health."},

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIVATION / PREHAB (warm-up drills from The Year Plan constants)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Clamshell",
     "category": F, "primary_muscle": GLUT,
     "equipment": BW, "met_value": "2.0",
     "instructions": "Lie on your side, knees bent to 90°, hips stacked. Keeping feet together, rotate the top knee open like a clamshell lid — stop when the pelvis wants to roll back. "
                     "Lower under control. The movement should be felt in the outer glute, not the lower back. "
                     "Add a resistance band just above the knees to increase difficulty."},

    {"name": "Fire Hydrant",
     "category": F, "primary_muscle": GLUT,
     "equipment": BW, "met_value": "2.0",
     "instructions": "On hands and knees, spine neutral. Keeping the knee bent at 90°, lift one leg out to the side (like a dog at a fire hydrant) until the hip is at 90° of abduction. "
                     "Hold briefly, lower slowly. Works hip abductors and external rotators — critical for knee stability in squats and lunges."},

    {"name": "Side-lying Hip Abduction",
     "category": F, "primary_muscle": GLUT,
     "equipment": BW, "met_value": "2.0",
     "instructions": "Lie on your side, body in a straight line. Lift the top leg toward the ceiling, leading with the heel, until ~45° of abduction. "
                     "Pause, lower with control. Keep the foot flexed and toes pointing slightly toward the floor to target the gluteus medius. "
                     "Add an ankle weight or resistance band for progression."},

    {"name": "Frog Rocks",
     "category": F, "primary_muscle": FULL,
     "equipment": BW, "met_value": "2.0",
     "instructions": "From a frog position (on all fours, knees wide and turned out, feet in line with knees), rock the hips back toward the heels — feeling the inner-thigh and hip stretch — "
                     "then rock forward. Keep the spine neutral throughout. "
                     "A dynamic hip opener that primes the hip for deep squatting patterns. 10 slow rocks per set."},

    {"name": "Hip CARs",
     "category": F, "primary_muscle": GLUT, "secondary_muscles": ["core"],
     "equipment": BW, "met_value": "2.0",
     "instructions": "On all fours or standing holding a support. Trace the largest possible circle with one knee — flex the hip, externally rotate, extend, internally rotate, and return. "
                     "CARs (Controlled Articular Rotations) train the end-range strength of the hip capsule and maintain joint health. "
                     "Move as slowly as possible; keep the rest of the body completely still. 3–5 circles each direction, each side."},

    {"name": "90/90 Hip Rotation",
     "category": F, "primary_muscle": GLUT, "secondary_muscles": ["core"],
     "equipment": BW, "met_value": "2.0",
     "instructions": "Sit on the floor with both legs bent at 90° — front leg with the shin across your body, back leg at 90° to the side. "
                     "Keeping the torso upright, rotate to face the back leg (windshield-wiper motion), then rotate back to the front leg. "
                     "Each transition is one rep. A non-negotiable hip-mobility drill for squat and hinge patterns."},

    {"name": "Leg Swings",
     "category": F, "primary_muscle": FULL,
     "equipment": BW, "met_value": "2.0",
     "instructions": "Hold a wall or upright for balance. Swing one leg forward and back in a controlled arc — gradually increasing the range over 10 reps. "
                     "Then swing the same leg side-to-side across the body and out. Switch legs. "
                     "Dynamic hamstring, hip flexor, and adductor warm-up — do before any lower-body session."},

    # ══════════════════════════════════════════════════════════════════════════
    # FLEXIBILITY / COOLDOWN (from The Year Plan constants)
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Child's Pose",
     "category": F, "primary_muscle": BACK, "secondary_muscles": ["shoulders"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "Kneel, sit hips back toward heels, reach arms forward on the floor and relax the forehead down. "
                     "Hold 30–60 s. Walk the hands to the left and right to deepen the lat stretch. "
                     "Excellent cooldown after any pressing or back session."},

    {"name": "Frog Stretch",
     "category": F, "primary_muscle": FULL, "secondary_muscles": ["inner thigh"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "On hands and knees, widen the knees as far as comfortable with feet inline with knees. "
                     "Shift the hips back slowly to deepen the inner-thigh (adductor) and hip stretch. "
                     "Hold 30–60 s or rock gently. Pairs well with frog rocks as a static hold at the end of the warm-up."},

    {"name": "Butterfly Stretch",
     "category": F, "primary_muscle": FULL, "secondary_muscles": ["inner thigh"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "Sit with soles of feet pressed together, knees falling outward. Hold the feet and gently press the knees toward the floor. "
                     "Lean forward from the hips (not the spine) to deepen. Hold 30–60 s. "
                     "Targets the inner thighs, groin, and hip flexors. A standard cooldown for lower-body sessions."},

    # ══════════════════════════════════════════════════════════════════════════
    # CARDIO — HIIT FINISHER MOVEMENTS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "High Knees",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["core"],
     "equipment": BW, "met_value": "8.0",
     "instructions": "Run in place, driving the knees up to hip height on each stride. Pump the arms in opposition. "
                     "Go for 20–30 reps or 20–30 seconds. Used as a warm-up activation drill or as a high-intensity HIIT component. "
                     "Focus on posture — chest up, core braced, land softly on the balls of the feet."},

    {"name": "Jumping Jacks",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["shoulders"],
     "equipment": BW, "met_value": "7.0",
     "instructions": "From standing, jump to a wide stance while raising both arms overhead. Jump back to the start position. "
                     "A low-intensity full-body warm-up movement. Can be substituted with step jacks (no jump) for a lower-impact option. "
                     "Often used in HIIT finishers for active rest between harder movements."},

    # ══════════════════════════════════════════════════════════════════════════
    # PELVIC FLOOR — from The Year Plan daily protocol
    # Prescribed every day including rest days.
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Kegel — Long Hold",
     "category": F, "primary_muscle": CORE,
     "equipment": BW, "met_value": "1.5",
     "instructions": "Sit, stand, or lie down in a comfortable position. "
                     "Gently contract the pelvic-floor muscles — imagine stopping the flow of urine — and hold for 3–5 seconds. "
                     "Fully relax for 3–5 seconds between each rep. Do 10 reps per round, 2–3 rounds, 1–2 × per day. "
                     "Key points: isolate the pelvic floor only — do not squeeze the glutes, abs, or inner thighs. "
                     "Keep breathing throughout; never hold your breath. "
                     "If you feel pain or downward pressure, ease off and consult a pelvic-floor physiotherapist."},

    {"name": "Kegel — Quick Flick",
     "category": F, "primary_muscle": CORE,
     "equipment": BW, "met_value": "1.5",
     "instructions": "In a comfortable position, rapidly contract and fully release the pelvic-floor muscles in quick succession — each squeeze-and-release takes about 1 second. "
                     "Do 10 quick flicks per round, 2–3 rounds, 1–2 × per day. "
                     "Trains the fast-twitch fibres of the pelvic floor (important for coughing, sneezing, and sudden load). "
                     "Always follow quick flicks with a full, conscious relaxation of the pelvic floor. "
                     "Perform after long holds in the same session."},

    # ══════════════════════════════════════════════════════════════════════════
    # CHEST — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Pec Deck",
     "category": S, "primary_muscle": CHEST,
     "equipment": MA, "met_value": "4.0",
     "instructions": "Sit upright, forearms on pads. Bring pads together in a wide arc, squeezing the pecs at full adduction. "
                     "Keep elbows at shoulder height and resist the weight on the return — do not let it slam back. "
                     "Good isolation finisher; the machine path keeps tension through the inner range where free weights drop off."},

    {"name": "Incline Cable Fly",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders"],
     "equipment": CB, "met_value": "4.0",
     "instructions": "Set an adjustable bench to 30–45° between two low pulleys. Hold a handle in each hand, arms slightly bent. "
                     "Drive the handles upward and inward in a hugging arc, meeting above the chest. "
                     "Emphasises the upper pec clavicular head; cable provides constant tension unlike a barbell."},

    {"name": "Svend Press",
     "category": S, "primary_muscle": CHEST,
     "equipment": OT, "met_value": "3.5",
     "instructions": "Stand holding two weight plates pressed together at chest height. "
                     "Push them straight out to arm's length, squeezing the plates together as hard as possible throughout. "
                     "Return slowly. The inward squeeze creates continuous inner-chest activation without heavy loads."},

    {"name": "Landmine Press",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders", "triceps"],
     "equipment": BB, "is_compound": True, "met_value": "4.5",
     "instructions": "Anchor one end of a barbell in a corner or landmine attachment. "
                     "Hold the free end at shoulder height with one or both hands. Press the bar forward and up in an arc to full extension, lower under control. "
                     "The arc of motion closely mimics a push-up and is very shoulder-friendly."},

    {"name": "Wide Push-up",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["shoulders", "triceps"],
     "equipment": BW, "is_compound": True, "met_value": "3.8",
     "instructions": "Hands placed 1.5–2× shoulder-width apart, fingers angled outward 30–45°. "
                     "Lower chest to floor, elbows travel outward. Press back to lockout. "
                     "Wider hand position emphasises the outer/lower pec and reduces tricep contribution vs standard push-up."},

    {"name": "Archer Push-up",
     "category": S, "primary_muscle": CHEST, "secondary_muscles": ["triceps", "core"],
     "equipment": BW, "is_compound": True, "met_value": "4.5",
     "instructions": "Wide push-up stance. As you lower, shift weight entirely to one arm — that arm bends fully while the opposite arm stays straight and acts as a guide. "
                     "Alternate sides each rep. Bridges the gap between push-up and one-arm push-up."},

    # ══════════════════════════════════════════════════════════════════════════
    # BACK — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "T-Bar Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps", "rear delts"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Straddle a landmine barbell or T-bar station. Hinge forward, grip the handle with a neutral or overhand grip. "
                     "Row the bar to your chest, driving elbows back and squeezing the shoulder blades together. "
                     "Keep the spine neutral and avoid jerking the torso."},

    {"name": "Inverted Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps", "core"],
     "equipment": BW, "is_compound": True, "met_value": "4.0",
     "instructions": "Lie under a bar set at hip height (Smith machine or squat rack). Grip overhand, body in a straight line, heels on the floor. "
                     "Pull chest to bar, leading with the elbows, squeeze shoulder blades at the top. "
                     "Lower the bar or elevate feet to adjust difficulty. An accessible pull-up regression."},

    {"name": "Straight-arm Pulldown",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["core"],
     "equipment": CB, "met_value": "3.5",
     "instructions": "High pulley, rope or straight bar. Stand back, arms extended at eye level. "
                     "With elbows locked, pull the handle down to your hips in a wide arc — the movement comes entirely from the lat, not the bicep. "
                     "Squeeze hard at the bottom and return slowly. A powerful lat isolation that teaches the muscle-mind connection before rows."},

    {"name": "Rack Pull",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["glutes", "hamstrings", "traps"],
     "equipment": BB, "is_compound": True, "met_value": "5.5",
     "instructions": "Set bar in a rack at just below knee height. Deadlift from this elevated position. "
                     "The shortened ROM allows heavier loads, overloading the upper back, traps, and lockout. "
                     "Keep the same tight brace and hip-drive cues as a conventional deadlift."},

    {"name": "Meadows Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps", "rear delts"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Stand perpendicular to a landmine barbell, feet staggered. Take a staggered stance — lead foot forward on the same side as the working arm. "
                     "Hinge and grip the sleeve of the bar with one hand using a pronated grip. "
                     "Row the bar up and slightly back toward your hip. The angle provides a unique stretch and a high elbow finish that hammers the upper back."},

    {"name": "Single-arm Lat Pulldown",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps"],
     "equipment": CB, "is_compound": True, "met_value": "4.0",
     "instructions": "Single handle on a high pulley. Sit or kneel, pull handle to shoulder with one arm. "
                     "Focus on pulling the elbow down and back — the same cue as a pull-up — rather than pulling with the hand. "
                     "Unilateral work exposes and corrects left-right strength imbalances."},

    {"name": "Dumbbell Shrug",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["back"],
     "equipment": DB, "met_value": "3.5",
     "instructions": "Stand holding heavy dumbbells at sides. Elevate shoulders straight toward the ears as high as possible, hold 1 s at the top, lower fully. "
                     "Neutral dumbbell grip reduces wrist strain vs a barbell and allows freer scapular movement."},

    {"name": "Cable Pull-through",
     "category": S, "primary_muscle": GLUT, "secondary_muscles": ["hamstrings", "back"],
     "equipment": CB, "is_compound": True, "met_value": "4.5",
     "instructions": "Face away from a low pulley, rope between your legs. Hip-hinge forward with soft knees until you feel the glute and hamstring stretch. "
                     "Drive the hips forward to stand, squeezing the glutes at lockout — do not use the arms to pull. "
                     "Teaches the hip-hinge pattern with less lower-back loading than a deadlift."},

    # ══════════════════════════════════════════════════════════════════════════
    # SHOULDERS — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Dumbbell Front Raise",
     "category": S, "primary_muscle": SHLD,
     "equipment": DB, "met_value": "3.5",
     "instructions": "Stand with dumbbells at thighs, palms facing back. Raise both arms forward to shoulder height, slight bend in the elbow, thumbs up. "
                     "Lower under control. Isolates the anterior deltoid. Avoid swinging the torso; if you must, the weight is too heavy."},

    {"name": "Plate Front Raise",
     "category": S, "primary_muscle": SHLD,
     "equipment": OT, "met_value": "3.5",
     "instructions": "Hold a weight plate at the 3 and 9 o'clock positions. Raise it to shoulder height with arms nearly straight, lower slowly. "
                     "The neutral-width grip and plate diameter create a slightly different stimulus than dumbbells and the grip challenge is higher."},

    {"name": "Band Pull-Apart",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["back"],
     "equipment": BA, "met_value": "2.5",
     "instructions": "Hold a light resistance band at arm's length in front at shoulder height. Pull it apart to a T, squeezing the rear delts and mid-traps. "
                     "Return under control — do not let the band snap back. Exceptional shoulder-health prehab and warm-up; do 20–30 reps per set."},

    {"name": "Pike Push-up",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["triceps", "chest"],
     "equipment": BW, "is_compound": True, "met_value": "4.0",
     "instructions": "Hips-up push-up position forming an inverted V. Lower the top of your head toward the floor between your hands, press back to start. "
                     "The angled torso shifts emphasis heavily toward the shoulders. It is the key regression for the handstand push-up."},

    {"name": "Handstand Push-up",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["triceps", "core"],
     "equipment": BW, "is_compound": True, "met_value": "6.0",
     "instructions": "Kick up into a handstand against a wall, hands shoulder-width. Lower the crown of your head to the floor, press back to lockout. "
                     "Build with wall pike push-ups and partial range first. One of the most demanding pressing movements — develops elite shoulder and tricep strength."},

    {"name": "Cuban Press",
     "category": S, "primary_muscle": SHLD,
     "equipment": DB, "met_value": "3.5",
     "instructions": "Hang dumbbells at sides, internally rotated. Perform an upright row to shoulder height, pause; externally rotate so hands face forward (like a front-squat rack); press overhead; reverse. "
                     "Works external rotation strength and is excellent shoulder prehab for overhead athletes."},

    # ══════════════════════════════════════════════════════════════════════════
    # BICEPS — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "EZ-bar Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": BB, "met_value": "3.5",
     "instructions": "Grip the angled inner grips of an EZ bar, palms semi-supinated. Curl to the upper chest, lower fully. "
                     "The angled grip reduces wrist and elbow stress vs a straight bar while still hitting both bicep heads effectively."},

    {"name": "Zottman Curl",
     "category": S, "primary_muscle": BICE, "secondary_muscles": ["forearms"],
     "equipment": DB, "met_value": "3.5",
     "instructions": "Curl dumbbells with a supinated grip (bicep concentric), rotate to pronated at the top, lower with a reverse-curl (eccentric). "
                     "Each rep trains both the bicep (curling up) and the brachioradialis/forearm extensors (lowering down) — two movements for the price of one."},

    {"name": "Spider Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": BB, "met_value": "3.5",
     "instructions": "Lie prone on a 45° incline bench. Let arms hang straight down and curl the bar up to full contraction. "
                     "Gravity keeps tension on the bicep through the entire range — both the peak contraction and the stretched position are fully loaded."},

    {"name": "Reverse Curl",
     "category": S, "primary_muscle": FORE, "secondary_muscles": ["biceps"],
     "equipment": BB, "met_value": "3.0",
     "instructions": "Overhand (pronated) grip on a barbell. Curl to full contraction, lower under control. "
                     "Transfers emphasis to the brachioradialis and brachialis — the muscles that fill the upper arm under the bicep. Builds forearm mass and grip strength."},

    {"name": "Cross-body Hammer Curl",
     "category": S, "primary_muscle": BICE, "secondary_muscles": ["forearms"],
     "equipment": DB, "met_value": "3.5",
     "instructions": "Neutral grip. Instead of curling straight up, curl the dumbbell diagonally across the body toward the opposite shoulder. "
                     "Alternate arms. The angle increases brachialis recruitment and provides a longer moment arm through the mid-range."},

    {"name": "Bayesian Curl",
     "category": S, "primary_muscle": BICE,
     "equipment": CB, "met_value": "3.5",
     "instructions": "Set a single cable behind you at hip height. Step forward to create tension, arm extended back. "
                     "Curl the handle forward and up to full contraction. The cable behind the body provides peak tension at the stretched/bottom position — "
                     "where free weights are weakest — making it highly effective for bicep development."},

    # ══════════════════════════════════════════════════════════════════════════
    # TRICEPS — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Single-arm Overhead Cable Extension",
     "category": S, "primary_muscle": TRIC,
     "equipment": CB, "met_value": "3.5",
     "instructions": "Set pulley high, grip a single handle, face away from the stack. Hold handle behind head, elbow pointed forward. "
                     "Extend the forearm to full lockout, squeeze the tricep, return slowly. Fully stretches the long head of the tricep at the start position."},

    {"name": "Tate Press",
     "category": S, "primary_muscle": TRIC, "secondary_muscles": ["chest"],
     "equipment": DB, "met_value": "3.5",
     "instructions": "Lie on a bench, dumbbells over chest with elbows flared wide. Bend elbows to lower the dumbbells toward the inner chest — not the forehead. "
                     "Press back up from the chest. The wide-elbow path creates a unique loading angle on the tricep medial head."},

    {"name": "JM Press",
     "category": S, "primary_muscle": TRIC, "secondary_muscles": ["chest"],
     "equipment": BB, "is_compound": True, "met_value": "4.5",
     "instructions": "Lie on a bench, grip slightly inside shoulder-width. Lower the bar toward the chin/throat — a hybrid path between a skull crusher and a close-grip press. "
                     "The bar path should feel like the forearms fold toward the face. Press back to lockout. Heavy tricep builder popularised in powerlifting."},

    # ══════════════════════════════════════════════════════════════════════════
    # FOREARMS — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Dead Hang",
     "category": S, "primary_muscle": FORE, "secondary_muscles": ["back", "shoulders"],
     "equipment": BW, "met_value": "2.5",
     "instructions": "Hang from a pull-up bar with straight arms and relaxed shoulders (do not actively pull shoulder blades down). "
                     "Hold for time. Builds grip endurance, decompresses the spine, and gently stretches the lat and shoulder. "
                     "Progress from 30 s to 60 s+ and add weight via a dumbbell between the feet."},

    {"name": "Wrist Roller",
     "category": S, "primary_muscle": FORE,
     "equipment": OT, "met_value": "3.0",
     "instructions": "Hold a wrist-roller at arm's length. Roll the weight up by alternately winding each wrist forward, then unwind back down. "
                     "Equally works both the flexors (rolling up) and the extensors (lowering down). "
                     "One of the most effective forearm developers — the full range pump is unmatched."},

    {"name": "Plate Pinch",
     "category": S, "primary_muscle": FORE,
     "equipment": OT, "met_value": "2.5",
     "instructions": "Pinch two smooth-faced weight plates together with one hand, fingers on one side and thumb on the other. "
                     "Hold for time or carry for distance. Trains the thumb-opposing pinch-grip strength that grip-intensive sports demand."},

    # ══════════════════════════════════════════════════════════════════════════
    # LEGS — QUADS additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Zercher Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "core", "back"],
     "equipment": BB, "is_compound": True, "met_value": "6.0",
     "instructions": "Rest the bar in the crooks of the elbows, arms bent and crossed at the chest. Squat to full depth — the bar position forces an upright torso. "
                     "Stand back up, keeping elbows high. Brutal core and upper-back demand; also excellent for quad depth."},

    {"name": "Cyclist Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes"],
     "equipment": BW, "is_compound": True, "met_value": "5.0",
     "instructions": "Elevate your heels on weight plates or a wedge, feet close together. Squat to full depth — the heel elevation dramatically shifts the load onto the quads. "
                     "Add a goblet hold or barbell for load. Often used for quad hypertrophy when knee-over-toe range is the goal."},

    {"name": "Lateral Lunge",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "inner thigh"],
     "equipment": BW, "is_compound": True, "met_value": "4.5",
     "instructions": "Step out wide to one side, bend that knee and push the hips back — the other leg stays straight. "
                     "Drive through the heel to return to standing. Add dumbbells for load. Works the adductors and VMO through a lateral plane of motion."},

    {"name": "Wall Sit",
     "category": S, "primary_muscle": QUAD,
     "equipment": BW, "met_value": "4.0",
     "instructions": "Back flat against a wall, slide down until thighs are parallel to the floor (90° knee angle). Hold for time. "
                     "Pure quad isometric — great for building endurance, racing against a timer, or as a finisher on leg day."},

    {"name": "Jump Squat",
     "category": C, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "calves"],
     "equipment": BW, "is_compound": True, "met_value": "8.0",
     "instructions": "Squat to parallel, then explode upward off both feet as high as possible. Land softly, absorb through hips and knees, and go straight into the next rep. "
                     "Develops lower-body power and raises the heart rate quickly. Can add a light barbell or dumbbells once bodyweight is mastered."},

    {"name": "Pause Squat",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "core"],
     "equipment": BB, "is_compound": True, "met_value": "6.0",
     "instructions": "Perform a back squat but pause at the bottom (hips below parallel) for 2–3 seconds before driving up. "
                     "The pause eliminates stretch-reflex and builds strength out of the hole. "
                     "Reduces load by 10–20% vs regular squat; keep the brace, do not relax at the bottom."},

    {"name": "Dumbbell Lunge",
     "category": S, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "hamstrings"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Stand with dumbbells at sides. Step forward, lower back knee toward the floor, keep front shin vertical. "
                     "Return to standing either by stepping back or stepping through into the next lunge. "
                     "The loaded stationary lunge — more controlled than a walking lunge, better for focusing on single-leg strength."},

    # ══════════════════════════════════════════════════════════════════════════
    # LEGS — HAMSTRINGS additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Glute-Ham Raise",
     "category": S, "primary_muscle": HAMS, "secondary_muscles": ["glutes", "core"],
     "equipment": MA, "met_value": "5.0",
     "instructions": "Kneel on a GHD machine with feet anchored and thighs against the pad. Lower your torso forward under control by flexing at the knee, "
                     "using the hamstrings to resist gravity. At the bottom push up with the hands, then drive back to upright using only the hamstrings and glutes. "
                     "One of the most effective hamstring mass builders; start with band assistance."},

    {"name": "Stability Ball Leg Curl",
     "category": S, "primary_muscle": HAMS, "secondary_muscles": ["glutes", "core"],
     "equipment": OT, "met_value": "4.0",
     "instructions": "Lie on your back, heels resting on a stability ball, hips extended. "
                     "Curl the ball toward your glutes by bending the knees, keeping hips up throughout. "
                     "Extend back out under control. A low-equipment hamstring isolation exercise that also challenges the core anti-extension."},

    {"name": "Stiff-leg Deadlift",
     "category": S, "primary_muscle": HAMS, "secondary_muscles": ["back", "glutes"],
     "equipment": BB, "is_compound": True, "met_value": "5.0",
     "instructions": "Stand with knees completely locked. Hinge forward at the hips, lowering the bar along the legs until you feel maximum hamstring tension (usually mid-shin). "
                     "Drive the hips forward to return. Unlike the RDL, the knees do not bend — this creates greater hamstring stretch but demands more lower-back stability."},

    {"name": "Single-leg Dumbbell RDL",
     "category": S, "primary_muscle": HAMS, "secondary_muscles": ["glutes", "core"],
     "equipment": DB, "is_compound": True, "met_value": "4.5",
     "instructions": "Stand on one leg, soft knee. Hinge forward as the free leg extends behind, lowering the dumbbell along the standing leg until you feel the hamstring load. "
                     "Return by driving the hip forward — use the glute, not the lower back. "
                     "Corrects left-right imbalances and develops unilateral hip-hinge control."},

    # ══════════════════════════════════════════════════════════════════════════
    # LEGS — GLUTES additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Donkey Kick",
     "category": S, "primary_muscle": GLUT,
     "equipment": BW, "met_value": "3.0",
     "instructions": "On hands and knees, spine neutral. Keeping the knee bent at 90°, drive one heel toward the ceiling until the hip is fully extended. "
                     "Squeeze the glute at the top, lower under control. Add ankle weight or cable attachment for load. "
                     "Targets the gluteus maximus with minimal hamstring contribution."},

    {"name": "Lateral Band Walk",
     "category": F, "primary_muscle": GLUT, "secondary_muscles": ["core"],
     "equipment": BA, "met_value": "3.0",
     "instructions": "Place a resistance band just above the knees or around the ankles. Slightly bend the hips and knees into an athletic stance. "
                     "Step sideways against the band resistance — lead foot steps out, trail foot follows. "
                     "Keep constant tension in the band; do not let knees cave inward. "
                     "Classic glute medius activation drill for knee-stability prehab."},

    {"name": "Frog Pump",
     "category": S, "primary_muscle": GLUT,
     "equipment": BW, "met_value": "3.0",
     "instructions": "Lie on your back, soles of feet pressed together with knees flared out (butterfly position). "
                     "Drive hips up into full extension, squeezing the glutes hard, lower to just above the floor. "
                     "The externally-rotated leg position pre-positions the glute for maximal contraction. "
                     "Light but intense — sets of 20–30 reps are common."},

    {"name": "Reverse Hyper",
     "category": S, "primary_muscle": GLUT, "secondary_muscles": ["hamstrings", "back"],
     "equipment": MA, "met_value": "3.5",
     "instructions": "Lie face down on the reverse hyper machine with hips at the edge, feet in the strap. "
                     "Swing legs up until the body is horizontal, squeezing glutes at the top, lower under control with a slight pendulum swing. "
                     "Decompresses the lumbar spine on the way down while strengthening the posterior chain on the way up. "
                     "Excellent recovery and strength tool for the lower back and glutes."},

    {"name": "Monster Walk",
     "category": F, "primary_muscle": GLUT,
     "equipment": BA, "met_value": "3.0",
     "instructions": "Band around ankles, athletic quarter-squat position. Walk forward diagonally — lead foot steps forward and out, trail foot follows while maintaining band tension. "
                     "Then walk backward to start. Trains hip abductors and external rotators in a dynamic pattern that mirrors athletic movement."},

    # ══════════════════════════════════════════════════════════════════════════
    # LEGS — CALVES additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Tibialis Raise",
     "category": S, "primary_muscle": CALV,
     "equipment": BW, "met_value": "2.5",
     "instructions": "Stand with your back and heels against a wall, feet a few inches out. "
                     "Raise the toes and forefoot as high as possible (dorsiflexion), hold 1 s, lower. "
                     "Strengthens the tibialis anterior — the shin muscle — which is the most under-trained lower-leg muscle. "
                     "Directly prevents and rehabilitates shin splints. Progress to weighted ankle-over-ankle version."},

    {"name": "Donkey Calf Raise",
     "category": S, "primary_muscle": CALV,
     "equipment": OT, "met_value": "3.0",
     "instructions": "Hinge forward at the hips, supporting the torso on a bench. Have a partner sit across the hips or use a dedicated machine. "
                     "Rise on the balls of the feet to full extension, pause, lower heel below the step. "
                     "The hipped-over position stretches the calf more than standing raises — studies show the highest gastrocnemius activation of any calf variation."},

    # ══════════════════════════════════════════════════════════════════════════
    # CORE — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Crunch",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.0",
     "instructions": "Lie on back, knees bent, feet flat, hands lightly behind head. "
                     "Curl only the shoulder blades off the floor — the lower back stays down. "
                     "Exhale on the way up, inhale on the way down. Small range but high muscle activation when done slowly and with intention."},

    {"name": "Sit-up",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["hip flexors"],
     "equipment": BW, "met_value": "3.5",
     "instructions": "Lie on back, knees bent, feet anchored. Curl the torso all the way up until elbows touch knees, lower under control. "
                     "Greater range than a crunch; includes hip flexors through the full range. "
                     "Add a twist at the top for oblique involvement."},

    {"name": "Reverse Crunch",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "3.5",
     "instructions": "Lie on back, hands at sides or under hips. Bring knees to 90°. "
                     "Use the lower abs to curl the pelvis off the floor, drawing the knees toward the chest. Lower under control. "
                     "Emphasises the lower portion of the rectus abdominis and hip flexors without compressing the lumbar spine."},

    {"name": "Flutter Kicks",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["hip flexors"],
     "equipment": BW, "met_value": "4.0",
     "instructions": "Lie on back, lower back pressed to the floor, legs extended and lifted 6 inches. "
                     "Rapidly alternate kicking each leg up and down in a small scissor motion. "
                     "Keep the lower back pinned — if it arches, raise the legs slightly. Hold for time or reps."},

    {"name": "Windshield Wiper",
     "category": S, "primary_muscle": CORE,
     "equipment": BW, "met_value": "4.5",
     "instructions": "Hang from a bar, legs raised to horizontal (or vertical for advanced). "
                     "Rotate both legs together side to side in a slow, controlled arc like windshield wipers. "
                     "The further the legs from vertical, the greater the demand. Exceptional oblique and anti-rotation strength builder."},

    {"name": "Dragon Flag",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["back", "hip flexors"],
     "equipment": BW, "met_value": "5.0",
     "instructions": "Lie on a bench, grip the bench behind your head. Brace the entire body into a straight line from shoulders to feet and raise it off the bench. "
                     "Lower under full control — only the upper back stays on the bench. Return to top without breaking the straight body position. "
                     "One of the most demanding core exercises; build up through tuck and single-leg progressions."},

    {"name": "L-sit",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["triceps", "hip flexors"],
     "equipment": BW, "met_value": "4.5",
     "instructions": "Support on parallel bars, dip bars, or floor with hands. Compress the core and lift both legs to horizontal — forming an L. "
                     "Hold for time. Demands simultaneous hip-flexor strength and core compression. "
                     "Regress by bending one or both knees, progressing toward full extension."},

    {"name": "Stir the Pot",
     "category": S, "primary_muscle": CORE,
     "equipment": OT, "met_value": "4.0",
     "instructions": "Forearms on a stability ball, body in a straight plank line. "
                     "Draw small clockwise circles with the elbows — as if stirring a large pot — maintaining a rigid trunk with zero hip or pelvis movement. "
                     "Reverse direction after each set. One of the highest-EMG core exercises; the unstable surface forces constant adjustment."},

    {"name": "Cable Woodchop",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["shoulders"],
     "equipment": CB, "met_value": "4.0",
     "instructions": "Set cable high on one side. Stand perpendicular, feet shoulder-width. "
                     "Pull the handle diagonally down and across the body from high to low, rotating through the hips and trunk. "
                     "Resist the return under control. Trains rotational power and obliques in a functional diagonal plane."},

    {"name": "Landmine Rotation",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["shoulders", "back"],
     "equipment": BB, "met_value": "4.0",
     "instructions": "Stand over the anchor end of a landmine barbell, gripping the free end with both hands at arm's length. "
                     "Rotate the bar from hip to hip in a wide arc, pivoting on the feet and hips — the trunk rotates but the spine stays neutral. "
                     "Trains rotational power through a large range. Effective and shoulder-friendly."},

    {"name": "Toes to Bar",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["hip flexors", "back"],
     "equipment": BW, "met_value": "4.5",
     "instructions": "Dead hang from a pull-up bar. Engage the core, bring toes up to touch the bar by simultaneously flexing the hips and crunching the abs. "
                     "Lower with control. Requires lat engagement at the top to stabilise the shoulder. "
                     "Regress to knees-to-chest; progress to strict, no-swing reps."},

    {"name": "Superman",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["glutes"],
     "equipment": BW, "met_value": "2.5",
     "instructions": "Lie face down, arms extended overhead. Simultaneously lift arms, chest, and legs off the floor as high as possible, squeezing the glutes and back. "
                     "Hold 2 s at the top, lower slowly. Trains the erector spinae and glutes in extension. "
                     "A gentle but effective lower-back strengthener with no equipment required."},

    {"name": "Bird Dog",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["back", "glutes"],
     "equipment": BW, "met_value": "2.5",
     "instructions": "On hands and knees, spine neutral. Extend the opposite arm and leg simultaneously until both are horizontal. "
                     "Hold 2 s, return without touching the floor, repeat. "
                     "Builds anti-rotation and spinal stability; a foundational rehabilitation and warm-up movement."},

    # ══════════════════════════════════════════════════════════════════════════
    # KETTLEBELL — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Kettlebell Snatch",
     "category": S, "primary_muscle": FULL, "secondary_muscles": ["glutes", "back", "shoulders"],
     "equipment": KB, "is_compound": True, "met_value": "9.0",
     "instructions": "Hinge and hike the KB back. Drive the hips explosively, keeping the bell close to the body — guide it up the forearm (not in an arc) and punch through to lockout overhead in one fluid movement. "
                     "The bell should float to the top without banging the wrist. Lock out overhead with a straight arm and stable shoulder. "
                     "The gold standard of kettlebell conditioning: full-body power, grip, and endurance in one movement."},

    {"name": "Kettlebell Press",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["triceps", "core"],
     "equipment": KB, "is_compound": True, "met_value": "4.5",
     "instructions": "Clean the KB to rack position (knuckles at collarbone, elbow tucked, forearm vertical). "
                     "Brace the core and press straight overhead to full lockout. "
                     "The offset center of mass of the kettlebell creates greater instability than a dumbbell, demanding more rotator-cuff and lat involvement. Lower under control back to rack."},

    {"name": "Kettlebell Row",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["biceps"],
     "equipment": KB, "is_compound": True, "met_value": "4.5",
     "instructions": "Place one hand on a bench for support. Hold a kettlebell in the other hand, arm hanging straight. "
                     "Row the bell to the hip, leading with the elbow, squeezing the shoulder blade at the top. "
                     "The KB handle position allows a deeper stretch at the bottom vs a dumbbell."},

    {"name": "Kettlebell Deadlift",
     "category": S, "primary_muscle": BACK, "secondary_muscles": ["glutes", "hamstrings"],
     "equipment": KB, "is_compound": True, "met_value": "5.0",
     "instructions": "Stand over a kettlebell, feet shoulder-width. Hip-hinge with neutral spine to grip the handle. "
                     "Drive through the floor, extend hips to lockout. Lower by hinging back. "
                     "The single handle encourages a narrow grip which trains the lats to protect the spine — a great teaching deadlift for beginners."},

    {"name": "Kettlebell Windmill",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["shoulders", "glutes"],
     "equipment": KB, "met_value": "4.0",
     "instructions": "Press a kettlebell overhead with one arm. Push the hip out to the same side as the bell. "
                     "Keeping eyes on the KB, bend laterally and reach the opposite hand toward the inside of the foot. Return to standing. "
                     "Simultaneously demands shoulder stability, lateral core strength, and hip mobility."},

    {"name": "Kettlebell Halo",
     "category": S, "primary_muscle": SHLD, "secondary_muscles": ["core"],
     "equipment": KB, "met_value": "3.0",
     "instructions": "Hold a kettlebell by the horns (upside down, bell up) at chest height. "
                     "Circle the bell slowly around the head in as wide an arc as possible, keeping the core braced and torso still. "
                     "Reverse direction each rep. An excellent shoulder-mobility and rotator-cuff warm-up movement."},

    {"name": "Kettlebell Figure-8",
     "category": S, "primary_muscle": CORE, "secondary_muscles": ["back", "forearms"],
     "equipment": KB, "is_compound": True, "met_value": "5.5",
     "instructions": "Stand in a wide stance with soft knees. Pass the kettlebell in a figure-8 pattern around and between both legs, handing off between hands behind and in front. "
                     "Stay low and keep the core braced throughout. Builds rotational core strength, grip endurance, and hip mobility simultaneously."},

    # ══════════════════════════════════════════════════════════════════════════
    # CARDIO — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Walking",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["glutes", "calves"],
     "equipment": CV, "met_value": "3.5",
     "instructions": "Walk at a brisk pace (5–6 km/h). Keep posture upright, arms swinging naturally. "
                     "Daily low-intensity movement (LISS) is highly underrated for recovery, fat oxidation, and cardiovascular health. "
                     "Target 7,000–10,000 steps per day for baseline health."},

    {"name": "Swimming",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["back", "shoulders", "core"],
     "equipment": CV, "met_value": "8.0",
     "instructions": "Freestyle, breaststroke, or backstroke laps at steady pace. "
                     "The water provides full-body resistance with zero joint impact — ideal for injury rehabilitation and active recovery. "
                     "Steady-state for 20–40 min or interval sets (25–50 m sprints with rest) for conditioning."},

    {"name": "Hiking",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["glutes", "quads", "calves"],
     "equipment": CV, "met_value": "6.0",
     "instructions": "Walk on uneven terrain or incline at a sustained pace. The grade and surface changes increase caloric expenditure and demand more from the glutes, quads, and calves vs flat walking. "
                     "Add a loaded pack (rucking) to further increase intensity. Excellent low-impact cardio and mental-health benefit."},

    {"name": "Sprint Intervals",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["glutes", "hamstrings"],
     "equipment": CV, "met_value": "14.0",
     "instructions": "Alternate maximum-effort sprints (10–30 s) with full-recovery walking or standing rest (60–120 s). "
                     "Sprint at 90–100% of top speed on a track, grass, or treadmill. "
                     "As few as 4–6 sprint efforts per session produce significant VO2 max and anaerobic capacity improvements."},

    {"name": "Speed Skaters",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["glutes", "inner thigh"],
     "equipment": BW, "met_value": "7.5",
     "instructions": "Leap laterally from one foot to the other, landing on the outer foot and sweeping the trailing leg behind. "
                     "Reach the opposite hand toward the landing foot. Mimic a speed skater's gliding motion. "
                     "Trains lateral power and hip abductor strength while spiking the heart rate."},

    {"name": "Sled Pull",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["back", "biceps"],
     "equipment": OT, "is_compound": True, "met_value": "8.0",
     "instructions": "Attach a rope to a loaded sled behind you. Walk or drive backward, pulling the rope hand over hand to drag the sled toward you. "
                     "Or face the sled and row the rope to pull it forward. "
                     "Sled pulls with a rope hit the upper body and posterior chain differently from sled pushes and are more joint-friendly than heavy barbell rows."},

    {"name": "Rucking",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["glutes", "back", "core"],
     "equipment": OT, "met_value": "6.0",
     "instructions": "Walk at a brisk pace with a weighted backpack (rucksack). Start with 10% of bodyweight and build to 20–30%. "
                     "Keep posture upright — resist the pack's pull on the shoulders. "
                     "Rucking builds aerobic capacity, muscular endurance, and bone density with minimal injury risk."},

    {"name": "Shadow Boxing",
     "category": C, "primary_muscle": CARD, "secondary_muscles": ["shoulders", "core"],
     "equipment": BW, "met_value": "7.0",
     "instructions": "Move around an open space throwing jabs, crosses, hooks, and uppercuts at a non-existent opponent. "
                     "Stay on the balls of your feet, rotate the hips with each punch, keep the guard up. "
                     "Work 2–3 minute rounds with 60 s rest. Improves cardio, coordination, and shoulder endurance."},

    {"name": "Tire Flip",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["glutes", "back", "shoulders"],
     "equipment": OT, "is_compound": True, "met_value": "8.0",
     "instructions": "Drive fingers under the tire, hips low. Explosively drive through the legs, transitioning from a deadlift to a pressing movement as the tire rises. "
                     "Push the tire over and reset. "
                     "A full-body conditioning movement that combines lower-body power, upper-body pressing, and cardiovascular demand."},

    {"name": "Ski Erg",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["back", "core", "shoulders"],
     "equipment": CV, "met_value": "9.5",
     "instructions": "Grip handles overhead, brace core. Pull the handles down and back in a double-arm motion — hinge the hips slightly as the handles pass the waist. "
                     "Return to start with control. A total-body conditioning tool that emphasises the lats, core, and arms. "
                     "Excellent for HIIT intervals: 10–20 s max-effort pulls."},

    # ══════════════════════════════════════════════════════════════════════════
    # FLEXIBILITY / MOBILITY — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Standing Quad Stretch",
     "category": F, "primary_muscle": QUAD,
     "equipment": BW, "met_value": "1.5",
     "instructions": "Stand on one foot. Bend the other knee and hold the ankle, pulling the heel toward the glute. "
                     "Stand tall, squeeze the glute of the stretching leg and tuck the pelvis slightly to increase the hip-flexor component. "
                     "Hold 30–45 s per side. Do after any quad-dominant session."},

    {"name": "Couch Stretch",
     "category": F, "primary_muscle": QUAD, "secondary_muscles": ["hip flexors"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "Kneel with your back shin resting up a wall or couch, front leg in a lunge. "
                     "Drive the hips forward and down, squeezing the glute of the back leg. "
                     "One of the most effective hip-flexor and rectus-femoris stretches, especially important for people who sit for long hours."},

    {"name": "Thread the Needle",
     "category": F, "primary_muscle": BACK, "secondary_muscles": ["shoulders"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "On hands and knees. Slide one arm under the body as far as possible — shoulder and head follow, rotating the thoracic spine. "
                     "Hold 30 s, return and repeat on the other side. "
                     "Excellent upper-back rotation mobility drill; counteracts desk posture."},

    {"name": "Supine Spinal Twist",
     "category": F, "primary_muscle": BACK, "secondary_muscles": ["glutes"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "Lie on your back, bring one knee to the chest. Guide it across the body with the opposite hand, letting it fall toward the floor. "
                     "Extend the same-side arm out to the side, look away from the knee. "
                     "Hold 60 s per side. Releases the lower back and thoracic spine; ideal post-session or morning mobility."},

    {"name": "Doorway Pec Stretch",
     "category": F, "primary_muscle": CHEST, "secondary_muscles": ["shoulders"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "Stand in a doorway, place forearms on the frame at 90° elbows. "
                     "Step one foot forward and lean gently through the doorway until you feel the pec and front deltoid stretch. "
                     "Hold 30–60 s. Critical for anyone who bench-presses heavily or works at a desk."},

    {"name": "Standing Calf Stretch",
     "category": F, "primary_muscle": CALV,
     "equipment": BW, "met_value": "1.5",
     "instructions": "Stand facing a wall, hands on wall. Place one foot behind, heel flat on the floor. "
                     "Lean forward until you feel the calf stretch. Straighten the back knee for gastrocnemius; bend it slightly for soleus. "
                     "Hold 30–45 s each position per side. Essential after any running or calf-training session."},

    {"name": "Shoulder Cross-body Stretch",
     "category": F, "primary_muscle": SHLD, "secondary_muscles": ["back"],
     "equipment": BW, "met_value": "1.5",
     "instructions": "Bring one arm across the chest. Use the opposite hand or forearm to press the arm gently closer to the chest. "
                     "Hold 30 s per side. Targets the posterior capsule of the shoulder and the rear deltoid. "
                     "Essential for lifters who press heavily — restores internal rotation range."},

    # ══════════════════════════════════════════════════════════════════════════
    # BALANCE / FUNCTIONAL — additional
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Pistol Squat",
     "category": B, "primary_muscle": QUAD, "secondary_muscles": ["glutes", "core", "hamstrings"],
     "equipment": BW, "is_compound": True, "met_value": "5.0",
     "instructions": "Stand on one leg, the other extended forward. Descend into a full single-leg squat until the standing heel is on the floor and the hamstring touches the calf, "
                     "other leg floating horizontally. Drive back up to standing. "
                     "Requires exceptional quad strength, ankle mobility, and balance. "
                     "Regress with box pistols, assisted, or counterweight."},

    {"name": "Single-leg Stand (Balance)",
     "category": B, "primary_muscle": CORE, "secondary_muscles": ["glutes", "calves"],
     "equipment": BW, "met_value": "2.0",
     "instructions": "Stand on one foot with a soft knee. Progress through: eyes open on a firm surface → eyes closed → eyes open on a foam pad → eyes closed on foam pad. "
                     "Hold each stage for 30–60 s per side. Trains proprioception and ankle stability foundational to every lower-body movement."},

    # ══════════════════════════════════════════════════════════════════════════
    # OLYMPIC / FULL-BODY POWER
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Power Clean",
     "category": S, "primary_muscle": FULL, "secondary_muscles": ["glutes", "hamstrings", "back", "shoulders"],
     "equipment": BB, "is_compound": True, "met_value": "8.0",
     "instructions": "Bar over mid-foot, hips above knees. First pull: drive through the floor until bar passes knees. "
                     "Second pull: explosively extend hips, shrug, and pull the bar close to the body. "
                     "Third pull: drop under the bar, rotate elbows forward to catch in a front-squat rack position. Stand to finish. "
                     "Develops full-body explosive power; the foundation of Olympic weightlifting."},

    {"name": "Hang Power Clean",
     "category": S, "primary_muscle": FULL, "secondary_muscles": ["glutes", "hamstrings", "back", "shoulders"],
     "equipment": BB, "is_compound": True, "met_value": "7.5",
     "instructions": "Start with the bar at mid-thigh (hanging position). Hinge hips back, then explosively extend — same second and third pull as the power clean but without the floor start. "
                     "Easier to teach the hip-drive mechanics without the complexity of the first pull. "
                     "A staple in team sports and CrossFit programming."},

    {"name": "Thruster",
     "category": S, "primary_muscle": FULL, "secondary_muscles": ["quads", "glutes", "shoulders", "triceps"],
     "equipment": BB, "is_compound": True, "met_value": "8.0",
     "instructions": "Hold bar in front-squat rack position. Squat to full depth, and as you drive out of the hole use the momentum to press the bar overhead in one continuous movement. "
                     "Lower back to rack as you descend into the next squat. "
                     "A brutal conditioning movement combining a front squat and push-press; produces enormous metabolic demand."},

    {"name": "Devil Press",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["shoulders", "core", "glutes"],
     "equipment": DB, "is_compound": True, "met_value": "9.0",
     "instructions": "Hold a dumbbell in each hand. Perform a burpee (jump or step back to push-up, push-up optional, jump feet to hands). "
                     "From the bottom of the deadlift position, swing the dumbbells back between the legs and then explosively swing them overhead — like a double KB snatch. "
                     "A full-body conditioning movement combining a burpee, a swing, and a snatch."},

    {"name": "Man Maker",
     "category": C, "primary_muscle": FULL, "secondary_muscles": ["chest", "back", "shoulders", "core"],
     "equipment": DB, "is_compound": True, "met_value": "9.0",
     "instructions": "Hold dumbbells in a push-up position. Perform a push-up, then row one dumbbell to the hip (renegade row), then the other. "
                     "Jump or step feet forward into a squat, perform a squat clean to standing, then press overhead. "
                     "Lower and repeat. Every major muscle group is loaded in a single complex — the ultimate conditioning movement."},

    {"name": "Clean and Press",
     "category": S, "primary_muscle": FULL, "secondary_muscles": ["glutes", "hamstrings", "back", "shoulders", "triceps"],
     "equipment": BB, "is_compound": True, "met_value": "7.0",
     "instructions": "Deadlift the bar to hip height, then perform a hang power clean to bring it to the front-rack position. "
                     "Without pausing, press the bar overhead to full lockout. Lower to rack, then drop the bar back to the hips and repeat. "
                     "A classic barbell complex that develops total-body strength, power, and conditioning in a single movement."},
]


class Command(BaseCommand):
    help = "Seed the exercise library (safe to re-run — uses update_or_create on slug)."

    def handle(self, *args, **options):
        created = updated = 0
        for payload in EXERCISES:
            payload.setdefault("met_value", "4.0")
            payload.setdefault("is_compound", False)
            payload.setdefault("secondary_muscles", [])
            payload["slug"] = slugify(payload["name"])
            _, was_created = Exercise.objects.update_or_create(
                slug=payload["slug"], defaults=payload
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Seeded exercises: {created} created, {updated} updated "
            f"({len(EXERCISES)} total)."
        ))
