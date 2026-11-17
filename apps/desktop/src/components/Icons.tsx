// Inline stroke icons (no icon font, no CDN).
interface IconProps {
  size?: number;
  color?: string;
}

const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
});

export function ArcaMark({ size = 20, color = "currentColor" }: IconProps) {
  return (
    <svg {...base(size)} stroke={color}>
      <path d="M3 11h18l-2.5 7h-13z" />
      <path d="M7 11V6h10v5" />
      <path d="M12 6V3" />
    </svg>
  );
}

export function DiskIcon({ size = 22, color = "currentColor" }: IconProps) {
  return (
    <svg {...base(size)} stroke={color}>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <path d="M7 14h.01M11 14h6" />
    </svg>
  );
}

export function PlusIcon({ size = 18, color = "currentColor" }: IconProps) {
  return (
    <svg {...base(size)} stroke={color}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function RefreshIcon({ size = 18, color = "currentColor" }: IconProps) {
  return (
    <svg {...base(size)} stroke={color}>
      <path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5" />
    </svg>
  );
}
