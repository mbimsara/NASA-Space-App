/**
 * ErrorMessage — reusable error display with retry support.
 * Shows field-level errors from ApiClientError.fields.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import { ApiClientError } from "../../api/client";

interface Props {
  error: unknown;
  onRetry?: () => void;
}

export function ErrorMessage({ error, onRetry }: Props) {
  const { t } = useTranslation();
  if (error === null || error === undefined) return null;

  let message = t("common.error");
  let fields: Record<string, string> | undefined;

  if (error instanceof ApiClientError) {
    message = t(`errors.${error.code}`, { defaultValue: error.message });
    fields = error.fields;
  } else if (error instanceof DOMException && error.name === "AbortError") {
    return null; // Cancelled requests are not user-visible errors
  } else if (error instanceof Error) {
    message = error.message;
  }

  return (
    <div
      role="alert"
      style={{
        background: "#f8d7da",
        border: "1px solid #f5c2c7",
        borderRadius: 6,
        padding: "12px 16px",
        color: "#842029",
        marginBottom: 12,
      }}
    >
      <strong>{message}</strong>
      {fields && (
        <ul style={{ marginTop: 6, fontSize: 13 }}>
          {Object.entries(fields).map(([field, msg]) => (
            <li key={field}><strong>{field}:</strong> {msg}</li>
          ))}
        </ul>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{ marginTop: 8, padding: "4px 12px", cursor: "pointer" }}
        >
          {t("common.retry")}
        </button>
      )}
    </div>
  );
}

