import { Skeleton } from "@/components/ui/skeleton";

export function EmailLoadingState({
  title = "Loading emails",
}: {
  title?: string;
}) {
  return (
    <section className="mm-card">
      <div className="mm-card-title">{title}</div>
      <Skeleton lines={5} widths={["50%", "90%", "74%", "84%", "42%"]} />
    </section>
  );
}
