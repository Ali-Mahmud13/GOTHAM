import { useMemo, useState } from 'react';
import type { ElementType } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Heart, Droplets, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface VisitVitalsPoint {
  id: number;
  visit_date: string;
  bmi?: number | null;
  blood_pressure_systolic?: number | null;
  blood_pressure_diastolic?: number | null;
  glucose_level?: number | null;
  ogtt?: number | null;
  hgb?: number | null;
  baseline_value?: number | null;
}

interface ChartPoint {
  date: string;
  bmi: number | null;
  sysBP: number | null;
  diaBP: number | null;
  glucose: number | null;
  ogtt: number | null;
  hgb: number | null;
  fetalBaseline: number | null;
}

type MetricKey = 'bmi' | 'sysBP' | 'diaBP' | 'glucose' | 'ogtt' | 'hgb' | 'fetalBaseline';

interface MetricConfig {
  key: MetricKey;
  name: string;
  unit: string;
  color: string;
  gradient: string;
  icon: ElementType;
  description: string;
}

const metricsConfig: MetricConfig[] = [
  { key: 'bmi', name: 'BMI', unit: '', color: '#ec4899', gradient: 'from-pink-500 to-rose-500', icon: Activity, description: 'Body Mass Index' },
  { key: 'sysBP', name: 'Systolic BP', unit: 'mmHg', color: '#6366f1', gradient: 'from-indigo-500 to-purple-500', icon: Heart, description: 'Systolic blood pressure' },
  { key: 'diaBP', name: 'Diastolic BP', unit: 'mmHg', color: '#8b5cf6', gradient: 'from-violet-500 to-purple-500', icon: Heart, description: 'Diastolic blood pressure' },
  { key: 'glucose', name: 'Glucose', unit: 'mg/dL', color: '#06b6d4', gradient: 'from-cyan-500 to-blue-500', icon: Droplets, description: 'Blood glucose' },
  { key: 'ogtt', name: 'OGTT', unit: 'mg/dL', color: '#0ea5e9', gradient: 'from-sky-500 to-cyan-500', icon: Droplets, description: 'Oral glucose tolerance test' },
  { key: 'hgb', name: 'Hemoglobin', unit: 'g/dL', color: '#f43f5e', gradient: 'from-rose-500 to-red-500', icon: Activity, description: 'Hemoglobin level' },
  { key: 'fetalBaseline', name: 'Fetal Baseline HR', unit: 'bpm', color: '#10b981', gradient: 'from-emerald-500 to-teal-500', icon: Heart, description: 'CTG baseline fetal heart rate' },
];

interface VitalsChartProps {
  visits: VisitVitalsPoint[];
}

export const VitalsChart = ({ visits }: VitalsChartProps) => {
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>(() => (
    metricsConfig.find((metric) => visits.some((visit) => {
      const sourceKey: keyof VisitVitalsPoint =
        metric.key === 'sysBP' ? 'blood_pressure_systolic'
          : metric.key === 'diaBP' ? 'blood_pressure_diastolic'
            : metric.key === 'glucose' ? 'glucose_level'
              : metric.key === 'fetalBaseline' ? 'baseline_value'
                : metric.key;
      return typeof visit[sourceKey] === 'number';
    }))?.key ?? 'bmi'
  ));

  const chartData = useMemo<ChartPoint[]>(() => (
    [...visits]
      .sort((a, b) => new Date(a.visit_date).getTime() - new Date(b.visit_date).getTime())
      .map((visit) => {
        const visitDate = new Date(visit.visit_date);
        return {
          date: visitDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }),
          bmi: visit.bmi ?? null,
          sysBP: visit.blood_pressure_systolic ?? null,
          diaBP: visit.blood_pressure_diastolic ?? null,
          glucose: visit.glucose_level ?? null,
          ogtt: visit.ogtt ?? null,
          hgb: visit.hgb ?? null,
          fetalBaseline: visit.baseline_value ?? null,
        };
      })
  ), [visits]);

  const getReadings = (key: MetricKey) => chartData.filter((point) => typeof point[key] === 'number');

  const getTrend = (key: MetricKey) => {
    const readings = getReadings(key);
    if (readings.length < 2) return { direction: 'none' as const, label: readings.length === 1 ? 'One reading' : 'No readings' };

    const latest = readings[readings.length - 1][key] as number;
    const previous = readings[readings.length - 2][key] as number;
    if (latest === previous) return { direction: 'same' as const, label: 'No change' };

    const direction = latest > previous ? 'up' as const : 'down' as const;
    const percentage = previous === 0 ? null : Math.abs(((latest - previous) / previous) * 100);
    return {
      direction,
      label: `${direction === 'up' ? 'Increased' : 'Decreased'}${percentage === null ? '' : ` ${percentage.toFixed(1)}%`}`,
    };
  };

  const selectedConfig = metricsConfig.find((metric) => metric.key === selectedMetric) ?? metricsConfig[0];
  const selectedData = getReadings(selectedMetric);

  return (
    <div className="w-full space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
        {metricsConfig.map((metric) => {
          const Icon = metric.icon;
          const readings = getReadings(metric.key);
          const latest = readings[readings.length - 1];
          const trend = getTrend(metric.key);
          const isSelected = selectedMetric === metric.key;

          return (
            <button
              key={metric.key}
              type="button"
              onClick={() => setSelectedMetric(metric.key)}
              className={cn(
                'relative p-4 rounded-xl border-2 transition-all duration-300 text-left group',
                isSelected
                  ? 'border-transparent shadow-lg ring-2 ring-medical-blue/30'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md',
              )}
              style={{ background: isSelected ? `linear-gradient(135deg, ${metric.color}18, ${metric.color}05)` : undefined }}
              aria-pressed={isSelected}
            >
              <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-3 bg-gradient-to-br transition-transform group-hover:scale-105', metric.gradient)}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <p className="text-xs font-semibold text-gray-600">{metric.name}</p>
              <p className="text-xl font-bold text-gray-900 mt-1">
                {latest ? latest[metric.key] : 'N/A'}
                {latest && metric.unit && <span className="text-xs ml-1 text-gray-500">{metric.unit}</span>}
              </p>
              <div className="flex items-center gap-1 mt-2 text-xs font-semibold text-gray-500">
                <TrendingUp className={cn('w-3 h-3 text-medical-blue', trend.direction === 'down' && 'rotate-180', trend.direction === 'none' && 'text-gray-300')} />
                <span>{trend.label}</span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 border border-gray-200 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-6">
          <div>
            <h3 className="text-lg font-bold text-gray-900">{selectedConfig.name} Trend</h3>
            <p className="text-sm text-gray-600">{selectedConfig.description}; trend compares the latest two available readings.</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Activity className="w-4 h-4" />
            <span>{selectedData.length} readings</span>
          </div>
        </div>

        {selectedData.length === 0 ? (
          <div className="h-[360px] flex items-center justify-center text-gray-400">
            <div className="text-center">
              <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="font-semibold">No {selectedConfig.name.toLowerCase()} readings</p>
              <p className="text-sm">Select another metric or add a visit with this measurement.</p>
            </div>
          </div>
        ) : (
          <div className="w-full h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={selectedData} margin={{ top: 8, right: 24, left: 20, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12, fontWeight: 600 }} stroke="#d1d5db" tickLine={false} />
                <YAxis
                  domain={['auto', 'auto']}
                  tick={{ fill: '#6b7280', fontSize: 12, fontWeight: 600 }}
                  stroke="#d1d5db"
                  tickLine={false}
                  label={{
                    value: selectedConfig.unit || selectedConfig.name,
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#374151', fontWeight: 600 },
                  }}
                />
                <Tooltip
                  formatter={(value) => [`${value}${selectedConfig.unit ? ` ${selectedConfig.unit}` : ''}`, selectedConfig.name]}
                  labelFormatter={(label) => `Recorded ${label}`}
                  contentStyle={{ borderRadius: 12, borderColor: '#e5e7eb', boxShadow: '0 12px 30px rgba(15, 23, 42, 0.12)' }}
                />
                <Line
                  type="monotone"
                  dataKey={selectedMetric}
                  stroke={selectedConfig.color}
                  strokeWidth={3}
                  connectNulls={false}
                  dot={{ fill: selectedConfig.color, r: 5, strokeWidth: 2, stroke: 'white' }}
                  activeDot={{ r: 7, strokeWidth: 3, stroke: 'white' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};
