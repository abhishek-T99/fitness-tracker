/**
 * Tests for ProtectedRoute
 *
 * Covers: loading spinner, unauthenticated redirect (with from-location),
 * and successful render of child routes when authenticated.
 */

jest.mock("../../contexts/AuthContext.jsx", () => ({
  useAuth: jest.fn(),
}));

import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import ProtectedRoute from "../../components/ProtectedRoute.jsx";
import { useAuth } from "../../contexts/AuthContext.jsx";

function renderWithRouter(initialPath = "/dashboard") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<div>Dashboard</div>} />
          <Route path="/profile"   element={<div>Profile</div>} />
        </Route>
        <Route path="/login" element={<div data-testid="login-page">Login</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  it("renders a loading indicator while auth state is resolving", () => {
    useAuth.mockReturnValue({ user: null, loading: true });
    renderWithRouter();
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("redirects to /login when the user is not authenticated", () => {
    useAuth.mockReturnValue({ user: null, loading: false });
    renderWithRouter("/dashboard");
    expect(screen.getByTestId("login-page")).toBeInTheDocument();
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });

  it("renders the child route when the user is authenticated", () => {
    useAuth.mockReturnValue({ user: { id: 1, username: "alice" }, loading: false });
    renderWithRouter("/dashboard");
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("preserves the attempted path in redirect state so login can redirect back", () => {
    let capturedLocation;
    useAuth.mockReturnValue({ user: null, loading: false });

    // Override login page to inspect the location state
    render(
      <MemoryRouter initialEntries={["/profile"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/profile" element={<div>Profile</div>} />
          </Route>
          <Route
            path="/login"
            element={
              <CaptureLocation onCapture={(loc) => { capturedLocation = loc; }} />
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(capturedLocation?.state?.from?.pathname).toBe("/profile");
  });
});

function CaptureLocation({ onCapture }) {
  const { useLocation } = require("react-router-dom");
  const location = useLocation();
  React.useEffect(() => { onCapture(location); }, []);
  return <div data-testid="login-page" />;
}
