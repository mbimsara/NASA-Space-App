/**
 * ObservationChart — renders rainfall and temperature time series.
 * Shows explicit missing-data state; never substitutes zero for null.
 * Owner: Shehani. Time-series fields to be agreed with Matheesha.
 */
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { useTranslation } from "react-i18next";
import type { TimeSeriesPoint } from "../../types/api";
import { MissingDataPlaceholder } from "../ui/MissingDataPlaceholder";
import { cssVar, useTheme } from "../../hooks/useTheme";

interface Props {
  /** Normalized points (see utils/observations.toChartPoints). */
  timeSeries: TimeSeriesPoint[] | undefined;
  hasData: boolean;
}

export function ObservationChart({ timeSeries, hasData }: Props) {
  const { t } = useTranslation();
  // SVG attributes cannot use var(); resolve the theme's chart colours and re-render on theme change.
  const [theme] = useTheme();
  const c = {
    rain: cssVar("--chart-rain", "#2f7fc1"),
    temp: cssVar("--chart-temp", "#d9741c"),
    grid: cssVar("--chart-grid", "#e3ebe5"),
    text: cssVar("--chart-text", "#55685f"),
    surface: cssVar("--surface", "#ffffff"),
    theme,
  };

  if (!hasData || !timeSeries || timeSeries.length === 0) {
    return <MissingDataPlaceholder reason={t("observations.noSeries")} />;
  }

  // Format for recharts — keep null as null so gaps are visible (not zeroed)
  const data = timeSeries.map((p) => ({
    date: p.date.slice(5), // show MM-DD
    rainfall: p.rainfall_mm,       // null means no data — recharts will gap the bar
    temperature: p.mean_temperature_c,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.grid} />
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: c.text }} stroke={c.grid} />
          <YAxis
            yAxisId="rain"
            orientation="left"
            label={{ value: "mm", angle: -90, position: "insideLeft", fontSize: 12, fill: c.text }}
            tick={{ fontSize: 12, fill: c.text }}
            stroke={c.grid}
          />
          <YAxis
            yAxisId="temp"
            orientation="right"
            label={{ value: "°C", angle: 90, position: "insideRight", fontSize: 12, fill: c.text }}
            tick={{ fontSize: 12, fill: c.text }}
            stroke={c.grid}
          />
          <Tooltip
            contentStyle={{ background: c.surface, border: `1px solid ${c.grid}`, borderRadius: 10, color: c.text }}
            formatter={(value, name) =>
              value === null || value === undefined ? [t("observations.noDataPoint"), name] : [value, name]
            }
          />
          <Legend formatter={(value) => <span style={{ color: c.text }}>{value}</span>} />
          <Bar
            yAxisId="rain"
            dataKey="rainfall"
            name={t("observations.rainfall")}
            fill={c.rain}
            opacity={0.8}
          />
          <Line
            yAxisId="temp"
            type="monotone"
            dataKey="temperature"
            name={t("observations.temperature")}
            stroke={c.temp}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="muted" style={{ fontSize: 12, marginTop: 4, textAlign: "center" }}>
        {t("observations.chartLegend", { rain: t("observations.rainfall"), temp: t("observations.temperature") })}
      </p>
    </div>
  );
}

