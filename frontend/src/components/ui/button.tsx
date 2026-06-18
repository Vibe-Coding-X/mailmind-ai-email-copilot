import type { ReactNode } from "react";

/**
 * Button — STATIC, non-functional button (design preview).
 *
 * Intentionally has no onClick handler and defaults to disabled. This round
 * forbids real submit/auth/fetch behavior, so buttons must not do anything.
 */
export function Button({
  children,
  variant = "default",
  disabled = true,
  type = "button",
}: {
  children: ReactNode;
  variant?: "default" | "primary";
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      className={variant === "primary" ? "mm-btn mm-btn--primary" : "mm-btn"}
      disabled={disabled}
      aria-disabled={disabled}
    >
      {children}
    </button>
  );
}
