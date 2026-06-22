import { redirect } from "next/navigation";

/**
 * MailMind is dashboard-first; the root route opens the real dashboard instead
 * of rendering a separate static preview.
 */
export default function HomePage() {
  redirect("/dashboard");
}
