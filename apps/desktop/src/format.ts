const GB = 1024 ** 3;

export function gb(bytes: number | null | undefined, digits = 1): string {
  if (bytes == null) return "—";
  return `${(bytes / GB).toLocaleString("pt-BR", { maximumFractionDigits: digits, minimumFractionDigits: digits })} GB`;
}

export function percent(part: number, total: number): number {
  return total > 0 ? Math.min(100, Math.max(0, (part / total) * 100)) : 0;
}

export function when(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

/** File size with a unit that fits: KB, MB or GB. */
export function size(bytes: number | null | undefined): string {
  if (bytes == null) return "—";
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit++;
  }
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: value < 10 ? 1 : 0 })} ${units[unit]}`;
}
