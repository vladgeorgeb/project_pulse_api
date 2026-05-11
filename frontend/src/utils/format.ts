export function centsToUsd(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export function usdToCents(value: string): number {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue) || numericValue < 0) return 0;
  return Math.round(numericValue * 100);
}

export function minutesToHours(minutes: number): number {
  return Math.round((minutes / 60) * 10) / 10;
}

export function formatDate(value: string | null): string {
  if (!value) return "No date";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

export function classNames(...items: Array<string | false | null | undefined>): string {
  return items.filter(Boolean).join(" ");
}
