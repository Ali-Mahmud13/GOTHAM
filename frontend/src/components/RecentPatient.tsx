import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface RecentPatientProps {
  name: string;
  avatar?: string;
  lastVisit: string;
}

export const RecentPatient = ({ name, avatar, lastVisit }: RecentPatientProps) => {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  return (
    <div className="flex items-center gap-3 py-3 border-b border-border last:border-0">
      <Avatar className="h-10 w-10">
        <AvatarImage src={avatar} alt={name} />
        <AvatarFallback className="bg-medical-pink text-white">{initials}</AvatarFallback>
      </Avatar>
      <div className="flex-1">
        <p className="font-medium text-foreground">{name}</p>
        <p className="text-sm text-muted-foreground">{lastVisit}</p>
      </div>
    </div>
  );
};
