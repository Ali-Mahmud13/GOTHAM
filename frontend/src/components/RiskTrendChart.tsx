import { useState, useEffect } from "react";
import { CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, XAxis, YAxis } from "recharts";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import { apiFetch } from "@/lib/apiClient";

interface TrendPoint {
  day: string;
  date: string;
  highRisk: number;
  mediumRisk: number;
}

const WINDOW_OPTIONS = [7, 14, 30] as const;

export const RiskTrendChart = () => {
  const { user, tokens, setTokens, logout } = useAuth();
  const [selectedWindow, setSelectedWindow] = useState<(typeof WINDOW_OPTIONS)[number]>(30);
  const [data, setData] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.email) {
      fetchTrendData(selectedWindow);
    }
  }, [user?.email, selectedWindow]);

  const fetchTrendData = async (days: number) => {
    setLoading(true);
    try {
      const response = await apiFetch(
        `/api/dashboard/risk-trends?days=${days}`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (response.ok) {
        const payload: { data?: TrendPoint[] } = await response.json();
        setData(payload.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch trend data:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-card border border-border/50 rounded-2xl p-6 shadow-soft h-full">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Risk Trends</h3>
          <p className="text-sm text-muted-foreground">{selectedWindow}-day high and medium risk activity</p>
        </div>
        <div className="flex items-center gap-2 text-sm flex-wrap justify-end">
          <div className="inline-flex rounded-lg border border-border overflow-hidden">
            {WINDOW_OPTIONS.map((window) => (
              <button
                key={window}
                type="button"
                onClick={() => setSelectedWindow(window)}
                className={cn(
                  "px-3 py-1.5 text-xs font-semibold transition-colors",
                  selectedWindow === window
                    ? "bg-medical-blue text-white"
                    : "bg-background text-muted-foreground hover:bg-muted"
                )}
              >
                {window}D
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-medical-pink" />
            <span className="text-muted-foreground">High Risk</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-medical-blue" />
            <span className="text-muted-foreground">Medium Risk</span>
          </div>
        </div>
      </div>

      <div className="h-[250px] w-full">
        {loading ? (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            Loading trend data...
          </div>
        ) : data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            No recent visit activity
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ec4899" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorMedium" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" opacity={0.5} />
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#6b7280", fontSize: 12 }}
                dy={10}
                tickFormatter={(value: string) => {
                  const parsed = new Date(value);
                  if (Number.isNaN(parsed.getTime())) return value;
                  return selectedWindow > 7
                    ? parsed.toLocaleDateString("en-US", { month: "short", day: "numeric" })
                    : parsed.toLocaleDateString("en-US", { weekday: "short" });
                }}
                minTickGap={selectedWindow > 7 ? 20 : 8}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#6b7280", fontSize: 12 }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(255, 255, 255, 0.9)",
                  borderRadius: "12px",
                  border: "none",
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
                }}
                labelStyle={{ color: "#374151", fontWeight: 600, marginBottom: "4px" }}
              />
              <Area
                type="monotone"
                dataKey="highRisk"
                stroke="#ec4899"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorHigh)"
              />
              <Area
                type="monotone"
                dataKey="mediumRisk"
                stroke="#3b82f6"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorMedium)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
