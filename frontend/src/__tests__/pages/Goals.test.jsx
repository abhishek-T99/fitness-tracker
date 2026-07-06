jest.mock("../../api/endpoints.js", () => ({
  goalsApi: {
    list: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
    reorder: jest.fn(),
  },
}));

jest.mock("../../components/SortableList.jsx", () => {
  const React = require("react");
  function SortableList({ children }) {
    return <div data-testid="sortable-list">{children}</div>;
  }
  function SortableItem({ children }) {
    return <div>{children({})}</div>;
  }
  function DragHandle() {
    return null;
  }
  return { __esModule: true, default: SortableList, SortableItem, DragHandle };
});

jest.mock("react-hot-toast", () => ({ success: jest.fn(), error: jest.fn() }));

import React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import Goals from "../../pages/Goals.jsx";
import { goalsApi } from "../../api/endpoints.js";

function makeGoal(overrides = {}) {
  return {
    id: 1,
    title: "Run a 5K",
    goal_type: "endurance",
    status: "active",
    current_value: 3,
    target_value: 5,
    unit: "km",
    progress_percent: 60,
    deadline: null,
    created_at: "2026-06-01T10:00:00Z",
    ...overrides,
  };
}

function renderGoals() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Goals />
    </QueryClientProvider>
  );
}

describe("Goals page — created_at display", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows 'Created X ago' when created_at is present", async () => {
    goalsApi.list.mockResolvedValue([makeGoal({ created_at: "2026-06-01T10:00:00Z" })]);

    renderGoals();

    const el = await screen.findByTestId("goal-created-at");
    expect(el).toBeInTheDocument();
    expect(el.textContent).toMatch(/Created .+ ago/);
  });

  it("does not render the created-at element when created_at is absent", async () => {
    goalsApi.list.mockResolvedValue([makeGoal({ created_at: null })]);

    renderGoals();

    await screen.findByText("Run a 5K");
    expect(screen.queryByTestId("goal-created-at")).not.toBeInTheDocument();
  });

  it("renders one created-at element per goal card", async () => {
    goalsApi.list.mockResolvedValue([
      makeGoal({ id: 1, title: "Goal A", created_at: "2026-05-01T00:00:00Z" }),
      makeGoal({ id: 2, title: "Goal B", created_at: "2026-04-15T00:00:00Z" }),
    ]);

    renderGoals();

    const els = await screen.findAllByTestId("goal-created-at");
    expect(els).toHaveLength(2);
  });

  it("renders the goal title alongside the created-at text", async () => {
    goalsApi.list.mockResolvedValue([makeGoal({ title: "Bench 100kg" })]);

    renderGoals();

    await screen.findByText("Bench 100kg");
    expect(screen.getByTestId("goal-created-at")).toBeInTheDocument();
  });
});
