import { Check, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ProgressData {
  currentStep: number;
  completedSteps: string[];
  stepLabel: string;
}

const STEP_LABELS = [
  "Analyzing request",
  "Loading patient data",
  "Running maternal health models",
  "Running fetal health models",
  "Retrieving medical guidelines",
  "Generating assessment report",
];

export const AssessmentProgress = ({ data }: { data: ProgressData }) => {
  const completedSet = new Set(data.completedSteps ?? []);
  const pct = Math.round(
    ((data.currentStep > 0 ? data.currentStep - 1 : 0) / STEP_LABELS.length) * 100
  );

  return (
    <div className="space-y-4 py-1">
      {/* Header row */}
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-medical-pink tracking-wide">
          Processing Assessment
        </p>
        <span className="text-[11px] font-semibold tabular-nums text-medical-blue bg-medical-blue/10 px-2.5 py-0.5 rounded-full">
          {pct}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="relative h-[5px] w-full rounded-full bg-white/30 overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-medical-pink via-medical-pink-light to-medical-blue transition-all duration-700 ease-[cubic-bezier(0.4,0,0.2,1)]"
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
        {/* Shimmer overlay on the filled portion */}
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-[shimmer_2s_ease-in-out_infinite] bg-[length:200%_100%]"
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
      </div>

      {/* Step list */}
      <div className="space-y-2">
        {STEP_LABELS.map((label) => {
          const isCompleted = completedSet.has(label);
          const isActive = label === data.stepLabel && !isCompleted;

          return (
            <div
              key={label}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 transition-all duration-500",
                isActive && "bg-white/30",
              )}
            >
              {/* Status icon */}
              <div
                className={cn(
                  "flex-shrink-0 w-[22px] h-[22px] rounded-full flex items-center justify-center transition-all duration-500",
                  isCompleted &&
                    "bg-gradient-to-br from-medical-blue to-medical-blue-light shadow-glow-blue",
                  isActive &&
                    "bg-gradient-to-br from-medical-pink to-medical-blue shadow-[0_0_12px_hsl(340_45%_65%/0.4)]",
                  !isCompleted &&
                    !isActive &&
                    "border border-white/40 bg-white/10",
                )}
              >
                {isCompleted ? (
                  <Check className="h-3 w-3 text-white" strokeWidth={3} />
                ) : isActive ? (
                  <Loader2 className="h-3 w-3 text-white animate-spin" />
                ) : (
                  <Circle className="h-2 w-2 text-muted-foreground/30" />
                )}
              </div>

              {/* Label */}
              <span
                className={cn(
                  "text-[13px] leading-tight transition-all duration-300",
                  isCompleted && "text-foreground/60",
                  isActive && "text-medical-pink font-medium",
                  !isCompleted && !isActive && "text-muted-foreground/40",
                )}
              >
                {label}
                {isActive && (
                  <span className="inline-flex ml-0.5 tracking-widest animate-pulse">
                    ...
                  </span>
                )}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
