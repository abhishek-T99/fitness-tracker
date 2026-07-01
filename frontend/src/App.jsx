import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute.jsx";
import AppLayout from "./components/AppLayout.jsx";

// Auth pages — eager (tiny, load on unauthenticated path)
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import CheckEmail from "./pages/CheckEmail.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import ResetPassword from "./pages/ResetPassword.jsx";

// All other pages — lazy loaded
const Dashboard      = lazy(() => import("./pages/Dashboard.jsx"));
const Workouts       = lazy(() => import("./pages/Workouts.jsx"));
const WorkoutDetail  = lazy(() => import("./pages/WorkoutDetail.jsx"));
const WorkoutEditor  = lazy(() => import("./pages/WorkoutEditor.jsx"));
const Exercises      = lazy(() => import("./pages/Exercises.jsx"));
const Routines       = lazy(() => import("./pages/Routines.jsx"));
const RoutineEditor  = lazy(() => import("./pages/RoutineEditor.jsx"));
const Nutrition           = lazy(() => import("./pages/Nutrition.jsx"));
const NutritionInsights   = lazy(() => import("./pages/NutritionInsights.jsx"));
const Measurements   = lazy(() => import("./pages/Measurements.jsx"));
const Goals          = lazy(() => import("./pages/Goals.jsx"));
const Social         = lazy(() => import("./pages/Social.jsx"));
const Achievements   = lazy(() => import("./pages/Achievements.jsx"));
const Reminders      = lazy(() => import("./pages/Reminders.jsx"));
const Profile        = lazy(() => import("./pages/Profile.jsx"));
const WorkoutSession = lazy(() => import("./pages/WorkoutSession.jsx"));
const MealPlan       = lazy(() => import("./pages/MealPlan.jsx"));
const Progress       = lazy(() => import("./pages/Progress.jsx"));
const Leaderboard    = lazy(() => import("./pages/Leaderboard.jsx"));

export default function App() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center"><span className="text-slate-500 text-sm">Loading…</span></div>}>
      <Routes>
        {/* Public auth routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/check-email" element={<CheckEmail />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route element={<ProtectedRoute />}>
          {/* Full-screen workout session — no sidebar */}
          <Route path="/session/:routineId" element={<WorkoutSession />} />

          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />

            <Route path="/workouts" element={<Workouts />} />
            <Route path="/workouts/new" element={<WorkoutEditor />} />
            <Route path="/workouts/:id" element={<WorkoutDetail />} />
            <Route path="/workouts/:id/edit" element={<WorkoutEditor />} />

            <Route path="/exercises" element={<Exercises />} />

            <Route path="/routines" element={<Routines />} />
            <Route path="/routines/new" element={<RoutineEditor />} />
            <Route path="/routines/:id" element={<RoutineEditor />} />

            <Route path="/nutrition" element={<Nutrition />} />
            <Route path="/nutrition/insights" element={<NutritionInsights />} />
            <Route path="/meal-plan" element={<MealPlan />} />
            <Route path="/progress" element={<Progress />} />
            <Route path="/measurements" element={<Measurements />} />
            <Route path="/goals" element={<Goals />} />
            <Route path="/social" element={<Social />} />
            <Route path="/achievements" element={<Achievements />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/reminders" element={<Reminders />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}
