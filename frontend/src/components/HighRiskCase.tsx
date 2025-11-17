import { AlertTriangle } from "lucide-react";

interface HighRiskCaseProps {
  patientName: string;
  riskLevel: string;
  condition: string;
}

export const HighRiskCase = ({ patientName, riskLevel, condition }: HighRiskCaseProps) => {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-border last:border-0">
      <div className="p-2 rounded-lg bg-destructive/10">
        <AlertTriangle className="h-4 w-4 text-destructive" />
      </div>
      <div className="flex-1">
        <p className="font-medium text-foreground">{patientName}</p>
        <p className="text-sm text-muted-foreground">{condition}</p>
      </div>
      <span className="px-3 py-1 rounded-full bg-destructive/10 text-destructive text-xs font-semibold">
        {riskLevel}
      </span>
    </div>
  );
};
