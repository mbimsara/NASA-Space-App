/**
 * Crop catalog loading + validation.
 * Owner: Shehani (implementation). Bhagya owns the scientific meaning of entries.
 *
 * Mirrors data/schemas/crop-catalog.schema.json v0.1 and the cross-record rules in
 * scripts/validate_data.py so malformed catalogs are surfaced in the UI *before*
 * any engine or screen consumes them. Keep the three in sync when the schema changes.
 */

export interface CropSource {
  url: string;
  accessed_on: string;
  notes: string;
}

export interface CatalogCrop {
  id: string;
  name: string;
  family: string | null;
  season_labels: string[];
  water_demand_mm_per_cycle: number | null;
  sources: CropSource[];
  review_status: "draft" | "approved";
}

export interface CropCatalog {
  schema_version: "0.1";
  catalog_version: string;
  status: "research_pending" | "reviewed";
  region: string;
  crops: CatalogCrop[];
}

export interface CatalogIssue {
  path: string;
  message: string;
}

export interface CatalogValidationResult {
  ok: boolean;
  issues: CatalogIssue[];
  /** Non-blocking notes, e.g. empty catalog or draft entries. */
  notes: string[];
  /** Present only when `ok` is true. */
  catalog: CropCatalog | null;
  /** Crops safe for recommendation use: approved entries of a valid catalog. */
  approvedCrops: CatalogCrop[];
}

const TOP_KEYS = ["schema_version", "catalog_version", "status", "region", "crops"] as const;
const CROP_KEYS = [
  "id",
  "name",
  "family",
  "season_labels",
  "water_demand_mm_per_cycle",
  "sources",
  "review_status",
] as const;
const SOURCE_KEYS = ["url", "accessed_on", "notes"] as const;

const isObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const isNonEmptyString = (v: unknown): v is string => typeof v === "string" && v.trim().length > 0;
const isFiniteNumber = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

function isIsoDate(v: unknown): v is string {
  if (typeof v !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
  const d = new Date(`${v}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === v;
}

function isHttpUrl(v: unknown): v is string {
  if (typeof v !== "string") return false;
  try {
    const u = new URL(v);
    return (u.protocol === "http:" || u.protocol === "https:") && u.host.length > 0;
  } catch {
    return false;
  }
}

function checkKeys(
  obj: Record<string, unknown>,
  allowed: readonly string[],
  path: string,
  issues: CatalogIssue[],
) {
  for (const k of allowed) {
    if (!(k in obj)) issues.push({ path: `${path}.${k}`, message: "Missing required field" });
  }
  for (const k of Object.keys(obj)) {
    if (!allowed.includes(k)) issues.push({ path: `${path}.${k}`, message: "Unexpected field" });
  }
}

export function validateCatalog(input: unknown): CatalogValidationResult {
  const issues: CatalogIssue[] = [];
  const notes: string[] = [];
  const fail = (): CatalogValidationResult => ({ ok: false, issues, notes, catalog: null, approvedCrops: [] });

  if (!isObject(input)) {
    issues.push({ path: "$", message: "Catalog must be a JSON object" });
    return fail();
  }
  checkKeys(input, TOP_KEYS, "$", issues);

  if (input.schema_version !== "0.1") issues.push({ path: "$.schema_version", message: 'Must be "0.1"' });
  if (!isNonEmptyString(input.catalog_version)) issues.push({ path: "$.catalog_version", message: "Must be a non-empty string" });
  if (input.status !== "research_pending" && input.status !== "reviewed") {
    issues.push({ path: "$.status", message: 'Must be "research_pending" or "reviewed"' });
  }
  if (!isNonEmptyString(input.region)) issues.push({ path: "$.region", message: "Must be a non-empty string" });
  if (!Array.isArray(input.crops)) {
    issues.push({ path: "$.crops", message: "Must be an array" });
    return fail();
  }

  const seenIds = new Map<string, number>();
  input.crops.forEach((crop, i) => {
    const p = `$.crops[${i}]`;
    if (!isObject(crop)) {
      issues.push({ path: p, message: "Crop entry must be an object" });
      return;
    }
    checkKeys(crop, CROP_KEYS, p, issues);

    if (!isNonEmptyString(crop.id)) {
      issues.push({ path: `${p}.id`, message: "Missing or empty crop identifier" });
    } else if (seenIds.has(crop.id)) {
      issues.push({ path: `${p}.id`, message: `Duplicate crop ID "${crop.id}" (also at crops[${seenIds.get(crop.id)}])` });
    } else {
      seenIds.set(crop.id, i);
    }
    if (!isNonEmptyString(crop.name)) issues.push({ path: `${p}.name`, message: "Must be a non-empty string" });
    if (crop.family !== null && !isNonEmptyString(crop.family)) {
      issues.push({ path: `${p}.family`, message: "Must be a non-empty string or null (unknown)" });
    }

    if (!Array.isArray(crop.season_labels)) {
      issues.push({ path: `${p}.season_labels`, message: "Must be an array of strings" });
    } else {
      crop.season_labels.forEach((s, j) => {
        if (!isNonEmptyString(s)) issues.push({ path: `${p}.season_labels[${j}]`, message: "Must be a non-empty string" });
      });
      if (new Set(crop.season_labels).size !== crop.season_labels.length) {
        issues.push({ path: `${p}.season_labels`, message: "Duplicate season labels" });
      }
    }

    const w = crop.water_demand_mm_per_cycle;
    if (w !== null && !(isFiniteNumber(w) && w > 0)) {
      issues.push({
        path: `${p}.water_demand_mm_per_cycle`,
        message: "Invalid unit/value: must be a positive number of millimetres per cycle, or null when unknown",
      });
    }

    if (!Array.isArray(crop.sources)) {
      issues.push({ path: `${p}.sources`, message: "Must be an array" });
    } else {
      crop.sources.forEach((src, j) => {
        const sp = `${p}.sources[${j}]`;
        if (!isObject(src)) {
          issues.push({ path: sp, message: "Source must be an object" });
          return;
        }
        checkKeys(src, SOURCE_KEYS, sp, issues);
        if (!isHttpUrl(src.url)) issues.push({ path: `${sp}.url`, message: "Invalid source URL (http/https required)" });
        if (!isIsoDate(src.accessed_on)) issues.push({ path: `${sp}.accessed_on`, message: "Use YYYY-MM-DD" });
        if (!isNonEmptyString(src.notes)) issues.push({ path: `${sp}.notes`, message: "Must be a non-empty string" });
      });
    }

    if (crop.review_status !== "draft" && crop.review_status !== "approved") {
      issues.push({ path: `${p}.review_status`, message: 'Must be "draft" or "approved"' });
    } else if (crop.review_status === "approved") {
      if (!Array.isArray(crop.sources) || crop.sources.length === 0) {
        issues.push({ path: `${p}.sources`, message: "Approved crops need at least one source" });
      }
      if (!Array.isArray(crop.season_labels) || crop.season_labels.length === 0) {
        issues.push({ path: `${p}.season_labels`, message: "Approved crops need at least one season" });
      }
      if (crop.family === null) issues.push({ path: `${p}.family`, message: "Approved crops need a reviewed family" });
    }
  });

  if (input.status === "reviewed") {
    const crops = input.crops as unknown[];
    const allApproved = crops.length > 0 && crops.every((c) => isObject(c) && c.review_status === "approved");
    if (!allApproved) issues.push({ path: "$.status", message: "A reviewed catalog needs at least one crop and all crops approved" });
  }

  if (issues.length > 0) return fail();

  const catalog = input as unknown as CropCatalog;
  if (catalog.crops.length === 0) {
    notes.push("Catalog is empty; research and approval are required before recommendations.");
  }
  const drafts = catalog.crops.filter((c) => c.review_status === "draft").length;
  if (drafts > 0) notes.push(`${drafts} crop(s) are drafts and will not be used for recommendations.`);
  const unknownWater = catalog.crops.filter((c) => c.water_demand_mm_per_cycle === null).length;
  if (unknownWater > 0) notes.push(`${unknownWater} crop(s) have unknown water demand (null, not zero).`);

  return {
    ok: true,
    issues,
    notes,
    catalog,
    approvedCrops: catalog.crops.filter((c) => c.review_status === "approved"),
  };
}
