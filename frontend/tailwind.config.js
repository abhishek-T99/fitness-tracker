/** @type {import('tailwindcss').Config} */

// Theme system: `slate`, `brand`, and `surface` resolve to CSS variables
// declared in index.css (`:root` = light values, `.dark` = dark values), so
// every existing `text-slate-500` / `bg-brand-600` class is theme-aware
// without per-callsite `dark:` edits. `ink` is a STATIC copy of Tailwind's
// slate palette for surfaces that must stay dark in both themes (sidebar,
// auth-page gradients).
const v = (name) => `rgb(var(--c-${name}) / <alpha-value>)`;

const scale = (prefix) =>
  Object.fromEntries(
    [50, 100, 200, 300, 400, 500, 600, 700, 800, 900].map((n) => [
      n,
      v(`${prefix}-${n}`),
    ])
  );

export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        slate: scale("slate"),
        brand: scale("brand"),
        surface: v("surface"),
        ink: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      keyframes: {
        "slide-up": {
          from: { transform: "translateY(100%)" },
          to:   { transform: "translateY(0)" },
        },
      },
      animation: {
        "slide-up": "slide-up 0.28s cubic-bezier(0.32, 0.72, 0, 1)",
      },
    },
  },
  plugins: [],
};
