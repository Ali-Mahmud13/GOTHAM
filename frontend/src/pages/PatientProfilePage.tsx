import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Hash, User, Phone, Calendar, FileText, Brain, AlertCircle } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { cn } from "@/lib/utils";

// Mock data - only first 3 patients have profile data
const mockPatients = [
  {
    id: 'P001',
    name: 'Sarah Johnson',
    age: '28',
    contactNumber: '+1 (555) 123-4567',
    riskLevel: 'low' as const,
    doctorNotes: 'Patient shows consistent progress with regular checkups.  Vitals are stable and within normal ranges.  Continue current treatment plan.',
    aiReport: 'Based on historical data and current health metrics, the patient demonstrates a low-risk profile.  Recommended follow-up in 3 months.  All vital signs are within acceptable parameters.  Suggest maintaining current lifestyle and medication regimen.',
  },
  {
    id: 'P002',
    name: 'Jennifer Wilson',
    age: '34',
    contactNumber: '+1 (555) 234-5678',
    riskLevel: 'high' as const,
    doctorNotes: 'Requires immediate attention.  Blood pressure elevated during last visit. Scheduled for additional tests next week.',
    aiReport: 'High-risk assessment based on recent vital readings and medical history. Elevated cardiovascular markers detected. Immediate consultation recommended. Close monitoring required for the next 2 weeks.',
  },
  {
    id: 'P003',
    name: 'Emily Davis',
    age: '26',
    contactNumber: '+1 (555) 345-6789',
    riskLevel: 'low' as const,
    doctorNotes: 'Healthy patient with no major concerns. Annual checkup completed successfully.',
    aiReport: 'Low-risk profile maintained.  All systems functioning normally. Continue preventive care routine.  Next checkup recommended in 6 months.',
  },
];

const PatientProfilePage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();

  // Find patient by ID - if not found in mock data, return null
  const patient = mockPatients.find(p => p.id === patientId);

  // If patient doesn't exist in our mock data, show message or redirect
  if (!patient) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
        <Navbar />
        <main className="container mx-auto px-6 py-10">
          <button
            onClick={() => navigate('/patients')}
            className="flex items-center gap-2 text-gray-600 hover:text-medical-blue transition-colors mb-6 group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-semibold">Back to Patients</span>
          </button>
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Patient Profile Not Available</h2>
            <p className="text-gray-600 mb-6">This patient's detailed profile has not been created yet.</p>
            <button
              onClick={() => navigate('/patients')}
              className="px-6 py-3 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-lg hover:shadow-lg transition-all"
            >
              Return to Patients List
            </button>
          </div>
        </main>
      </div>
    );
  }

  const getRiskColor = () => {
    switch (patient. riskLevel) {
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
    switch (patient.riskLevel) {
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

  const getRiskTextColor = () => {
    switch (patient.riskLevel) {
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-orange-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
      <Navbar />

      <main className="container mx-auto px-6 py-10">
        {/* Back Button */}
        <button
          onClick={() => navigate('/patients')}
          className="flex items-center gap-2 text-gray-600 hover:text-medical-blue transition-colors mb-6 group"
        >
          <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
          <span className="font-semibold">Back to Patients</span>
        </button>

        {/* Header Card - Patient Info */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 relative overflow-hidden border border-gray-100">
          {/* Decorative Background Gradient */}
          <div className="absolute top-0 right-0 w-1/3 h-full bg-gradient-to-l from-medical-pink/5 to-medical-blue/5 -z-0" />
          
          <div className="relative z-10">
            {/* Patient ID & Risk Badge */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-r from-medical-pink to-medical-blue p-3 rounded-xl">
                  <Hash className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium">Patient ID</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                    {patient.id}
                  </p>
                </div>
              </div>

              {/* Risk Level Badge */}
              <div className={cn(
                "px-6 py-3 rounded-full text-white font-bold shadow-lg flex items-center gap-2",
                getRiskColor()
              )}>
                <AlertCircle className="w-5 h-5" />
                {getRiskLabel()}
              </div>
            </div>

            {/* Patient Name */}
            <h1 className="text-4xl font-bold text-gray-900 mb-6">
              {patient.name}
            </h1>

            {/* Info Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Age */}
              <div className="flex items-center gap-3 bg-gradient-to-br from-blue-50 to-blue-100/50 p-4 rounded-xl">
                <div className="bg-blue-500 p-3 rounded-lg">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs text-gray-600 font-semibold uppercase">Age</p>
                  <p className="text-xl font-bold text-gray-900">{patient.age} years</p>
                </div>
              </div>

              {/* Phone */}
              <div className="flex items-center gap-3 bg-gradient-to-br from-purple-50 to-purple-100/50 p-4 rounded-xl">
                <div className="bg-purple-500 p-3 rounded-lg">
                  <Phone className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs text-gray-600 font-semibold uppercase">Contact</p>
                  <p className="text-sm font-bold text-gray-900">{patient.contactNumber}</p>
                </div>
              </div>

              {/* Last Updated */}
              <div className="flex items-center gap-3 bg-gradient-to-br from-pink-50 to-pink-100/50 p-4 rounded-xl">
                <div className="bg-pink-500 p-3 rounded-lg">
                  <Calendar className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs text-gray-600 font-semibold uppercase">Last Updated</p>
                  <p className="text-sm font-bold text-gray-900">Nov 26, 2025</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Two Column Layout for Notes and AI Report */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Doctor's Notes */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 hover:shadow-2xl transition-shadow">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-gradient-to-r from-blue-500 to-cyan-500 p-3 rounded-xl">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Doctor's Notes</h2>
            </div>

            <div className="bg-gradient-to-br from-blue-50/50 to-cyan-50/50 rounded-xl p-6 border-l-4 border-blue-500">
              <p className="text-gray-700 leading-relaxed">
                {patient.doctorNotes}
              </p>
            </div>

            {/* Timestamp */}
            <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>Last updated: Nov 26, 2025 at 10:30 AM</span>
            </div>
          </div>

          {/* AI Report */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 hover:shadow-2xl transition-shadow">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-gradient-to-r from-medical-pink to-medical-blue p-3 rounded-xl animate-pulse">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">AI Analysis Report</h2>
                <p className="text-sm text-gray-500">Powered by GOTHAM AI</p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-pink-50/50 to-purple-50/50 rounded-xl p-6 border-l-4 border-medical-pink">
              <p className="text-gray-700 leading-relaxed mb-4">
                {patient. aiReport}
              </p>

              {/* Risk Assessment Summary */}
              <div className={cn(
                "mt-4 p-4 rounded-lg border-2",
                patient.riskLevel === 'high' ?  'bg-red-50 border-red-200' :
                patient. riskLevel === 'medium' ? 'bg-orange-50 border-orange-200' :
                'bg-green-50 border-green-200'
              )}>
                <p className={cn("font-bold text-sm", getRiskTextColor())}>
                  ⚡ Risk Assessment: {getRiskLabel()}
                </p>
              </div>
            </div>

            {/* Timestamp */}
            <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
              <Brain className="w-4 h-4" />
              <span>Generated: Nov 26, 2025 at 10:35 AM</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default PatientProfilePage;