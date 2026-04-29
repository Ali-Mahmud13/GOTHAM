import { ReactNode } from "react";

interface SummaryPanelProps {
  title: string;
  children: ReactNode;
  gradient?: "pink" | "blue" | "neutral";
  onViewAll?: () => void;
}

export const SummaryPanel = ({ title, children, gradient = "neutral", onViewAll }: SummaryPanelProps) => {
  const gradientClasses = {
    pink: "from-medical-pink/5 to-transparent",
    blue: "from-medical-blue/5 to-transparent",
    neutral: "from-muted/50 to-transparent",
  };

  return (
    <div className="group relative bg-card rounded-2xl p-6 shadow-soft border border-border/50 hover:border-border transition-all duration-500 hover:shadow-lg overflow-hidden">
      {/* Gradient overlay */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradientClasses[gradient]} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
      
      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-center justify-between gap-2 mb-4">
          <div className="flex items-center gap-2">
            <div className={`h-1 w-8 rounded-full bg-gradient-to-r ${gradient === "pink" ? "from-medical-pink to-medical-pink-light" : gradient === "blue" ? "from-medical-blue to-medical-blue-light" : "from-muted-foreground to-muted"}`} />
            <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          </div>
          {onViewAll && (
            <button onClick={onViewAll} className="text-xs text-medical-blue hover:underline font-medium">
              View all
            </button>
          )}
        </div>
        {children}
      </div>
    </div>
  );
};
