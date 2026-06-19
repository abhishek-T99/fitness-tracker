/**
 * Tests for EmptyState component
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import EmptyState from "../../components/EmptyState.jsx";

const MockIcon = () => <svg data-testid="empty-icon" />;

describe("EmptyState", () => {
  it("renders the title", () => {
    render(<EmptyState title="No workouts yet" />);
    expect(screen.getByText("No workouts yet")).toBeInTheDocument();
  });

  it("renders the description when provided", () => {
    render(<EmptyState title="Title" description="Start by logging a workout." />);
    expect(screen.getByText("Start by logging a workout.")).toBeInTheDocument();
  });

  it("does not render a description element when description is omitted", () => {
    const { queryByText } = render(<EmptyState title="Title" />);
    // No second paragraph should exist beyond the title
    expect(queryByText(/start by/i)).not.toBeInTheDocument();
  });

  it("renders the action slot when provided", () => {
    render(
      <EmptyState
        title="Title"
        action={<button>Add workout</button>}
      />
    );
    expect(screen.getByRole("button", { name: "Add workout" })).toBeInTheDocument();
  });

  it("renders the icon when provided", () => {
    render(<EmptyState icon={MockIcon} title="Title" />);
    expect(screen.getByTestId("empty-icon")).toBeInTheDocument();
  });

  it("marks the icon container as aria-hidden so screen readers skip the decorative graphic", () => {
    const { container } = render(<EmptyState icon={MockIcon} title="Title" />);
    const iconWrapper = container.querySelector("[aria-hidden='true']");
    expect(iconWrapper).toBeInTheDocument();
  });

  it("does not render an icon container when icon is omitted", () => {
    render(<EmptyState title="Title" />);
    expect(screen.queryByTestId("empty-icon")).not.toBeInTheDocument();
  });
});
