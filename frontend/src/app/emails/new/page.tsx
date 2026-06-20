import { redirect } from "next/navigation";

/**
 * New-mail detection is represented in the digest API. Until a dedicated
 * backend endpoint is wired, route users to the real email list.
 */
export default function NewEmailsPage() {
  redirect("/emails");
}
