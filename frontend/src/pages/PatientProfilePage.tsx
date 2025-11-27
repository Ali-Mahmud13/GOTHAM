import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { ArrowLeft, Hash, User, Phone, Calendar, FileText, Brain, AlertCircle, Activity } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { VitalsChart } from "@/components/charts/VitalsChart";
import { cn } from "@/lib/utils";

const API_URL = "http://localhost:8000";

interface PatientProfile {
  id: number;
  patient_identifier: string;
  name: string;
  age: number;
  contact_number: string;
  doctor_notes: string | null;
  ai_report: string | null;
  risk_level: 'high' | 'medium' | 'low';
  created_at: string;
  updated_at: string;
}

interface PatientMedical {
  id: number;
  patient_identifier: string;
  family_history: boolean | null;
  pcos: boolean | null;
  unexplained_prenatal_loss: boolean | null;
  large_child_or_birth_default: boolean | null;
  prediabetes: boolean | null;
}

const PatientProfilePage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [medicalData, setMedicalData] = useState<PatientMedical | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPatientData();
  }, [patientId]);

  const fetchPatientData = async () => {
    try {
      setLoading(true);
      
      // Fetch patient profile
      const profileResponse = await fetch(`${API_URL}/api/patient-profiles/${patientId}`);
      if (profileResponse.status === 404) {
        setPatient(null);
        setError("not_found");
        return;
      }
      if (!profileResponse.ok) {
        throw new Error('Failed to fetch patient profile');
      }
      const profileData = await profileResponse.json();
      setPatient(profileData);

      // Fetch medical data
      const medicalResponse = await fetch(`${API_URL}/api/patients/${patientId}`);
      if (medicalResponse.ok) {
        const medicalDataResponse = await medicalResponse.json();
        setMedicalData(medicalDataResponse);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching patient data:', err);
      setError('error');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel: string) => {
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

  const getRiskLabel = (riskLevel: string) => {
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

  const getRiskTextColor = (riskLevel: string) => {
    switch (riskLevel) {
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Loading state
  if (loading) {
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
          <div className="text-center text-lg">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent rounded-full text-medical-blue mb-4" />
            <p>Loading patient profile...</p>
          </div>
        </main>
      </div>
    );
  }

  // If patient doesn't exist in database
  if (error === "not_found" || !patient) {
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

  // Error state
  if (error === 'error') {
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
          <div className="text-center text-red-500">
            <p>Failed to load patient profile.  Please try again.</p>
            <button 
              onClick={fetchPatientData}
              className="mt-4 px-6 py-2 bg-medical-blue text-white rounded-lg hover:bg-medical-blue/90"
            >
              Retry
            </button>
          </div>
        </main>
      </div>
    );
  }

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
                    {patient.patient_identifier}
                  </p>
                </div>
              </div>

              {/* Risk Level Badge */}
              <div className={cn(
                "px-6 py-3 rounded-full text-white font-bold shadow-lg flex items-center gap-2",
                getRiskColor(patient.risk_level)
              )}>
                <AlertCircle className="w-5 h-5" />
                {getRiskLabel(patient.risk_level)}
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
                  <p className="text-sm font-bold text-gray-900">{patient.contact_number}</p>
                </div>
              </div>

              {/* Last Updated */}
              <div className="flex items-center gap-3 bg-gradient-to-br from-pink-50 to-pink-100/50 p-4 rounded-xl">
                <div className="bg-pink-500 p-3 rounded-lg">
                  <Calendar className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs text-gray-600 font-semibold uppercase">Last Updated</p>
                  <p className="text-sm font-bold text-gray-900">{formatDate(patient.updated_at)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Vitals Chart Section - ONLY THIS CHART */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-r from-purple-500 to-indigo-500 p-3 rounded-xl">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Vitals Tracking</h2>
              <p className="text-sm text-gray-500">Monitor key health metrics over time</p>
            </div>
          </div>
          <VitalsChart />
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
                {patient.doctor_notes || "No doctor notes available yet. "}
              </p>
            </div>

            {/* Timestamp */}
            <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>Last updated: {formatDate(patient.updated_at)}</span>
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
                {patient. ai_report || "AI analysis report will be generated soon."}
              </p>

              {/* Risk Assessment Summary */}
              <div className={cn(
                "mt-4 p-4 rounded-lg border-2",
                patient.risk_level === 'high' ?    'bg-red-50 border-red-200' :
                patient. risk_level === 'medium' ? 'bg-orange-50 border-orange-200' :
                'bg-green-50 border-green-200'
              )}>
                <p className={cn("font-bold text-sm", getRiskTextColor(patient. risk_level))}>
                  ⚡ Risk Assessment: {getRiskLabel(patient.risk_level)}
                </p>
              </div>
            </div>

            {/* Timestamp */}
            <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
              <Brain className="w-4 h-4" />
              <span>Generated: {formatDate(patient.created_at)}</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default PatientProfilePage;