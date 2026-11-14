/**
 * Light/dark theme from Tharuka's design: follows the device preference until the
 * user chooses, then remembers it (same storage key as the design prototype).
 * Owner: Shehani.
 */
import { useSyncExternalStore } from "react";

export type Theme = "light" | "dark";
const KEY = "agrosphere-theme";
const listeners = new Set<() => void>();

function systemTheme(): Theme {
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  } catch {
    return "light";
  }
}

function readSaved(): Theme | null {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

let current: Theme = typeof window === "undefined" ? "light" : readSaved() ?? systemTheme();

function apply(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

if (typeof window !== "undefined") {
  apply(current);
  try {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (readSaved() === null) setTheme(systemTheme(), false);
    });
  } catch {
    /* older browsers: keep the initial theme */
  }
}

export function setTheme(theme: Theme, remember = true) {
  current = theme;
  apply(theme);
  if (remember) {
    try {
      localStorage.setItem(KEY, theme);
    } catch {
      /* storage unavailable: theme still applies for this visit */
    }
  }
  listeners.forEach((l) => l());
}

export function useTheme(): [Theme, () => void] {
  const theme = useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => current,
    () => "light" as Theme,
  );
  return [theme, () => setTheme(theme === "light" ? "dark" : "light")];
}

/** Resolved CSS custom property for SVG attributes (charts), which cannot use var(). */
export function cssVar(name: string, fallback: string): string {
  try {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  } catch {
    return fallback;
  }
}
