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

interface Props {
  /** Normalized points (see utils/observations.toChartPoints). */
  timeSeries: TimeSeriesPoint[] | undefined;
  hasData: boolean;
}

export function ObservationChart({ timeSeries, hasData }: Props) {
  const { t } = useTranslation();

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
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis
            yAxisId="rain"
            orientation="left"
            label={{ value: "mm", angle: -90, position: "insideLeft", fontSize: 11 }}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            yAxisId="temp"
            orientation="right"
            label={{ value: "°C", angle: 90, position: "insideRight", fontSize: 11 }}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={(value, name) =>
              value === null || value === undefined ? [t("observations.noDataPoint"), name] : [value, name]
            }
          />
          <Legend />
          <Bar
            yAxisId="rain"
            dataKey="rainfall"
            name={t("observations.rainfall")}
            fill="#4a90d9"
            opacity={0.8}
          />
          <Line
            yAxisId="temp"
            type="monotone"
            dataKey="temperature"
            name={t("observations.temperature")}
            stroke="#e67e22"
            strokeWidth={2}
            dot={false}
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p style={{ fontSize: 11, color: "#888", marginTop: 4, textAlign: "center" }}>
        {t("observations.rainfall")} (bars, left axis) · {t("observations.temperature")} (line, right axis)
      </p>
    </div>
  );
}

