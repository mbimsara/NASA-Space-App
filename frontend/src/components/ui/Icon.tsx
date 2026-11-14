/**
 * Minimal inline icon set (stroke style matching the design prototype).
 * Decorative by default (aria-hidden); pair with visible text.
 */
const PATHS: Record<string, string> = {
  home: "M3 11 12 4l9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  farm: "M4 20V9l8-5 8 5v11M9 20v-6h6v6",
  overview: "M4 19V5M4 19h16M8 15l3-4 3 2 4-6",
  rotate: "M4 12a8 8 0 0 1 13.7-5.7L20 8M20 4v4h-4M20 12a8 8 0 0 1-13.7 5.7L4 16M4 20v-4h4",
  climate: "M7 18a4 4 0 0 1-.5-8 6 6 0 0 1 11.6 1.5A3.5 3.5 0 0 1 17.5 18zM9 21l1-2M13 21l1-2",
  chat: "M4 5h16v11H9l-5 4z",
  save: "M5 4h11l3 3v13H5zM8 4v5h7V4M8 20v-6h8v6",
  coin: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM14.5 9.5c-.5-1-1.5-1.5-2.5-1.5-1.4 0-2.5.8-2.5 2s1.1 1.6 2.5 2 2.5.8 2.5 2-1.1 2-2.5 2c-1 0-2-.5-2.5-1.5M12 6.5v11",
  book: "M5 4h9a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h9",
  map: "M9 4 3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14",
  edit: "M4 20h4L19 9l-4-4L4 16zM14 6l4 4",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6 6 18",
  sun: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
  moon: "M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z",
  leaf: "M5 19c0-8 5-14 15-15-1 10-7 15-15 15zM5 19l7-7",
  arrow: "M5 12h14M13 6l6 6-6 6",
  check: "M5 12.5 10 17l9-10",
};

export function Icon({ name, label }: { name: keyof typeof PATHS | string; label?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : true}
      role={label ? "img" : undefined}
      aria-label={label}
      focusable="false"
    >
      <path d={PATHS[name] ?? PATHS.leaf} />
    </svg>
  );
}
