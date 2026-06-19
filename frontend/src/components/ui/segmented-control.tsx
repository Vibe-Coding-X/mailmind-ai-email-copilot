"use client";

import type { ReactNode } from "react";

/**
 * SegmentedControl — a small group of mutually-exclusive options rendered as a
 * pill of buttons. Presentational + controlled: the parent owns the value.
 *
 * Accessible: each option is a real <button> with aria-pressed; the group has
 * an accessible label. Keyboard focus is visible via the global :focus-visible
 * style. No data fetching.
 */

export interface SegmentedOption<T extends string> {
  value: T;
  label: ReactNode;
  title?: string;
}

export function SegmentedControl<T extends string>({
  label,
  value,
  options,
  onChange,
  block = false,
}: {
  label: string;
  value: T;
  options: SegmentedOption<T>[];
  onChange: (value: T) => void;
  block?: boolean;
}) {
  return (
    <div
      className={block ? "mm-seg mm-seg--block" : "mm-seg"}
      role="group"
      aria-label={label}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            className="mm-seg-btn"
            aria-pressed={active}
            title={opt.title}
            onClick={() => {
              if (!active) {
                onChange(opt.value);
              }
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
