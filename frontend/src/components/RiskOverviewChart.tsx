import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

interface RiskData {
    name: string;
    value: number;
    color: string;
}

export const RiskOverviewChart = () => {
    const statsQuery = useApiQuery<Record<string, number>>(
        queryKeys.dashboard.stats,
        "/api/dashboard/stats",
    );
    const stats = statsQuery.data;
    const data: RiskData[] = [
        { name: "High Risk", value: stats?.high_risk_count || 0, color: "hsl(340, 45%, 65%)" },
        { name: "Medium Risk", value: stats?.medium_risk_count || 0, color: "hsl(270, 50%, 60%)" },
        { name: "Low Risk", value: stats?.low_risk_count || 0, color: "hsl(200, 60%, 55%)" },
        { name: "Not Assessed", value: stats?.unassessed_count || 0, color: "hsl(215, 16%, 65%)" },
    ];
    const totalPatients = stats?.total_patients || 0;

    return (
        <div className="bg-card border border-border/50 rounded-2xl p-6 shadow-soft h-full">
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-foreground">Risk Distribution</h3>
                <p className="text-sm text-muted-foreground">Current patient risk assessment</p>
            </div>

            <div className="h-[250px] w-full relative">
                {statsQuery.isPending ? (
                    <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-muted-foreground">Loading...</p>
                    </div>
                ) : (
                    <>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={data}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "rgba(255, 255, 255, 0.9)",
                                        borderRadius: "12px",
                                        border: "none",
                                        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)"
                                    }}
                                    itemStyle={{ color: "#374151", fontSize: "12px", fontWeight: 500 }}
                                />
                                <Legend
                                    verticalAlign="bottom"
                                    height={36}
                                    iconType="circle"
                                    formatter={(value) => (
                                        <span className="text-sm text-muted-foreground font-medium ml-1">{value}</span>
                                    )}
                                />
                            </PieChart>
                        </ResponsiveContainer>

                        {/* Center Text */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center -mt-4">
                            <p className="text-3xl font-bold text-foreground">{totalPatients}</p>
                            <p className="text-xs text-muted-foreground font-medium">Total Patients</p>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
