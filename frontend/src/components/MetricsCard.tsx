import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricsCardProps {
    title: string;
    value: string | number;
    subtext: string;
    icon: LucideIcon;
    trend?: "up" | "down" | "neutral";
    trendValue?: string;
    color?: "pink" | "blue" | "purple";
    onClick?: () => void;
}

export const MetricsCard = ({
    title,
    value,
    subtext,
    icon: Icon,
    trend,
    trendValue,
    color = "blue",
    onClick,
}: MetricsCardProps) => {
    const colorStyles = {
        pink: "from-medical-pink/10 to-medical-pink/5 text-medical-pink",
        blue: "from-medical-blue/10 to-medical-blue/5 text-medical-blue",
        purple: "from-purple-500/10 to-purple-500/5 text-purple-500",
    };

    const iconStyles = {
        pink: "bg-medical-pink/10 text-medical-pink",
        blue: "bg-medical-blue/10 text-medical-blue",
        purple: "bg-purple-500/10 text-purple-500",
    };

    return (
        <div className={cn("relative overflow-hidden rounded-2xl bg-card border border-border/50 shadow-soft p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-1", onClick && "cursor-pointer")} onClick={onClick}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm font-medium text-muted-foreground mb-1">{title}</p>
                    <h3 className="text-3xl font-bold text-foreground tracking-tight">{value}</h3>
                </div>
                <div className={cn("p-3 rounded-xl", iconStyles[color])}>
                    <Icon className="h-5 w-5" />
                </div>
            </div>

            <div className="mt-4 flex items-center gap-2">
                {trend && (
                    <span className={cn(
                        "text-xs font-medium px-2 py-0.5 rounded-full",
                        trend === "up" ? "bg-green-500/10 text-green-600" :
                            trend === "down" ? "bg-red-500/10 text-red-600" :
                                "bg-gray-500/10 text-gray-600"
                    )}>
                        {trend === "up" ? "↑" : trend === "down" ? "↓" : "−"} {trendValue}
                    </span>
                )}
                <p className="text-xs text-muted-foreground">{subtext}</p>
            </div>

            {/* Background Gradient */}
            <div className={cn(
                "absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-gradient-to-br opacity-50 blur-2xl",
                colorStyles[color].split(" ")[0]
            )} />
        </div>
    );
};
