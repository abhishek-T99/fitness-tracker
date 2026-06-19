/**
 * Tests for StatCard component
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import StatCard from "../../components/StatCard.jsx";

const MockIcon = () => <svg data-testid="stat-icon" />;

describe("StatCard", () => {
  it("renders the label and value", () => {
    render(<StatCard label="Total Workouts" value="42" />);
    expect(screen.getByText("Total Workouts")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders the icon when provided", () => {
    render(<StatCard icon={MockIcon} label="Workouts" value="10" />);
    expect(screen.getByTestId("stat-icon")).toBeInTheDocument();
  });

  it("does not render an icon container when icon is omitted", () => {
    const { container } = render(<StatCard label="Label" value="0" />);
    // The icon wrapper div is only rendered when Icon is truthy
    expect(container.querySelector("[data-testid='stat-icon']")).toBeNull();
  });

  it("renders the hint text when provided", () => {
    render(<StatCard label="Calories" value="2400" hint="kcal this week" />);
    expect(screen.getByText("kcal this week")).toBeInTheDocument();
  });

  it("does not render hint text when omitted", () => {
    const { container } = render(<StatCard label="Calories" value="2400" />);
    // The hint paragraph is conditionally rendered
    expect(container.querySelectorAll("p")).toHaveLength(2); // label + value only
  });

  it("applies emerald accent colour classes", () => {
    const { container } = render(
      <StatCard icon={MockIcon} label="L" value="V" accent="emerald" />
    );
    const iconWrapper = container.querySelector("[class*='emerald']");
    expect(iconWrapper).toBeInTheDocument();
  });

  it("falls back to brand accent for unrecognised accent values", () => {
    const { container } = render(
      <StatCard icon={MockIcon} label="L" value="V" accent="unknown" />
    );
    const iconWrapper = container.querySelector("[class*='brand']");
    expect(iconWrapper).toBeInTheDocument();
  });
});
