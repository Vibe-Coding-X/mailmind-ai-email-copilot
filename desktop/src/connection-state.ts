export type ConnectionTransition = "none" | "lost" | "recovered";

export function getConnectionTransition(
  previous: boolean | null,
  next: boolean,
): ConnectionTransition {
  if (previous === null) {
    return "none";
  }

  if (previous && !next) {
    return "lost";
  }

  if (!previous && next) {
    return "recovered";
  }

  return "none";
}
