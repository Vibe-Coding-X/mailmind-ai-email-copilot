import { useId, type MouseEventHandler, type ReactNode } from "react";

export function Button({
  children,
  variant = "default",
  disabled = false,
  disabledReason,
  onClick,
  type = "button",
}: {
  children: ReactNode;
  variant?: "default" | "primary" | "ghost";
  disabled?: boolean;
  disabledReason?: string;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  type?: "button" | "submit";
}) {
  const reasonId = useId();
  const className =
    variant === "primary"
      ? "mm-btn mm-btn--primary"
      : variant === "ghost"
        ? "mm-btn mm-btn--ghost"
        : "mm-btn";

  return (
    <button
      type={type}
      className={className}
      disabled={disabled}
      aria-disabled={disabled}
      aria-describedby={disabled && disabledReason ? reasonId : undefined}
      title={disabled ? disabledReason : undefined}
      onClick={onClick}
    >
      {children}
      {disabled && disabledReason ? (
        <span id={reasonId} className="mm-sr-only">
          {disabledReason}
        </span>
      ) : null}
    </button>
  );
}
