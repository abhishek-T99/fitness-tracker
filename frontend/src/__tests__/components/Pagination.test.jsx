/**
 * Tests for Pagination component
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Pagination from "../../components/Pagination.jsx";

function setup(props) {
  const onChange = jest.fn();
  const utils = render(<Pagination onChange={onChange} {...props} />);
  return { ...utils, onChange };
}

describe("Pagination — hidden when unnecessary", () => {
  it("renders nothing when totalCount equals pageSize", () => {
    const { container } = setup({ page: 1, pageSize: 10, totalCount: 10 });
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when totalCount is less than pageSize", () => {
    const { container } = setup({ page: 1, pageSize: 10, totalCount: 5 });
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when totalCount is undefined", () => {
    const { container } = setup({ page: 1, pageSize: 10, totalCount: undefined });
    expect(container).toBeEmptyDOMElement();
  });
});

describe("Pagination — item range label", () => {
  it("shows correct from–to–total for the first page", () => {
    setup({ page: 1, pageSize: 10, totalCount: 35 });
    expect(screen.getByText(/1–10/)).toBeInTheDocument();
    expect(screen.getByText(/35/)).toBeInTheDocument();
  });

  it("shows correct range for a middle page", () => {
    setup({ page: 2, pageSize: 10, totalCount: 35 });
    expect(screen.getByText(/11–20/)).toBeInTheDocument();
  });

  it("caps the 'to' value at totalCount on the last page", () => {
    setup({ page: 4, pageSize: 10, totalCount: 35 });
    expect(screen.getByText(/31–35/)).toBeInTheDocument();
  });
});

describe("Pagination — page button interactions", () => {
  it("calls onChange with the target page number when a page button is clicked", async () => {
    const user = userEvent.setup();
    const { onChange } = setup({ page: 1, pageSize: 10, totalCount: 50 });

    await user.click(screen.getByRole("button", { name: "3" }));
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it("marks the current page button with aria-current='page'", () => {
    setup({ page: 2, pageSize: 10, totalCount: 50 });
    const currentBtn = screen.getByRole("button", { name: "2" });
    expect(currentBtn).toHaveAttribute("aria-current", "page");
  });

  it("disables the Previous button on the first page", () => {
    setup({ page: 1, pageSize: 10, totalCount: 30 });
    // The prev chevron is always the first button in document order
    const buttons = screen.getAllByRole("button");
    expect(buttons[0]).toBeDisabled();
  });

  it("disables the Next button on the last page", () => {
    setup({ page: 3, pageSize: 10, totalCount: 30 });
    // The next chevron is always the last button in document order
    const buttons = screen.getAllByRole("button");
    expect(buttons[buttons.length - 1]).toBeDisabled();
  });

  it("does not fire onChange when a disabled Prev button is clicked", async () => {
    const user = userEvent.setup();
    const { onChange } = setup({ page: 1, pageSize: 10, totalCount: 30 });

    const prevBtn = screen.getAllByRole("button")[0];
    await user.click(prevBtn);
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe("Pagination — ellipsis for large page counts", () => {
  it("shows ellipsis when there are many pages", () => {
    setup({ page: 1, pageSize: 10, totalCount: 200 });
    expect(screen.getAllByText("…").length).toBeGreaterThan(0);
  });

  it("always renders the first and last page buttons", () => {
    setup({ page: 5, pageSize: 10, totalCount: 200 });
    expect(screen.getByRole("button", { name: "1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "20" })).toBeInTheDocument();
  });
});
