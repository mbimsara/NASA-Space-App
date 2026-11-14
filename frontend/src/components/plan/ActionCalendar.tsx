/**
 * ActionCalendar — farmer-entered actions per season of a saved plan, sorted by date,
 * stored on this device, exportable as .ics. No reminders are sent.
 * Owner: Shehani.
 */
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ACTION_KINDS,
  initialEntries,
  loadCalendar,
  saveCalendar,
  sortedDated,
  toICS,
  validateCalendar,
  type ActionKind,
  type CalendarEntry,
  type SeasonInfo,
} from "../../utils/calendar";

interface Props {
  planId: string;
  seasons: SeasonInfo[];
}

export function ActionCalendar({ planId, seasons }: Props) {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<CalendarEntry[]>(() => loadCalendar(planId) ?? initialEntries(seasons));
  const [seq, setSeq] = useState(1);

  useEffect(() => {
    saveCalendar(planId, entries);
  }, [planId, entries]);

  const errors = useMemo(() => validateCalendar(entries), [entries]);
  const dated = sortedDated(entries);
  const kindLabel = (k: ActionKind) => t(`calendar.kind.${k}`);
  const crop = (i: number) => seasons.find((s) => s.season_index === i)?.crop_name ?? String(i);

  const update = (id: string, patch: Partial<CalendarEntry>) =>
    setEntries((es) => es.map((e) => (e.id === id ? { ...e, ...patch } : e)));

  const add = (season_index: number) => {
    setEntries((es) => [...es, { id: `a${Date.now()}-${seq}`, season_index, kind: "monitoring", date: "", note: "" }]);
    setSeq((n) => n + 1);
  };

  const download = () => {
    const ics = toICS(planId, entries, seasons, kindLabel, t("calendar.disclaimer"));
    const url = URL.createObjectURL(new Blob([ics], { type: "text/calendar;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `agrosphere-${planId}-calendar.ics`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="card" aria-labelledby="calendar-title">
      <h2 id="calendar-title" style={{ marginTop: 0 }}>
        {t("calendar.title")}
      </h2>
      <p className="muted" style={{ marginTop: 0 }}>
        {t("calendar.help")}
      </p>

      <div className="no-print">
        {seasons.map((s) => (
          <fieldset key={s.season_index} style={{ border: "1px solid var(--border)", borderRadius: 6, margin: "0 0 10px", padding: 10 }}>
            <legend style={{ fontWeight: 600 }}>{t("calendar.seasonLegend", { n: s.season_index, crop: s.crop_name })}</legend>
            {entries
              .filter((e) => e.season_index === s.season_index)
              .map((e) => (
                <div key={e.id} className="grid-2" style={{ alignItems: "end", marginBottom: 8 }}>
                  <div className="field">
                    <label htmlFor={`cal-kind-${e.id}`}>{t("calendar.action")}</label>
                    <select id={`cal-kind-${e.id}`} value={e.kind} onChange={(ev) => update(e.id, { kind: ev.target.value as ActionKind })}>
                      {ACTION_KINDS.map((k) => (
                        <option key={k} value={k}>
                          {kindLabel(k)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label htmlFor={`cal-date-${e.id}`}>{t("calendar.date")}</label>
                    <input
                      id={`cal-date-${e.id}`}
                      type="date"
                      value={e.date}
                      onChange={(ev) => update(e.id, { date: ev.target.value })}
                      aria-invalid={!!errors[e.id]}
                      aria-describedby={errors[e.id] ? `cal-err-${e.id}` : undefined}
                    />
                    {errors[e.id] && (
                      <span id={`cal-err-${e.id}`} className="field-error" role="alert">
                        {errors[e.id]}
                      </span>
                    )}
                  </div>
                  <div className="field">
                    <label htmlFor={`cal-note-${e.id}`}>{t("calendar.note")}</label>
                    <input id={`cal-note-${e.id}`} value={e.note} onChange={(ev) => update(e.id, { note: ev.target.value })} />
                  </div>
                  <button type="button" className="btn btn-danger" onClick={() => setEntries((es) => es.filter((x) => x.id !== e.id))}>
                    {t("common.remove")}
                  </button>
                </div>
              ))}
            <button type="button" className="btn" onClick={() => add(s.season_index)}>
              + {t("calendar.addAction")}
            </button>
          </fieldset>
        ))}
      </div>

      <h3 style={{ fontSize: "1rem" }}>{t("calendar.timeline")}</h3>
      {dated.length === 0 ? (
        <p className="muted">{t("calendar.empty")}</p>
      ) : (
        <div className="table-scroll">
          <table className="data">
            <thead>
              <tr>
                <th scope="col">{t("calendar.date")}</th>
                <th scope="col">{t("calendar.action")}</th>
                <th scope="col">{t("rotation.season")}</th>
                <th scope="col">{t("calendar.note")}</th>
              </tr>
            </thead>
            <tbody>
              {dated.map((e) => (
                <tr key={e.id}>
                  <td>{e.date}</td>
                  <td>{kindLabel(e.kind)}</td>
                  <td>
                    {e.season_index}. {crop(e.season_index)}
                  </td>
                  <td>{e.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="row no-print" style={{ marginTop: 10 }}>
        <button type="button" className="btn btn-secondary" onClick={download} disabled={dated.length === 0 || Object.keys(errors).length > 0}>
          {t("calendar.export")}
        </button>
        <span className="muted" style={{ fontSize: 12 }}>
          {t("calendar.localOnly")}
        </span>
      </div>
    </section>
  );
}
