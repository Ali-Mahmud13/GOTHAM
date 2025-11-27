import { useNavigate } from "react-router-dom";
import { Phone, User, Hash, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface PatientCardProps {
  id: string;
  name: string;
  age: string;
  contactNumber: string;
  riskLevel: 'high' | 'medium' | 'low';
}

export const PatientCard = ({ id, name, age, contactNumber, riskLevel }: PatientCardProps) => {
  const navigate = useNavigate();

  const getRiskConfig = () => {
    switch (riskLevel) {
      case 'high':
        return {
          color: 'from-rose-500 via-pink-500 to-red-500',
          bgColor: 'bg-rose-500',
          textColor: 'text-rose-600',
          glowColor: 'shadow-rose-500/50',
          label: 'High Risk',
          pulseAnimation: true,
        };
      case 'medium':
        return {
          color: 'from-purple-500 via-violet-500 to-purple-600',
          bgColor: 'bg-purple-500',
          textColor: 'text-purple-600',
          glowColor: 'shadow-purple-500/50',
          label: 'Medium Risk',
          pulseAnimation: false,
        };
      case 'low':
        return {
          color: 'from-cyan-500 via-blue-500 to-teal-500',
          bgColor: 'bg-cyan-500',
          textColor: 'text-cyan-600',
          glowColor: 'shadow-cyan-500/50',
          label: 'Low Risk',
          pulseAnimation: false,
        };
      default:
        return {
          color: 'from-gray-400 to-gray-500',
          bgColor: 'bg-gray-400',
          textColor: 'text-gray-600',
          glowColor: 'shadow-gray-500/50',
          label: 'Unknown',
          pulseAnimation: false,
        };
    }
  };

  const riskConfig = getRiskConfig();

  const handleClick = () => {
    navigate(`/patients/${id}`);
  };

  return (
    <div
      onClick={handleClick}
      className="group relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-md hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 cursor-pointer border border-gray-200/50 overflow-hidden"
    >
      {/* Gradient Border Glow Effect */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-r from-medical-pink via-medical-blue to-medical-pink p-[2px] -z-10">
        <div className="absolute inset-[2px] bg-white rounded-2xl" />
      </div>

      {/* Background Gradient Overlay on Hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-medical-pink/5 via-transparent to-medical-blue/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Card Content */}
      <div className="relative p-6">
        {/* Patient Avatar with Gradient */}
        <div className="flex items-start justify-between mb-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue p-[3px] shadow-lg">
              <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                <User className="w-8 h-8 text-medical-blue" />
              </div>
            </div>
            {/* Online Status Indicator */}
            <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 rounded-full border-2 border-white shadow-sm" />
          </div>

          {/* Risk Badge */}
          <div className={cn(
            "relative px-3 py-1.5 rounded-full text-xs font-bold text-white shadow-lg",
            `bg-gradient-to-r ${riskConfig.color}`,
            riskConfig.pulseAnimation && "animate-pulse"
          )}>
            <div className={cn(
              "absolute inset-0 rounded-full blur-md opacity-60",
              riskConfig.bgColor
            )} />
            <div className="relative flex items-center gap-1.5">
              <Activity className="w-3 h-3" />
              {riskConfig.label}
            </div>
          </div>
        </div>

        {/* Patient ID */}
        <div className="flex items-center gap-1.5 mb-2">
          <Hash className="w-3.5 h-3.5 text-medical-blue/70" />
          <span className="text-xs font-semibold text-medical-blue/70 tracking-wide">{id}</span>
        </div>

        {/* Patient Name */}
        <h3 className="text-xl font-bold text-gray-900 mb-4 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-medical-pink group-hover:to-medical-blue group-hover:bg-clip-text transition-all duration-300">
          {name}
        </h3>

        {/* Divider */}
        <div className="h-[2px] bg-gradient-to-r from-transparent via-gray-200 to-transparent mb-4 group-hover:via-medical-blue/30 transition-colors duration-500" />

        {/* Patient Details */}
        <div className="space-y-3">
          {/* Age */}
          <div className="flex items-center gap-3 text-sm text-gray-600 group-hover:text-gray-900 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-100 to-blue-50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <User className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Age</p>
              <p className="font-semibold">{age} years old</p>
            </div>
          </div>

          {/* Contact Number */}
          <div className="flex items-center gap-3 text-sm text-gray-600 group-hover:text-gray-900 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-100 to-purple-50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <Phone className="w-4 h-4 text-purple-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Contact</p>
              <p className="font-semibold">{contactNumber}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Hover Glow Effect at Bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-medical-pink via-medical-blue to-medical-pink transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-center" />

      {/* Card Glow on Hover */}
      <div className={cn(
        "absolute inset-0 -z-20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl",
        "bg-gradient-to-r from-medical-pink/20 to-medical-blue/20"
      )} />
    </div>
  );
};