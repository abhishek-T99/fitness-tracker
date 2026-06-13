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
