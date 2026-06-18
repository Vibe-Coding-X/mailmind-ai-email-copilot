/**
 * Field — STATIC labeled input (design preview).
 *
 * Renders a label + input for visual layout only. The input is read-only with
 * no state binding, no onChange, and no form submission. This round forbids
 * implementing login/register logic or storing any values.
 */
export function Field({
  label,
  type = "text",
  placeholder,
  autoComplete,
}: {
  label: string;
  type?: "text" | "email" | "password";
  placeholder?: string;
  autoComplete?: string;
}) {
  return (
    <div className="mm-field">
      <label className="mm-label">{label}</label>
      <input
        className="mm-input"
        type={type}
        placeholder={placeholder}
        autoComplete={autoComplete}
        readOnly
        disabled
      />
    </div>
  );
}
