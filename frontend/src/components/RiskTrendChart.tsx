import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";

const API_URL = "http://localhost:8000";

// Mock data for demonstration (until historical tracking is implemented)
const mockData = [
    { day: "Mon", highRisk: 0, mediumRisk: 0 },
    { day: "Tue", highRisk: 0, mediumRisk: 0 },
    { day: "Wed", highRisk: 0, mediumRisk: 0 },
    { day: "Thu", highRisk: 0, mediumRisk: 0 },
    { day: "Fri", highRisk: 0, mediumRisk: 0 },
    { day: "Sat", highRisk: 0, mediumRisk: 0 },
    { day: "Sun", highRisk: 0, mediumRisk: 0 },
];

export const RiskTrendChart = () => {
    const { user } = useAuth();
    const [data, setData] = useState(mockData);
    const [hasPatients, setHasPatients] = useState(false);

    useEffect(() => {
        if (user?.email) {
            fetchTrendData();
        }
    }, [user?.email]);

    const fetchTrendData = async () => {
        try {
            // Build headers with user email for doctor filtering
            const headers: HeadersInit = {};
            if (user?.email) {
                headers['X-User-Email'] = user.email;
            }
            
            const response = await fetch(`${API_URL}/api/dashboard/stats`, { headers });
            if (response.ok) {
                const stats = await response.json();
                const totalPatients = stats.total_patients || 0;
                setHasPatients(totalPatients > 0);
                
                // For now, use current stats to show on the last day
                // TODO: Implement proper historical tracking
                if (totalPatients > 0) {
                    setData([
                        { day: "Mon", highRisk: 0, mediumRisk: 0 },
                        { day: "Tue", highRisk: 0, mediumRisk: 0 },
                        { day: "Wed", highRisk: 0, mediumRisk: 0 },
                        { day: "Thu", highRisk: 0, mediumRisk: 0 },
                        { day: "Fri", highRisk: 0, mediumRisk: 0 },
                        { day: "Sat", highRisk: 0, mediumRisk: 0 },
                        { day: "Sun", highRisk: stats.high_risk_count || 0, mediumRisk: stats.medium_risk_count || 0 },
                    ]);
                }
            }
        } catch (error) {
            console.error('Failed to fetch trend data:', error);
        }
    };
    return (
        <div className="bg-card border border-border/50 rounded-2xl p-6 shadow-soft h-full">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-foreground">Risk Trends</h3>
                    <p className="text-sm text-muted-foreground">Weekly high-risk case tracking</p>
                </div>
                <div className="flex items-center gap-2 text-sm">
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
                            dataKey="day"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#6b7280', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#6b7280', fontSize: 12 }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "rgba(255, 255, 255, 0.9)",
                                borderRadius: "12px",
                                border: "none",
                                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)"
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
            </div>
        </div>
    );
};
