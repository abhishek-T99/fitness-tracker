/**
 * Tests for LevelBadge component
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import LevelBadge from "../../components/LevelBadge.jsx";

describe("LevelBadge — tier labels", () => {
  const tiers = [
    ["rookie",   "Rookie"],
    ["amateur",  "Amateur"],
    ["athlete",  "Athlete"],
    ["warrior",  "Warrior"],
    ["legend",   "Legend"],
    ["elite",    "Elite"],
    ["immortal", "Immortal"],
  ];

  it.each(tiers)("renders the correct label for tier '%s'", (tier, label) => {
    render(<LevelBadge tier={tier} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("falls back to 'Rookie' for an unrecognised tier", () => {
    render(<LevelBadge tier="unknown_tier" />);
    expect(screen.getByText("Rookie")).toBeInTheDocument();
  });
});

describe("LevelBadge — level number", () => {
  it("renders the level number when provided", () => {
    render(<LevelBadge tier="elite" level={25} />);
    expect(screen.getByText("Lv.25")).toBeInTheDocument();
  });

  it("does not render a level prefix when level is null", () => {
    render(<LevelBadge tier="warrior" level={null} />);
    expect(screen.queryByText(/Lv\./)).not.toBeInTheDocument();
  });

  it("does not render a level prefix when level is undefined", () => {
    render(<LevelBadge tier="warrior" />);
    expect(screen.queryByText(/Lv\./)).not.toBeInTheDocument();
  });
});

describe("LevelBadge — size variants", () => {
  it("applies small size classes by default", () => {
    const { container } = render(<LevelBadge tier="rookie" level={1} />);
    const badge = container.querySelector("span");
    expect(badge.className).toMatch(/text-xs/);
  });

  it("applies large size classes when size='lg'", () => {
    const { container } = render(<LevelBadge tier="rookie" level={1} size="lg" />);
    const badge = container.querySelector("span");
    expect(badge.className).toMatch(/text-sm/);
  });
});
