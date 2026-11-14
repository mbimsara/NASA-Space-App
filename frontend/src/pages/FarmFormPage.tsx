/**
 * FarmFormPage — farm setup / edit: map, area + unit, irrigation, crop history,
 * soil tests, priorities and crop exclusions, with validation and draft recovery.
 * Owner: Shehani.
 *
 * - New farm: /farms/new. Edit: /farms/:farmId/edit (farm loaded by FarmLayout).
 * - Unknown irrigation stays null; unknown soil values are omitted, never 0.
 * - Drafts are saved only after the user edits, per farm ("new" or farm ID).
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { farmFormSchema, fieldErrors, todayIso, type FarmFormValues } from "../utils/validation";
import { clearDraft, loadDraft, saveDraft } from "../utils/draft";
import { api } from "../api";
import { isAbortError } from "../api/requestGuard";
import { useAppStore } from "../hooks/useAppStore";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { MapPicker } from "../components/map/MapPicker";
import { HECTARES_PER, type AreaUnit } from "../finance/calculator";
import { loadedCatalog } from "../catalog";

const DEFAULT_VALUES: FarmFormValues = {
  name: "",
  location: { latitude: 8.3, longitude: 80.4 },
  area_ha: 1.0,
  irrigation_supply_mm_per_season: null,
  crop_history: [],
  soil_tests: [],
  priority_weights: { water: 0.5, soil: 0.3, climate: 0.2 },
  excluded_crop_ids: [],
};

function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return (
    <span id={id} className="field-error" role="alert">
      {message}
    </span>
  );
}

const num = (s: string) => (s.trim() === "" ? Number.NaN : Number(s));
const errId = (k: string) => `${k.replace(/\./g, "-")}-error`;

export function FarmFormPage({ mode }: { mode: "new" | "edit" }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const farm = useAppStore((s) => s.farm);
  const setFarm = useAppStore((s) => s.setFarm);
  const guard = useLatestRequest();

  const editingFarm = mode === "edit" ? farm : null;
  const draftKey = editingFarm?.id ?? "new";

  const initial = useMemo<FarmFormValues>(() => {
    if (!editingFarm) return DEFAULT_VALUES;
    const { schema_version: _v, data_kind: _k, ...rest } = editingFarm.profile;
    return rest;
  }, [editingFarm]);

  const [values, setValues] = useState<FarmFormValues>(initial);
  const [areaUnit, setAreaUnit] = useState<AreaUnit>("ha");
  const [areaInput, setAreaInput] = useState(String(initial.area_ha));
  const [exclusionsInput, setExclusionsInput] = useState(initial.excluded_crop_ids.join(", "));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState(() => {
    const d = loadDraft(draftKey);
    return d && d.values.name ? d : null;
  });
  const dirty = useRef(false);
  const errorSummaryRef = useRef<HTMLDivElement>(null);

  const update = (fn: (v: FarmFormValues) => FarmFormValues) => {
    dirty.current = true;
    setValues(fn);
  };

  useEffect(() => {
    if (dirty.current && values.name) saveDraft(draftKey, values);
  }, [values, draftKey]);

  const setArea = (text: string, unit: AreaUnit) => {
    setAreaInput(text);
    setAreaUnit(unit);
    const n = num(text);
    update((v) => ({ ...v, area_ha: Number.isFinite(n) ? n * HECTARES_PER[unit] : Number.NaN }));
  };

  const setExclusions = (text: string) => {
    setExclusionsInput(text);
    const ids = [...new Set(text.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean))];
    update((v) => ({ ...v, excluded_crop_ids: ids }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = farmFormSchema.safeParse(values);
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      requestAnimationFrame(() => errorSummaryRef.current?.focus());
      return;
    }
    setErrors({});
    setSaving(true);
    setSubmitError(null);
    const ticket = guard.next();
    try {
      const profile = { ...parsed.data, data_kind: editingFarm?.profile.data_kind ?? ("farmer_input" as const) };
      const env = editingFarm
        ? await api.updateFarm(editingFarm.id, editingFarm.input_version, profile, ticket.signal)
        : await api.createFarm(profile, ticket.signal);
      if (!ticket.isCurrent()) return;
      clearDraft(draftKey);
      dirty.current = false;
      setFarm(env);
      navigate(`/farms/${env.id}`);
    } catch (err) {
      if (!isAbortError(err)) {
        setSubmitError(err);
        requestAnimationFrame(() => errorSummaryRef.current?.focus());
      }
    } finally {
      setSaving(false);
    }
  };

  const resumeDraft = () => {
    if (draft) {
      const v = { ...initial, ...draft.values } as FarmFormValues;
      dirty.current = true;
      setValues(v);
      setAreaUnit("ha");
      setAreaInput(String(v.area_ha));
      setExclusionsInput(v.excluded_crop_ids.join(", "));
    }
    setDraft(null);
  };

  const discardDraft = () => {
    clearDraft(draftKey);
    setDraft(null);
  };

  const err = (k: string) => errors[k];
  const describedBy = (k: string) => (errors[k] ? errId(k) : undefined);
  const errorCount = Object.keys(errors).length;
  const today = todayIso();
  const catalogIds = loadedCatalog.approvedCrops.map((c) => c.id);

  return (
    <div className="page">
      <h1>{mode === "new" ? t("farm.title") : t("farm.editTitle")}</h1>

      {draft && (
        <div className="notice notice-info row" role="status" style={{ alignItems: "center" }}>
          <span style={{ flex: 1 }}>{t("farm.draftBanner", { time: new Date(draft.savedAt).toLocaleString() })}</span>
          <button type="button" className="btn" onClick={resumeDraft}>
            {t("farm.resumeDraft")}
          </button>
          <button type="button" className="btn btn-danger" onClick={discardDraft}>
            {t("farm.clearDraft")}
          </button>
        </div>
      )}

      <div ref={errorSummaryRef} tabIndex={-1} style={{ outline: "none" }}>
        {errorCount > 0 && (
          <div className="notice notice-warn" role="alert">
            <strong>{t("farm.fixErrors", { count: errorCount })}</strong>
            <ul style={{ margin: "6px 0 0" }}>
              {Object.entries(errors).map(([k, m]) => (
                <li key={k}>
                  <code>{k}</code>: {m}
                </li>
              ))}
            </ul>
          </div>
        )}
        <ErrorMessage error={submitError} />
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="card">
          <div className="field">
            <label htmlFor="farm-name">
              {t("farm.name")} <span aria-hidden="true">*</span>
            </label>
            <input
              id="farm-name"
              type="text"
              required
              value={values.name}
              onChange={(e) => update((v) => ({ ...v, name: e.target.value }))}
              placeholder={t("farm.namePlaceholder")}
              aria-invalid={!!err("name")}
              aria-describedby={describedBy("name")}
            />
            <FieldError id={errId("name")} message={err("name")} />
          </div>
        </div>

        <fieldset className="card" style={{ margin: "0 0 16px" }}>
          <legend style={{ fontWeight: 600 }}>{t("farm.location")}</legend>
          <p className="muted" style={{ marginTop: 0 }}>
            {t("farm.locationHelp")}
          </p>
          <MapPicker
            latitude={values.location.latitude}
            longitude={values.location.longitude}
            label={t("farm.mapLabel")}
            onChange={(lat, lng) => update((v) => ({ ...v, location: { latitude: lat, longitude: lng } }))}
          />
          <div className="grid-2">
            {(["latitude", "longitude"] as const).map((k) => (
              <div className="field" key={k}>
                <label htmlFor={`loc-${k}`}>{t(`farm.${k}`)} (WGS84 °)</label>
                <input
                  id={`loc-${k}`}
                  type="number"
                  step="any"
                  value={Number.isFinite(values.location[k]) ? values.location[k] : ""}
                  onChange={(e) => update((v) => ({ ...v, location: { ...v.location, [k]: num(e.target.value) } }))}
                  aria-invalid={!!err(`location.${k}`)}
                  aria-describedby={describedBy(`location.${k}`)}
                />
                <FieldError id={errId(`location.${k}`)} message={err(`location.${k}`)} />
              </div>
            ))}
          </div>
        </fieldset>

        <div className="card grid-2">
          <div className="field">
            <label htmlFor="area">
              {t("farm.area")} <span aria-hidden="true">*</span>
            </label>
            <div className="row" style={{ flexWrap: "nowrap" }}>
              <input
                id="area"
                type="number"
                min="0"
                step="any"
                value={areaInput}
                onChange={(e) => setArea(e.target.value, areaUnit)}
                aria-invalid={!!err("area_ha")}
                aria-describedby={describedBy("area_ha") ?? "area-hint"}
              />
              <select
                aria-label={t("farm.areaUnitLabel")}
                value={areaUnit}
                onChange={(e) => setArea(areaInput, e.target.value as AreaUnit)}
                style={{ width: "auto" }}
              >
                <option value="ha">{t("units.ha")}</option>
                <option value="acre">{t("units.acre")}</option>
                <option value="perch">{t("units.perch")}</option>
              </select>
            </div>
            <span id="area-hint" className="muted">
              {Number.isFinite(values.area_ha) ? t("farm.areaStored", { ha: values.area_ha.toFixed(4) }) : ""}
            </span>
            <FieldError id={errId("area_ha")} message={err("area_ha")} />
          </div>

          <div className="field">
            <label htmlFor="irrigation">
              {t("farm.irrigation")} <span className="muted">({t("common.optional")})</span>
            </label>
            <input
              id="irrigation"
              type="number"
              min="0"
              step="any"
              disabled={values.irrigation_supply_mm_per_season === null}
              value={values.irrigation_supply_mm_per_season ?? ""}
              placeholder={t("common.unknown")}
              onChange={(e) =>
                update((v) => ({
                  ...v,
                  irrigation_supply_mm_per_season: e.target.value === "" ? null : num(e.target.value),
                }))
              }
              aria-invalid={!!err("irrigation_supply_mm_per_season")}
              aria-describedby={describedBy("irrigation_supply_mm_per_season")}
            />
            <label style={{ fontWeight: 400, fontSize: "0.875rem" }}>
              <input
                type="checkbox"
                checked={values.irrigation_supply_mm_per_season === null}
                onChange={(e) =>
                  update((v) => ({ ...v, irrigation_supply_mm_per_season: e.target.checked ? null : 0 }))
                }
                style={{ width: "auto", marginRight: 6 }}
              />
              {t("farm.irrigationUnknown")}
            </label>
            <FieldError
              id={errId("irrigation_supply_mm_per_season")}
              message={err("irrigation_supply_mm_per_season")}
            />
          </div>
        </div>

        <fieldset className="card" style={{ margin: "0 0 16px" }}>
          <legend style={{ fontWeight: 600 }}>{t("farm.priorities")}</legend>
          <p className="muted" style={{ marginTop: 0 }}>
            {t("farm.prioritiesHelp")}
          </p>
          {(["water", "soil", "climate"] as const).map((key) => {
            const label = t(`farm.priority${key.charAt(0).toUpperCase() + key.slice(1)}`);
            return (
              <div key={key} className="field" style={{ marginBottom: 8 }}>
                <label htmlFor={`priority-${key}`} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{label}</span>
                  <span>{values.priority_weights[key].toFixed(1)}</span>
                </label>
                <input
                  id={`priority-${key}`}
                  type="range"
                  min={0}
                  max={1}
                  step={0.1}
                  value={values.priority_weights[key]}
                  onChange={(e) =>
                    update((v) => ({ ...v, priority_weights: { ...v.priority_weights, [key]: Number(e.target.value) } }))
                  }
                  style={{ padding: 0 }}
                />
              </div>
            );
          })}
          <FieldError id={errId("priority_weights")} message={err("priority_weights")} />
        </fieldset>

        <div className="card field">
          <label htmlFor="exclusions">{t("farm.excludedCrops")}</label>
          <input
            id="exclusions"
            type="text"
            value={exclusionsInput}
            onChange={(e) => setExclusions(e.target.value)}
            placeholder="e.g. maize, groundnut"
            aria-describedby="exclusions-hint"
            list="catalog-crops"
          />
          <datalist id="catalog-crops">
            {catalogIds.map((id) => (
              <option key={id} value={id} />
            ))}
          </datalist>
          <span id="exclusions-hint" className="muted">
            {t("farm.excludedCropsHelp")}
          </span>
        </div>

        <fieldset className="card" style={{ margin: "0 0 16px" }}>
          <legend style={{ fontWeight: 600 }}>{t("farm.cropHistory")}</legend>
          {values.crop_history.length === 0 && <p className="muted">{t("farm.noHistory")}</p>}
          {values.crop_history.map((entry, i) => (
            <div key={i} className="grid-2" style={{ marginBottom: 12, alignItems: "end" }}>
              <div className="field">
                <label htmlFor={`ch-crop-${i}`}>
                  {t("farm.cropId")} {i + 1}
                </label>
                <input
                  id={`ch-crop-${i}`}
                  value={entry.crop_id}
                  list="catalog-crops"
                  onChange={(e) =>
                    update((v) => ({
                      ...v,
                      crop_history: v.crop_history.map((h, j) => (j === i ? { ...h, crop_id: e.target.value } : h)),
                    }))
                  }
                  aria-invalid={!!err(`crop_history.${i}.crop_id`)}
                  aria-describedby={describedBy(`crop_history.${i}.crop_id`)}
                />
                <FieldError id={errId(`crop_history.${i}.crop_id`)} message={err(`crop_history.${i}.crop_id`)} />
              </div>
              <div className="field">
                <label htmlFor={`ch-planted-${i}`}>{t("farm.plantedOn")}</label>
                <input
                  id={`ch-planted-${i}`}
                  type="date"
                  max={today}
                  value={entry.planted_on}
                  onChange={(e) =>
                    update((v) => ({
                      ...v,
                      crop_history: v.crop_history.map((h, j) => (j === i ? { ...h, planted_on: e.target.value } : h)),
                    }))
                  }
                  aria-invalid={!!err(`crop_history.${i}.planted_on`)}
                  aria-describedby={describedBy(`crop_history.${i}.planted_on`)}
                />
                <FieldError id={errId(`crop_history.${i}.planted_on`)} message={err(`crop_history.${i}.planted_on`)} />
              </div>
              <div className="field">
                <label htmlFor={`ch-harvested-${i}`}>{t("farm.harvestedOn")}</label>
                <input
                  id={`ch-harvested-${i}`}
                  type="date"
                  min={entry.planted_on}
                  value={entry.harvested_on ?? ""}
                  onChange={(e) =>
                    update((v) => ({
                      ...v,
                      crop_history: v.crop_history.map((h, j) =>
                        j === i ? { ...h, harvested_on: e.target.value || null } : h,
                      ),
                    }))
                  }
                  aria-invalid={!!err(`crop_history.${i}.harvested_on`)}
                  aria-describedby={describedBy(`crop_history.${i}.harvested_on`)}
                />
                <FieldError
                  id={errId(`crop_history.${i}.harvested_on`)}
                  message={err(`crop_history.${i}.harvested_on`)}
                />
              </div>
              <button
                type="button"
                className="btn btn-danger"
                onClick={() => update((v) => ({ ...v, crop_history: v.crop_history.filter((_, j) => j !== i) }))}
              >
                {t("common.remove")} {i + 1}
              </button>
            </div>
          ))}
          <button
            type="button"
            className="btn"
            onClick={() =>
              update((v) => ({
                ...v,
                crop_history: [...v.crop_history, { crop_id: "", planted_on: today, harvested_on: null }],
              }))
            }
          >
            + {t("farm.addCrop")}
          </button>
        </fieldset>

        <fieldset className="card" style={{ margin: "0 0 16px" }}>
          <legend style={{ fontWeight: 600 }}>{t("farm.soilTests")}</legend>
          <p className="notice notice-info" style={{ marginTop: 0 }}>
            {t("farm.soilUnknownNote")}
          </p>
          {values.soil_tests.map((test, i) => (
            <div key={i} className="grid-2" style={{ marginBottom: 12, alignItems: "end" }}>
              {(
                [
                  ["metric", "text", t("farm.soilMetric")],
                  ["value", "number", t("farm.soilValue")],
                  ["unit", "text", t("farm.soilUnit")],
                  ["sampled_on", "date", t("farm.soilSampledOn")],
                ] as const
              ).map(([k, type, label]) => {
                const path = `soil_tests.${i}.${k}`;
                return (
                  <div className="field" key={k}>
                    <label htmlFor={`soil-${k}-${i}`}>
                      {label} {i + 1}
                    </label>
                    <input
                      id={`soil-${k}-${i}`}
                      type={type}
                      step={type === "number" ? "any" : undefined}
                      max={type === "date" ? today : undefined}
                      value={k === "value" ? (Number.isFinite(test.value) ? test.value : "") : test[k]}
                      onChange={(e) =>
                        update((v) => ({
                          ...v,
                          soil_tests: v.soil_tests.map((s, j) =>
                            j === i ? { ...s, [k]: k === "value" ? num(e.target.value) : e.target.value } : s,
                          ),
                        }))
                      }
                      aria-invalid={!!err(path)}
                      aria-describedby={describedBy(path)}
                    />
                    <FieldError id={errId(path)} message={err(path)} />
                  </div>
                );
              })}
              <button
                type="button"
                className="btn btn-danger"
                onClick={() => update((v) => ({ ...v, soil_tests: v.soil_tests.filter((_, j) => j !== i) }))}
              >
                {t("common.remove")} {i + 1}
              </button>
            </div>
          ))}
          <button
            type="button"
            className="btn"
            onClick={() =>
              update((v) => ({
                ...v,
                soil_tests: [...v.soil_tests, { metric: "", value: Number.NaN, unit: "", sampled_on: today }],
              }))
            }
          >
            + {t("farm.addSoilTest")}
          </button>
        </fieldset>

        {editingFarm && <p className="muted">{t("farm.editWarning")}</p>}

        <button type="submit" className="btn btn-primary" disabled={saving} style={{ width: "100%", padding: 12 }}>
          {saving ? t("common.loading") : mode === "new" ? t("farm.save") : t("farm.update")}
        </button>
      </form>
    </div>
  );
}
