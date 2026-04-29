import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface DashboardCardProps {
  title: string;
  icon: LucideIcon;
  variant: "dual-glow" | "gradient";
  onClick?: () => void;
}

export const DashboardCard = ({ title, icon: Icon, variant, onClick }: DashboardCardProps) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        "relative group cursor-pointer overflow-hidden rounded-2xl transition-all duration-500",
        "hover:scale-[1.02] hover:-translate-y-2",
        variant === "dual-glow" && "bg-card border border-border/50 shadow-soft card-glow-hover",
        variant === "gradient" && "bg-gradient-chatbot shadow-glow-pink"
      )}
    >
      {/* Shine effect on hover */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
      </div>

      {/* Content */}
      <div className="relative z-10 p-8 flex flex-col items-center gap-6">
        {/* Icon Container */}
        <div
          className={cn(
            "relative p-5 rounded-2xl transition-all duration-500",
            "group-hover:scale-110 group-hover:rotate-3",
            variant === "dual-glow" && "bg-gradient-to-br from-medical-pink/10 to-medical-blue/10 group-hover:from-medical-pink/12 group-hover:to-medical-blue/12",
            variant === "gradient" && "bg-white/20 group-hover:bg-white/30 backdrop-blur-sm"
          )}
        >
          {/* Icon glow */}
          <div className={cn(
            "absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-20 transition-opacity duration-500 blur-xl",
            variant === "dual-glow" && "bg-gradient-to-br from-medical-pink/50 to-medical-blue/50",
            variant === "gradient" && "bg-white/40"
          )} />
          
          <Icon
            className={cn(
              "relative h-10 w-10 transition-all duration-500",
              variant === "dual-glow" && "text-primary group-hover:text-medical-pink",
              variant === "gradient" && "text-white group-hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]"
            )}
          />
        </div>

        {/* Title */}
        <h3
          className={cn(
            "text-xl font-semibold text-center transition-all duration-500",
            variant === "dual-glow" && "text-foreground group-hover:bg-gradient-to-r group-hover:from-medical-pink/80 group-hover:to-medical-blue/80 group-hover:bg-clip-text group-hover:text-transparent",
            variant === "gradient" && "text-white group-hover:drop-shadow-[0_2px_8px_rgba(255,255,255,0.3)]"
          )}
        >
          {title}
        </h3>
      </div>

      {/* Bottom gradient accent */}
      <div className={cn(
        "absolute bottom-0 left-0 right-0 h-1 opacity-0 group-hover:opacity-60 transition-opacity duration-500",
        variant === "dual-glow" && "bg-gradient-to-r from-medical-pink/60 via-medical-blue/60 to-medical-pink/60",
        variant === "gradient" && "bg-white/40"
      )} />
    </div>
  );
};
