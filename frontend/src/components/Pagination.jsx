import { ChevronLeft, ChevronRight } from "lucide-react";

/**
 * Reusable page-number pagination bar.
 *
 * Props
 * ─────
 * page        number   current 1-based page
 * pageSize    number   items per page
 * totalCount  number   total items from API (data.count)
 * onChange    fn       called with the new page number
 * className   string   optional extra wrapper classes
 */
export default function Pagination({ page, pageSize, totalCount, onChange, className = "" }) {
  if (!totalCount || totalCount <= pageSize) return null;

  const totalPages = Math.ceil(totalCount / pageSize);
  const from = (page - 1) * pageSize + 1;
  const to   = Math.min(page * pageSize, totalCount);

  // Build the page number array with ellipsis ("…" represented as null).
  // Always show first, last, current ±1. Fill with nulls where gaps exist.
  function buildPages() {
    const delta = 2; // pages around current to always show
    const pages = [];
    const left  = page - delta;
    const right = page + delta;

    for (let p = 1; p <= totalPages; p++) {
      if (p === 1 || p === totalPages || (p >= left && p <= right)) {
        pages.push(p);
      } else if (pages[pages.length - 1] !== null) {
        pages.push(null); // ellipsis
      }
    }
    return pages;
  }

  const pages = buildPages();

  function btn(label, target, disabled, isActive = false) {
    return (
      <button
        key={label}
        onClick={() => !disabled && onChange(target)}
        disabled={disabled}
        aria-label={typeof label === "string" ? label : undefined}
        aria-current={isActive ? "page" : undefined}
        className={[
          "flex h-9 min-w-[2.25rem] items-center justify-center rounded-lg px-2 text-sm font-medium transition",
          isActive
            ? "bg-brand-600 text-white shadow-sm"
            : disabled
            ? "cursor-not-allowed text-slate-300 dark:text-slate-600"
            : "text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-100/10",
        ].join(" ")}
      >
        {label}
      </button>
    );
  }

  return (
    <div className={`flex flex-col items-center gap-3 sm:flex-row sm:justify-between mt-6 ${className}`}>
      {/* Count label */}
      <p className="text-sm text-slate-500 order-2 sm:order-1">
        Showing <span className="font-medium text-slate-700">{from}–{to}</span> of{" "}
        <span className="font-medium text-slate-700">{totalCount}</span>
      </p>

      {/* Page buttons */}
      <div className="flex items-center gap-1 order-1 sm:order-2">
        {btn(<ChevronLeft className="w-4 h-4" />, page - 1, page === 1, false)}

        {pages.map((p, i) =>
          p === null
            ? <span key={`ellipsis-${i}`} className="px-1 text-slate-400 select-none">…</span>
            : btn(p, p, false, p === page)
        )}

        {btn(<ChevronRight className="w-4 h-4" />, page + 1, page === totalPages, false)}
      </div>
    </div>
  );
}
