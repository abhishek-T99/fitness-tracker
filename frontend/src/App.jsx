import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute.jsx";
import AppLayout from "./components/AppLayout.jsx";

import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import CheckEmail from "./pages/CheckEmail.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import ResetPassword from "./pages/ResetPassword.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Workouts from "./pages/Workouts.jsx";
import WorkoutDetail from "./pages/WorkoutDetail.jsx";
import WorkoutEditor from "./pages/WorkoutEditor.jsx";
import Exercises from "./pages/Exercises.jsx";
import Routines from "./pages/Routines.jsx";
import RoutineEditor from "./pages/RoutineEditor.jsx";
import Nutrition from "./pages/Nutrition.jsx";
import Measurements from "./pages/Measurements.jsx";
import Goals from "./pages/Goals.jsx";
import Social from "./pages/Social.jsx";
import Achievements from "./pages/Achievements.jsx";
import Reminders from "./pages/Reminders.jsx";
import Profile from "./pages/Profile.jsx";
import WorkoutSession from "./pages/WorkoutSession.jsx";

export default function App() {
  return (
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
          <Route path="/measurements" element={<Measurements />} />
          <Route path="/goals" element={<Goals />} />
          <Route path="/social" element={<Social />} />
          <Route path="/achievements" element={<Achievements />} />
          <Route path="/reminders" element={<Reminders />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
