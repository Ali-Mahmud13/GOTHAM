import { useMemo, useState } from 'react';
import type { ElementType } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Activity, Heart, Droplets, TrendingUp, Eye, EyeOff } from 'lucide-react';
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
  visit: string;
  date: string;
  bmi: number | null;
  sysBP: number | null;
  diaBP: number | null;
  glucose: number | null;
  hgb: number | null;
  fetalBaseline: number | null;
}

interface MetricConfig {
  key: string;
  name: string;
  unit: string;
  color: string;
  gradientFrom: string;
  gradientTo: string;
  icon: ElementType;
  description: string;
}

const metricsConfig: MetricConfig[] = [
  {
    key: 'bmi',
    name: 'BMI',
    unit: '',
    color: '#ec4899', // medical-pink
    gradientFrom: 'from-pink-500',
    gradientTo: 'to-rose-500',
    icon: Activity,
    description: 'Body Mass Index',
  },
  {
    key: 'sysBP',
    name: 'Systolic BP',
    unit: 'mmHg',
    color: '#6366f1', // indigo
    gradientFrom: 'from-indigo-500',
    gradientTo: 'to-purple-500',
    icon: Heart,
    description: 'Blood Pressure (Systolic)',
  },
  {
    key: 'diaBP',
    name: 'Diastolic BP',
    unit: 'mmHg',
    color: '#8b5cf6', // violet
    gradientFrom: 'from-violet-500',
    gradientTo: 'to-purple-500',
    icon: Heart,
    description: 'Blood Pressure (Diastolic)',
  },
  {
    key: 'glucose',
    name: 'Glucose',
    unit: 'mg/dL',
    color: '#06b6d4', // medical-blue (cyan)
    gradientFrom: 'from-cyan-500',
    gradientTo: 'to-blue-500',
    icon: Droplets,
    description: 'Blood glucose / OGTT',
  },
  {
    key: 'hgb',
    name: 'Hemoglobin',
    unit: 'g/dL',
    color: '#f43f5e',
    gradientFrom: 'from-rose-500',
    gradientTo: 'to-red-500',
    icon: Activity,
    description: 'Hemoglobin level',
  },
  {
    key: 'fetalBaseline',
    name: 'Fetal Baseline HR',
    unit: 'bpm',
    color: '#10b981', // emerald
    gradientFrom: 'from-emerald-500',
    gradientTo: 'to-teal-500',
    icon: Heart,
    description: 'CTG baseline fetal heart rate',
  },
];

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white/95 backdrop-blur-lg border border-gray-200 rounded-xl shadow-2xl p-4 min-w-[200px]">
        <p className="font-bold text-gray-900 mb-3 text-sm">{data.visit}</p>
        <p className="text-xs text-gray-500 mb-3">{data.date}</p>
        <div className="space-y-2">
          {payload.map((entry: any) => {
            const metric = metricsConfig.find(m => m.key === entry.dataKey);
            return (
              <div key={entry.dataKey} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-xs font-semibold text-gray-700">{metric?.name}</span>
                </div>
                <span className="text-sm font-bold text-gray-900">
                  {entry.value ?? 'N/A'} {entry.value !== null && entry.value !== undefined ? metric?.unit : ''}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
};

interface VitalsChartProps {
  visits: VisitVitalsPoint[];
}

export const VitalsChart = ({ visits }: VitalsChartProps) => {
  const [visibleMetrics, setVisibleMetrics] = useState<string[]>(['bmi', 'sysBP', 'glucose']);

  const chartData = useMemo<ChartPoint[]>(() => {
    if (!visits || visits.length === 0) {
      return [];
    }

    return [...visits]
      .slice()
      .sort((a, b) => new Date(a.visit_date).getTime() - new Date(b.visit_date).getTime())
      .map((visit, index) => {
        const visitDate = new Date(visit.visit_date);
        return {
          visit: `Visit ${index + 1}`,
          date: visitDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          bmi: visit.bmi ?? null,
          sysBP: visit.blood_pressure_systolic ?? null,
          diaBP: visit.blood_pressure_diastolic ?? null,
          glucose: visit.glucose_level ?? visit.ogtt ?? null,
          hgb: visit.hgb ?? null,
          fetalBaseline: visit.baseline_value ?? null,
        };
      });
  }, [visits]);

  const toggleMetric = (metricKey: string) => {
    setVisibleMetrics(prev =>
      prev.includes(metricKey)
        ? prev.filter(k => k !== metricKey)
        : [...prev, metricKey]
    );
  };

  const getLatestValue = (key: string) => {
    if (chartData.length === 0) return 'N/A';
    const latestData = chartData[chartData.length - 1] as Record<string, string | number | null>;
    const value = latestData[key];
    return value ?? 'N/A';
  };

  const getTrend = (key: string) => {
    if (chartData.length < 2) return 0;
    const latest = chartData[chartData.length - 1][key as keyof ChartPoint];
    const previous = chartData[chartData.length - 2][key as keyof ChartPoint];
    if (typeof latest === 'number' && typeof previous === 'number') {
      if (previous === 0) return 0;
      return ((latest - previous) / previous * 100).toFixed(1);
    }
    return 0;
  };

  return (
    <div className="w-full space-y-6">
      {/* Metric Toggles */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {metricsConfig.map((metric) => {
          const Icon = metric.icon;
          const isVisible = visibleMetrics.includes(metric.key);
          const trend = getTrend(metric.key);
          const trendNum = typeof trend === 'string' ? parseFloat(trend) : trend;

          return (
            <button
              key={metric.key}
              onClick={() => toggleMetric(metric.key)}
              className={cn(
                "relative p-4 rounded-xl border-2 transition-all duration-300 text-left group overflow-hidden",
                isVisible
                  ? "border-transparent shadow-lg hover:shadow-xl scale-100"
                  : "border-gray-200 bg-white hover:border-gray-300 opacity-60 hover:opacity-100"
              )}
              style={{
                background: isVisible
                  ? `linear-gradient(135deg, ${metric.color}15, ${metric.color}05)`
                  : undefined,
              }}
            >
              {/* Toggle Icon */}
              <div className="absolute top-2 right-2">
                {isVisible ? (
                  <Eye className="w-4 h-4 text-gray-600" />
                ) : (
                  <EyeOff className="w-4 h-4 text-gray-400" />
                )}
              </div>

              {/* Metric Icon */}
              <div
                className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center mb-3 transition-transform group-hover:scale-110",
                  `bg-gradient-to-br ${metric.gradientFrom} ${metric.gradientTo}`
                )}
              >
                <Icon className="w-5 h-5 text-white" />
              </div>

              {/* Metric Name */}
              <p className="text-xs font-semibold text-gray-600 mb-1">{metric.name}</p>

              {/* Latest Value */}
              <p className="text-2xl font-bold text-gray-900 mb-1">
                {getLatestValue(metric.key)}
                {metric.unit && getLatestValue(metric.key) !== 'N/A' && (
                  <span className="text-sm ml-1 text-gray-500">{metric.unit}</span>
                )}
              </p>

              {/* Trend */}
              <div className="flex items-center gap-1">
                <TrendingUp
                  className={cn(
                    "w-3 h-3",
                    trendNum > 0 ? "text-red-500" : trendNum < 0 ? "text-green-500" : "text-gray-400",
                    trendNum < 0 && "rotate-180"
                  )}
                />
                <span
                  className={cn(
                    "text-xs font-semibold",
                    trendNum > 0 ? "text-red-600" : trendNum < 0 ? "text-green-600" : "text-gray-500"
                  )}
                >
                  {Math.abs(trendNum)}%
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Chart Container */}
      <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 border border-gray-200 shadow-lg">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Vitals Trend Analysis</h3>
            <p className="text-sm text-gray-600">Track health metrics over time</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Activity className="w-4 h-4" />
            <span>{chartData.length} visits recorded</span>
          </div>
        </div>

        {chartData.length === 0 ? (
          <div className="h-[400px] flex items-center justify-center text-gray-400">
            <div className="text-center">
              <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="font-semibold">No vitals data available</p>
              <p className="text-sm">Add new visits to view metric trends</p>
            </div>
          </div>
        ) : visibleMetrics.length === 0 ? (
          <div className="h-[400px] flex items-center justify-center text-gray-400">
            <div className="text-center">
              <EyeOff className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="font-semibold">No metrics selected</p>
              <p className="text-sm">Click on metric cards above to display them</p>
            </div>
          </div>
        ) : (
          <div className="w-full h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <defs>
                  {metricsConfig.map((metric) => (
                    <linearGradient
                      key={`gradient-${metric.key}`}
                      id={`gradient-${metric.key}`}
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="0%" stopColor={metric.color} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={metric.color} stopOpacity={0.05} />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#6b7280', fontSize: 12, fontWeight: 600 }}
                  stroke="#d1d5db"
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#6b7280', fontSize: 12, fontWeight: 600 }}
                  stroke="#d1d5db"
                  tickLine={false}
                  label={{
                    value: 'Value',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#374151', fontWeight: 600 },
                  }}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#d1d5db', strokeWidth: 1 }} />
                <Legend
                  wrapperStyle={{ paddingTop: '20px' }}
                  iconType="line"
                  formatter={(value) => {
                    const metric = metricsConfig.find(m => m.key === value);
                    return <span className="text-sm font-semibold text-gray-700">{metric?.name}</span>;
                  }}
                />

                {metricsConfig.map((metric) => {
                  if (!visibleMetrics.includes(metric.key)) return null;
                  return (
                    <Line
                      key={metric.key}
                      type="monotone"
                      dataKey={metric.key}
                      stroke={metric.color}
                      strokeWidth={3}
                      dot={{
                        fill: metric.color,
                        r: 5,
                        strokeWidth: 2,
                        stroke: 'white',
                      }}
                      activeDot={{
                        r: 7,
                        strokeWidth: 3,
                        stroke: 'white',
                      }}
                      name={metric.key}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};