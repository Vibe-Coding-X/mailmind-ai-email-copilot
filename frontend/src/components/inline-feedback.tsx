import type { ReactNode } from "react";

import { Badge, type BadgeTone } from "@/components/ui/badge";

export type InlineFeedbackTone = "info" | "success" | "warning" | "danger";

const TONE_TO_BADGE: Record<InlineFeedbackTone, BadgeTone> = {
  info: "info",
  success: "ok",
  warning: "warn",
  danger: "danger",
};

export function InlineFeedback({
  tone,
  title,
  children,
  action,
}: {
  tone: InlineFeedbackTone;
  title?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className={`mm-feedback mm-feedback--${tone}`} role="status">
      <div className="mm-feedback-main">
        <Badge tone={TONE_TO_BADGE[tone]} dot>
          {title ?? tone}
        </Badge>
        <span>{children}</span>
      </div>
      {action ? <div className="mm-feedback-action">{action}</div> : null}
    </div>
  );
}
