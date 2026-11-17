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
