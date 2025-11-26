import { useNavigate } from "react-router-dom";
import { Phone, User, Hash } from "lucide-react";
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

  const getRiskColor = () => {
    switch (riskLevel) {
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-orange-500';
      case 'low':
        return 'bg-green-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getRiskLabel = () => {
    switch (riskLevel) {
      case 'high':
        return 'High Risk';
      case 'medium':
        return 'Medium Risk';
      case 'low':
        return 'Low Risk';
      default:
        return 'Unknown';
    }
  };

  const handleClick = () => {
    navigate(`/patients/${id}`);
  };

  return (
    <div 
      onClick={handleClick}
      className="group relative bg-white shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer border border-gray-100"
      style={{
        clipPath: 'polygon(15% 0%, 85% 0%, 100% 8%, 100% 92%, 92% 100%, 8% 100%, 0% 92%, 0% 8%)'
      }}
    >
      {/* Dropdown Tag - Mid-length, elegant */}
      <div className="absolute top-0 left-0 right-0 z-10 overflow-hidden flex justify-center">
        <div 
          className={cn(
            "relative w-[70%] px-4 py-2 text-xs font-semibold text-white shadow-md flex items-center justify-center gap-2",
            getRiskColor()
          )}
          style={{
            clipPath: 'polygon(0% 0%, 100% 0%, 85% 100%, 15% 100%)'
          }}
        >
          <span className="w-1. 5 h-1.5 rounded-full bg-white/90" />
          {getRiskLabel()}
        </div>
      </div>

      {/* Card Content */}
      <div className="p-6 pt-11">
        {/* Patient ID */}
        <div className="flex items-center gap-1. 5 mb-2">
          <Hash className="w-3. 5 h-3.5 text-medical-blue" />
          <span className="text-xs font-semibold text-medical-blue">{id}</span>
        </div>

        {/* Patient Name */}
        <h3 className="text-lg font-semibold text-gray-900 mb-3 group-hover:text-medical-blue transition-colors">
          {name}
        </h3>

        {/* Age */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <User className="w-4 h-4" />
          <span>{age} years old</span>
        </div>

        {/* Contact Number */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Phone className="w-4 h-4" />
          <span>{contactNumber}</span>
        </div>
      </div>

      {/* Hover Glow Effect */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
        <div 
          className="absolute inset-0 bg-gradient-to-br from-medical-pink/5 to-medical-blue/5"
          style={{
            clipPath: 'polygon(15% 0%, 85% 0%, 100% 8%, 100% 92%, 92% 100%, 8% 100%, 0% 92%, 0% 8%)'
          }}
        />
      </div>
    </div>
  );
};