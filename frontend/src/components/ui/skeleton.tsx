/**
 * Skeleton — placeholder shimmer lines (design preview).
 *
 * Used to suggest where future content will appear WITHOUT showing any real or
 * mock data. Renders neutral gray bars only — never fake email subjects,
 * senders, summaries, or AI output.
 */
export function Skeleton({
  lines = 3,
  widths,
}: {
  lines?: number;
  widths?: string[];
}) {
  return (
    <div>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="mm-skel"
          style={{ width: widths?.[i] ?? (i === lines - 1 ? "60%" : "100%") }}
        />
      ))}
    </div>
  );
}
