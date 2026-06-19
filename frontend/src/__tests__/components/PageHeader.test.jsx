/**
 * Tests for PageHeader component
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import PageHeader from "../../components/PageHeader.jsx";

describe("PageHeader", () => {
  it("renders the title as an h1", () => {
    render(<PageHeader title="Workouts" />);
    expect(screen.getByRole("heading", { level: 1, name: "Workouts" })).toBeInTheDocument();
  });

  it("renders the subtitle when provided", () => {
    render(<PageHeader title="Goals" subtitle="Track your progress" />);
    expect(screen.getByText("Track your progress")).toBeInTheDocument();
  });

  it("does not render a subtitle element when subtitle is omitted", () => {
    render(<PageHeader title="Goals" />);
    // Only the h1 should be in the header div
    expect(screen.queryByText(/track your/i)).not.toBeInTheDocument();
  });

  it("renders actions in the actions slot", () => {
    render(
      <PageHeader
        title="Routines"
        actions={<button>New routine</button>}
      />
    );
    expect(screen.getByRole("button", { name: "New routine" })).toBeInTheDocument();
  });

  it("does not render an actions container when actions are omitted", () => {
    const { container } = render(<PageHeader title="Title" />);
    // There should be no extra wrapper div for actions
    const flexContainers = container.querySelectorAll("div");
    // Outer wrapper + title wrapper = 2 divs; no third actions div
    expect(flexContainers).toHaveLength(2);
  });
});
