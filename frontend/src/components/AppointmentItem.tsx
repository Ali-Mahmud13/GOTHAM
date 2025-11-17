import { Clock } from "lucide-react";

interface AppointmentItemProps {
  patientName: string;
  time: string;
  type: string;
}

export const AppointmentItem = ({ patientName, time, type }: AppointmentItemProps) => {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-border last:border-0">
      <div className="p-2 rounded-lg bg-muted">
        <Clock className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1">
        <p className="font-medium text-foreground">{patientName}</p>
        <p className="text-sm text-muted-foreground">{type}</p>
      </div>
      <p className="text-sm font-medium text-muted-foreground">{time}</p>
    </div>
  );
};
