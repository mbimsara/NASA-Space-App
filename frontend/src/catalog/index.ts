/**
 * Validated loading path for the shared crop catalog (data/catalogs/crops.json).
 * The engine and UI must use `loadedCatalog` — never the raw JSON — so a
 * malformed catalog is reported instead of silently consumed.
 */
import rawCatalog from "../../../data/catalogs/crops.json";
import { validateCatalog } from "./validateCatalog";

export const loadedCatalog = validateCatalog(rawCatalog);

/** Catalog version sent with rotation requests. */
export const CATALOG_VERSION =
  loadedCatalog.catalog?.catalog_version ??
  (typeof (rawCatalog as { catalog_version?: unknown }).catalog_version === "string"
    ? (rawCatalog as { catalog_version: string }).catalog_version
    : "unknown");

export * from "./validateCatalog";
