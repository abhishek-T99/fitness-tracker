/**
 * Central registry for TanStack Query cache keys.
 * Every useQuery key and every invalidateQueries call must use this file
 * so key mismatches are caught at the definition site, not at runtime.
 *
 * Hierarchy rules:
 *  - list() keys are prefixes of detail/parameterised keys.
 *  - invalidateQueries(["key"]) clears ALL entries that start with that prefix.
 */
export const qk = {
  achievements: {
    catalog:   () => ["achievementCatalog"],
    unlocked:  () => ["userAchievements"],
    streak:    () => ["streak"],
  },
  levels: {
    profile:    () => ["levelProfile"],
    challenges: () => ["weeklyChallenges"],
    leaderboard: () => ["leaderboard"],
  },
  workouts: {
    all:             ()             => ["workouts"],
    list:            (page)         => ["workouts", page],
    detail:          (id)           => ["workout", id],
    stats:           ()             => ["workoutStats"],
    exercisePicker:  (search)       => ["exercisePicker", search],
    exerciseHistory: (ids)          => ["exerciseHistory", ids],
    strengthHistory: (exId, days)   => ["strengthHistory", exId, days],
    volumeByMuscle:  (weeks)        => ["volumeByMuscle", weeks],
    activityHeatmap: (days)         => ["activityHeatmap", days],
  },
  routines: {
    all:    ()       => ["routines"],
    detail: (id)     => ["routine", id],
    picker: (search) => ["routinePicker", search],
  },
  exercises: {
    list: (...args) => ["exercises", ...args],
    tutorials: (slug) => ["exerciseTutorials", slug],
  },
  nutrition: {
    // Bare prefix used for invalidation; date-scoped used for fetching.
    meals:        (date)   => date ? ["meals", date]         : ["meals"],
    water:        (date)   => date ? ["water", date]         : ["water"],
    dailySummary: (date)   => date ? ["dailyNutrition", date] : ["dailyNutrition"],
    // Prefix "nutritionRange" (no args) invalidates every insights query at once,
    // so mutations in Nutrition.jsx don't need to know the current filters.
    rangeSummary: (params) => params ? ["nutritionRange", params] : ["nutritionRange"],
    foodSearch:   (search) => ["foodSearch", search],
    foodPicker:   (search) => ["foodPicker", search],
  },
  mealPlans: {
    list:    (weekStart) => ["mealPlans", weekStart],
    summary: (id)        => ["mealPlanSummary", id],
  },
  measurements: {
    all:            () => ["measurements"],
    latest:         () => ["measurementLatest"],
    weightHistory:  () => ["weightHistory"],
    bodyComposition: (days) => ["bodyComposition", days],
  },
  goals: {
    all: () => ["goals"],
  },
  social: {
    feed:        ()    => ["feed"],
    friends:     ()    => ["friends"],
    friendships: ()    => ["friendships"],
    searchUsers: (q)   => ["searchUsers", q],
  },
  reminders: {
    all: () => ["reminders"],
  },
  notifications: {
    all:         () => ["notifications"],
    unreadCount: () => ["notifications", "unread_count"],
    list:        () => ["notifications", "list"],
  },
  integrations: {
    all: () => ["integrations"],
  },
  reports: {
    all: () => ["fitnessReports"],
  },
  wellness: {
    today: () => ["todayWellness"],
  },
  ai: {
    session: (id) => ["aiSession", id],
  },
};
