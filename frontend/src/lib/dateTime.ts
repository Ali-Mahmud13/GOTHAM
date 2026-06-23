const PAKISTAN_TIME_ZONE = "Asia/Karachi";

const hasTimezoneSuffix = (value: string) => /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);

const parseApiTimestamp = (value?: string | null): Date | null => {
  if (!value) return null;

  const trimmed = value.trim();
  if (!trimmed) return null;

  const normalized = /^\d{4}-\d{2}-\d{2}$/.test(trimmed)
    ? `${trimmed}T00:00:00Z`
    : hasTimezoneSuffix(trimmed) ? trimmed : `${trimmed}Z`;
  const date = new Date(normalized);

  return Number.isNaN(date.getTime()) ? null : date;
};

export const formatPakistanDateTime = (
  value?: string | null,
  fallback = "",
): string => {
  const date = parseApiTimestamp(value);
  if (!date) return fallback;

  return new Intl.DateTimeFormat("en-US", {
    timeZone: PAKISTAN_TIME_ZONE,
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  }).format(date);
};

export const formatPakistanDate = (
  value?: string | null,
  fallback = "",
): string => {
  const date = parseApiTimestamp(value);
  if (!date) return fallback;

  return new Intl.DateTimeFormat("en-US", {
    timeZone: PAKISTAN_TIME_ZONE,
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
};
