import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft, Hash, User, Phone, Calendar, FileText, Brain, AlertCircle,
  Activity, TrendingUp, Clock, Heart, ChevronRight,
  Stethoscope, Clipboard, BarChart3, Zap, CheckCircle2, XCircle, MinusCircle, X, Save, UserX
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { VitalsChart } from "@/components/charts/VitalsChart";
import { VisitTimeline } from "@/components/patient/VisitTimeline";
import { BatEasterEgg } from "@/components/BatEasterEgg";
import { cn } from "@/lib/utils";

const API_URL = "http://localhost:8000";

interface PatientProfile {
  id: number;
  patient_identifier: string;
  name: string;
  age: number;
  contact_number: string;
  clinical_notes: string | null;
  risk_level: 'high' | 'medium' | 'low';
  number_of_pregnancies: number | null;
  family_history: boolean | null;
  pcos: boolean | null;
  unexplained_prenatal_loss: boolean | null;
  large_child_or_birth_default: boolean | null;
  prediabetes: boolean | null;
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

type TabType = 'overview' | 'medical' | 'notes' | 'ai' | 'visits' | 'vitals';

const PatientProfilePage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [medicalData, setMedicalData] = useState<PatientMedical | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [visitStats, setVisitStats] = useState<{ total_visits: number; recent_visits: any[] }>({ total_visits: 0, recent_visits: [] });
  const [visits, setVisits] = useState<any[]>([]);
  const [showBats, setShowBats] = useState(false);
  const [keySequence, setKeySequence] = useState('');
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [editedNotes, setEditedNotes] = useState('');
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const [registeredPatientAuthId, setRegisteredPatientAuthId] = useState<number | null>(null);
  const [showUnregisterConfirm, setShowUnregisterConfirm] = useState(false);
  const [isUnregistering, setIsUnregistering] = useState(false);

  useEffect(() => {
    fetchPatientData();
  }, [patientId]);

  useEffect(() => {
    if (user?.email && patientId) {
      fetch(`${API_URL}/appointments/my-registered-patients`, {
        headers: { 'X-User-Email': user.email },
      })
        .then(r => r.ok ? r.json() : [])
        .then((list: { patient_auth_id: number; patient_identifier: string }[]) => {
          const match = list.find(p => p.patient_identifier === patientId);
          setRegisteredPatientAuthId(match ? match.patient_auth_id : null);
        })
        .catch(() => {});
    }
  }, [user?.email, patientId]);

  const handleUnregister = async () => {
    if (!registeredPatientAuthId || !user?.email) return;
    setIsUnregistering(true);
    try {
      const res = await fetch(`${API_URL}/appointments/unregister/${registeredPatientAuthId}`, {
        method: 'DELETE',
        headers: { 'X-User-Email': user.email },
      });
      if (res.ok) {
        setRegisteredPatientAuthId(null);
        setShowUnregisterConfirm(false);
      }
    } catch { } finally { setIsUnregistering(false); }
  };

  // Easter egg keyboard listener
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only track alphanumeric keys
      if (e.key.length === 1 && /[a-zA-Z0-9]/.test(e.key)) {
        setKeySequence(prev => {
          const newSequence = (prev + e.key.toLowerCase()).slice(-5);
          console.log('Key sequence:', newSequence, 'Risk level:', patient?.risk_level);

          // Check if the sequence matches "eza13" and patient is high risk
          if (newSequence === 'eza13' && patient?.risk_level === 'high') {
            console.log('Easter egg triggered! Showing bats...');
            setShowBats(true);
            return ''; // Reset sequence
          }

          return newSequence;
        });
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [patient?.risk_level]);

  const handleEditNotes = () => {
    setEditedNotes(patient?.clinical_notes || '');
    setIsEditingNotes(true);
  };

  const handleSaveNotes = async () => {
    if (!patient) return;

    setIsSavingNotes(true);
    try {
      const response = await fetch(`${API_URL}/api/patients/${patientId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clinical_notes: editedNotes,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save clinical notes');
      }

      const updatedPatient = await response.json();
      setPatient(updatedPatient);
      setIsEditingNotes(false);

      // Show success toast (you can add a toast library later)
      console.log('Clinical notes saved successfully');
    } catch (err) {
      console.error('Error saving clinical notes:', err);
      alert('Failed to save clinical notes. Please try again.');
    } finally {
      setIsSavingNotes(false);
    }
  };

  const fetchPatientData = async () => {
    try {
      // Fetch patient data (merged schema - single endpoint)
      const profileResponse = await fetch(`${API_URL}/api/patients/${patientId}`);
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
      setMedicalData(profileData);  // Medical data is in the same object now

      // Fetch visit statistics
      const visitsResponse = await fetch(`${API_URL}/api/dashboard/patient/${patientId}/visits`);
      if (visitsResponse.ok) {
        const visitsData = await visitsResponse.json();
        setVisitStats(visitsData);
        setVisits(visitsData.recent_visits || []);
      }

      setError(null);
    } catch (err) {
      console.error('Error fetching patient data:', err);
      setError('error');
    } finally {
      setLoading(false);
    }
  };

  const getRiskConfig = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high':
        return {
          bgColor: 'from-rose-500 via-pink-500 to-red-500',
          textColor: 'text-rose-600',
          ringColor: 'stroke-rose-500',
          label: 'High Risk',
          score: 85,
        };
      case 'medium':
        return {
          bgColor: 'from-purple-500 via-violet-500 to-purple-600',
          textColor: 'text-purple-600',
          ringColor: 'stroke-purple-500',
          label: 'Medium Risk',
          score: 55,
        };
      case 'low':
        return {
          bgColor: 'from-cyan-500 via-blue-500 to-teal-500',
          textColor: 'text-cyan-600',
          ringColor: 'stroke-cyan-500',
          label: 'Low Risk',
          score: 25,
        };
      default:
        return {
          bgColor: 'from-gray-400 to-gray-500',
          textColor: 'text-gray-600',
          ringColor: 'stroke-gray-400',
          label: 'Unknown',
          score: 0,
        };
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
        <Navbar />
        <main className="container mx-auto px-6 py-10">
          <div className="text-center text-lg">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent rounded-full text-medical-blue mb-4" />
            <p>Loading patient profile...</p>
          </div>
        </main>
      </div>
    );
  }

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
            <p>Failed to load patient profile. Please try again.</p>
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

  const riskConfig = getRiskConfig(patient.risk_level);

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: BarChart3 },
    { id: 'medical' as TabType, label: 'Medical History', icon: Stethoscope },
    { id: 'visits' as TabType, label: 'Visit History', icon: Clock },
    { id: 'notes' as TabType, label: 'Dr Notes', icon: Clipboard },
    { id: 'ai' as TabType, label: 'AI Analysis', icon: Brain },
    { id: 'vitals' as TabType, label: 'Vitals', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/20 to-pink-50/20">
      <Navbar />

      {/* Hero Header Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50/30 to-pink-50/30 border-b border-gray-200">
        <div className="container mx-auto px-6 py-6 relative z-10">
          {/* Back Button */}
          <button
            onClick={() => navigate('/patients')}
            className="flex items-center gap-2 text-gray-600 hover:text-medical-blue transition-colors mb-6 group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="text-sm font-medium">Back to Patients</span>
          </button>

          {/* Hero Content */}
          <div className="flex items-center justify-between">
            {/* Left: Patient Info */}
            <div className="flex items-center gap-6">
              {/* Large Avatar with Health Ring */}
              <div className="relative">
                {/* Health Score Ring */}
                <svg className="w-32 h-32" viewBox="0 0 128 128">
                  {/* Background circle */}
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="6"
                  />
                  {/* Progress circle */}
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    fill="none"
                    className={riskConfig.ringColor}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 56}`}
                    strokeDashoffset={`${2 * Math.PI * 56 * (1 - riskConfig.score / 100)}`}
                    transform="rotate(-90 64 64)"
                    style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
                  />
                </svg>

                {/* Avatar in center */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue p-0.5 shadow-xl">
                    <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                      <User className="w-10 h-10 text-gray-700" />
                    </div>
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-3 border-white shadow-md flex items-center justify-center">
                    <Heart className="w-3 h-3 text-white" />
                  </div>
                </div>
              </div>

              {/* Patient Details */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-gray-500 tracking-wide">{patient.patient_identifier}</span>
                  <div className={cn(
                    "px-3 py-1 rounded-full text-xs font-bold text-white",
                    `bg-gradient-to-r ${riskConfig.bgColor}`,
                    patient.risk_level === 'high' && "animate-pulse"
                  )}>
                    {riskConfig.label}
                  </div>
                </div>

                <h1 className="text-4xl font-bold text-gray-900 mb-3">
                  {patient.name}
                </h1>

                <div className="flex items-center gap-4 text-gray-600 text-sm">
                  <div className="flex items-center gap-1.5">
                    <User className="w-4 h-4" />
                    <span>{patient.age} years</span>
                  </div>
                  <span className="text-gray-300">•</span>
                  <div className="flex items-center gap-1.5">
                    <Phone className="w-4 h-4" />
                    <span>{patient.contact_number}</span>
                  </div>
                  <span className="text-gray-300">•</span>
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4" />
                    <span className="text-xs">Updated {formatDate(patient.updated_at)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Quick Actions */}
            <div className="flex items-center gap-2">
              {registeredPatientAuthId !== null && (
                <button
                  onClick={() => setShowUnregisterConfirm(true)}
                  className="px-4 py-2 bg-white border border-red-300 text-red-600 text-sm font-medium rounded-lg hover:bg-red-50 hover:border-red-500 transition-all flex items-center gap-2"
                >
                  <UserX className="w-4 h-4" />
                  Unregister Patient
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="bg-white/90 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="container mx-auto px-6">
          <div className="flex items-center gap-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "relative px-6 py-4 font-semibold transition-all duration-300 flex items-center gap-2 group",
                    isActive
                      ? "text-medical-blue"
                      : "text-gray-600 hover:text-gray-900"
                  )}
                >
                  <Icon className={cn(
                    "w-5 h-5 transition-transform",
                    isActive && "scale-110"
                  )} />
                  <span>{tab.label}</span>

                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-medical-pink to-medical-blue rounded-t-full" />
                  )}

                  {/* Hover effect */}
                  {!isActive && (
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-300 rounded-t-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <main className="container mx-auto px-6 py-10">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Health Score */}
              <div className="group relative bg-gradient-to-br from-medical-pink/5 to-rose-50/50 p-6 rounded-2xl border border-medical-pink/20 hover:shadow-xl transition-all duration-300 overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-medical-pink/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-medical-pink to-rose-400 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <Heart className="w-6 h-6 text-white" />
                    </div>
                    <TrendingUp className="w-5 h-5 text-medical-pink" />
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Health Score</p>
                  <p className="text-4xl font-bold text-gray-900 mb-2">{riskConfig.score}</p>
                  <p className="text-xs text-medical-pink font-semibold">Risk: {patient?.risk_level || 'N/A'}</p>
                </div>
              </div>

              {/* Total Visits */}
              <div className="group relative bg-gradient-to-br from-medical-blue/5 to-cyan-50/50 p-6 rounded-2xl border border-medical-blue/20 hover:shadow-xl transition-all duration-300 overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-medical-blue/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-medical-blue to-cyan-400 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <Stethoscope className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Total Visits</p>
                  <p className="text-4xl font-bold text-gray-900 mb-2">{visitStats.total_visits}</p>
                  <p className="text-xs text-gray-500 font-semibold">
                    {visitStats.recent_visits[0]
                      ? `Last visit: ${new Date(visitStats.recent_visits[0].visit_date).toLocaleDateString()}`
                      : 'No visits yet'}
                  </p>
                </div>
              </div>

              {/* Risk Factors */}
              <div className="group relative bg-gradient-to-br from-purple-50 to-violet-50 p-6 rounded-2xl border border-purple-200/50 hover:shadow-xl transition-all duration-300 overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-violet-500/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-violet-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <AlertCircle className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Risk Factors</p>
                  <p className="text-4xl font-bold text-gray-900 mb-2">{medicalData ? [medicalData.family_history, medicalData.pcos, medicalData.prediabetes].filter(Boolean).length : 0}</p>
                  <p className="text-xs text-gray-500 font-semibold">Active conditions</p>
                </div>
              </div>

              {/* AI Confidence */}
              <div className="group relative bg-gradient-to-br from-emerald-50 to-teal-50 p-6 rounded-2xl border border-emerald-200/50 hover:shadow-xl transition-all duration-300 overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <Zap className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">AI Confidence</p>
                  <p className="text-4xl font-bold text-gray-900 mb-2">94%</p>
                  <p className="text-xs text-gray-500 font-semibold">High accuracy</p>
                </div>
              </div>
            </div>

            {/* Quick Summary Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Activity */}
              <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-gray-200/50">
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-medical-blue" />
                  Recent Activity
                </h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl">
                    <div className="w-2 h-2 bg-medical-blue rounded-full mt-2" />
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-gray-900">Profile Updated</p>
                      <p className="text-xs text-gray-600">{formatDate(patient.updated_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 bg-pink-50 rounded-xl">
                    <div className="w-2 h-2 bg-medical-pink rounded-full mt-2" />
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-gray-900">AI Analysis Completed</p>
                      <p className="text-xs text-gray-600">{formatDate(patient.created_at)}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Info */}
              <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-gray-200/50">
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-medical-pink" />
                  Quick Info
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <span className="text-sm font-semibold text-gray-600">Patient ID</span>
                    <span className="text-sm font-bold text-gray-900">{patient.patient_identifier}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <span className="text-sm font-semibold text-gray-600">Risk Level</span>
                    <span className={cn("text-sm font-bold", riskConfig.textColor)}>{riskConfig.label}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <span className="text-sm font-semibold text-gray-600">Contact</span>
                    <span className="text-sm font-bold text-gray-900">{patient.contact_number}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Medical History Tab */}
        {activeTab === 'medical' && medicalData && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Medical History</h2>
              <p className="text-gray-600">Comprehensive overview of patient's medical conditions and risk factors</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Family History */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                medicalData.family_history
                  ? "bg-gradient-to-br from-pink-50 to-rose-50 border-medical-pink/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    medicalData.family_history
                      ? "bg-gradient-to-br from-medical-pink to-pink-600"
                      : "bg-gray-200"
                  )}>
                    <User className="w-7 h-7 text-white" />
                  </div>
                  {medicalData.family_history ? (
                    <CheckCircle2 className="w-8 h-8 text-medical-pink" />
                  ) : (
                    <MinusCircle className="w-8 h-8 text-gray-400" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Family History</h3>
                <p className="text-sm text-gray-600 mb-4">Genetic predisposition to conditions</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  medicalData.family_history
                    ? "bg-pink-100 text-pink-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {medicalData.family_history ? "Present" : "Not Reported"}
                </div>
              </div>

              {/* PCOS */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                medicalData.pcos
                  ? "bg-gradient-to-br from-blue-50 to-cyan-50 border-medical-blue/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    medicalData.pcos
                      ? "bg-gradient-to-br from-medical-blue to-blue-600"
                      : "bg-gray-200"
                  )}>
                    <Activity className="w-7 h-7 text-white" />
                  </div>
                  {medicalData.pcos ? (
                    <CheckCircle2 className="w-8 h-8 text-medical-blue" />
                  ) : (
                    <MinusCircle className="w-8 h-8 text-gray-400" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">PCOS</h3>
                <p className="text-sm text-gray-600 mb-4">Polycystic ovary syndrome</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  medicalData.pcos
                    ? "bg-blue-100 text-blue-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {medicalData.pcos ? "Diagnosed" : "Not Reported"}
                </div>
              </div>

              {/* Prenatal Loss */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                medicalData.unexplained_prenatal_loss
                  ? "bg-gradient-to-br from-purple-50 to-violet-50 border-purple-300/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    medicalData.unexplained_prenatal_loss
                      ? "bg-gradient-to-br from-purple-500 to-violet-500"
                      : "bg-gray-200"
                  )}>
                    <Heart className="w-7 h-7 text-white" />
                  </div>
                  {medicalData.unexplained_prenatal_loss ? (
                    <CheckCircle2 className="w-8 h-8 text-purple-600" />
                  ) : (
                    <MinusCircle className="w-8 h-8 text-gray-400" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Prenatal Loss</h3>
                <p className="text-sm text-gray-600 mb-4">Unexplained prenatal loss history</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  medicalData.unexplained_prenatal_loss
                    ? "bg-purple-100 text-purple-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {medicalData.unexplained_prenatal_loss ? "History Present" : "No History"}
                </div>
              </div>

              {/* Large Child/Birth */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                medicalData.large_child_or_birth_default
                  ? "bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-300/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    medicalData.large_child_or_birth_default
                      ? "bg-gradient-to-br from-indigo-500 to-blue-500"
                      : "bg-gray-200"
                  )}>
                    <User className="w-7 h-7 text-white" />
                  </div>
                  {medicalData.large_child_or_birth_default ? (
                    <CheckCircle2 className="w-8 h-8 text-indigo-600" />
                  ) : (
                    <MinusCircle className="w-8 h-8 text-gray-400" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Large Birth</h3>
                <p className="text-sm text-gray-600 mb-4">Large child or birth complications</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  medicalData.large_child_or_birth_default
                    ? "bg-indigo-100 text-indigo-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {medicalData.large_child_or_birth_default ? "Reported" : "Not Reported"}
                </div>
              </div>

              {/* Prediabetes */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                medicalData.prediabetes
                  ? "bg-gradient-to-br from-rose-50 to-pink-50 border-rose-300/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    medicalData.prediabetes
                      ? "bg-gradient-to-br from-rose-500 to-pink-500"
                      : "bg-gray-200"
                  )}>
                    <Activity className="w-7 h-7 text-white" />
                  </div>
                  {medicalData.prediabetes ? (
                    <CheckCircle2 className="w-8 h-8 text-rose-600" />
                  ) : (
                    <MinusCircle className="w-8 h-8 text-gray-400" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Prediabetes</h3>
                <p className="text-sm text-gray-600 mb-4">Elevated blood sugar levels</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  medicalData.prediabetes
                    ? "bg-rose-100 text-rose-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {medicalData.prediabetes ? "Diagnosed" : "Not Reported"}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Clinical Notes Tab */}
        {activeTab === 'notes' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl p-8 border border-gray-200/50">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg">
                    <Clipboard className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">Dr Notes</h2>
                    <p className="text-sm text-gray-600">Doctor's observations and clinical notes</p>
                  </div>
                </div>
                <button
                  onClick={handleEditNotes}
                  className="px-5 py-2.5 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-xl hover:shadow-lg hover:scale-105 transition-all flex items-center gap-2"
                >
                  <Edit className="w-4 h-4" />
                  Edit Notes
                </button>
              </div>

              <div className="bg-gradient-to-br from-blue-50/70 to-cyan-50/70 rounded-2xl p-8 border-l-4 border-blue-500 min-h-[300px]">
                <p className="text-gray-700 leading-relaxed text-lg whitespace-pre-wrap">
                  {patient.clinical_notes || "No clinical notes have been added yet. Click 'Edit Notes' to add observations and recommendations."}
                </p>
              </div>

              <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>Last updated: {formatDate(patient.updated_at)}</span>
              </div>
            </div>
          </div>
        )}

        {/* AI Analysis Tab */}
        {activeTab === 'ai' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl p-8 border border-gray-200/50">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 bg-gradient-to-br from-medical-pink to-medical-blue rounded-2xl flex items-center justify-center shadow-lg animate-glow-pulse">
                    <Brain className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">AI Analysis Report</h2>
                    <p className="text-sm text-gray-600">Powered by GOTHAM AI Engine</p>
                  </div>
                </div>
                <button className="px-5 py-2.5 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-xl hover:shadow-lg hover:scale-105 transition-all flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Regenerate
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Risk Score Card */}
                <div className="col-span-1 bg-gradient-to-br from-purple-50 to-violet-50 rounded-2xl p-6 border-2 border-purple-200">
                  <h3 className="text-sm font-semibold text-purple-600 mb-4 uppercase tracking-wide">Risk Assessment</h3>
                  <div className="flex items-center justify-center mb-4">
                    <div className="relative w-32 h-32">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="64"
                          cy="64"
                          r="56"
                          fill="none"
                          stroke="#e5e7eb"
                          strokeWidth="8"
                        />
                        <circle
                          cx="64"
                          cy="64"
                          r="56"
                          fill="none"
                          className={riskConfig.ringColor}
                          strokeWidth="8"
                          strokeLinecap="round"
                          strokeDasharray={`${2 * Math.PI * 56}`}
                          strokeDashoffset={`${2 * Math.PI * 56 * (1 - riskConfig.score / 100)}`}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-3xl font-bold text-gray-900">{riskConfig.score}</span>
                      </div>
                    </div>
                  </div>
                  <p className={cn("text-center font-bold text-lg", riskConfig.textColor)}>{riskConfig.label}</p>
                </div>

                {/* AI Insights */}
                <div className="col-span-2 bg-gradient-to-br from-pink-50/70 to-purple-50/70 rounded-2xl p-6 border-l-4 border-medical-pink">
                  <h3 className="text-sm font-semibold text-purple-600 mb-4 uppercase tracking-wide">AI Generated Insights</h3>
                  <p className="text-gray-700 leading-relaxed text-lg mb-4">
                    {patient.clinical_notes || "AI analysis is being processed. This comprehensive report will include risk assessments, recommendations, and personalized care suggestions based on the patient's medical history and current health indicators."}
                  </p>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Brain className="w-4 h-4" />
                    <span>Confidence Level: 94%</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Calendar className="w-4 h-4" />
                <span>Generated: {formatDate(patient.created_at)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Visit History Tab */}
        {activeTab === 'visits' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <VisitTimeline visits={visits} />
          </div>
        )}

        {/* Vitals Tab */}
        {activeTab === 'vitals' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-card/60 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-border/30">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-gradient-to-br from-medical-pink to-medical-blue">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-foreground">Vitals Tracking</h2>
                  <p className="text-sm text-muted-foreground">Monitor key health metrics over time</p>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-gradient-to-br from-medical-pink/10 to-rose-50/50 p-4 rounded-xl border border-medical-pink/20">
                  <p className="text-xs font-semibold text-medical-pink mb-1">AVG HEART RATE</p>
                  <p className="text-2xl font-bold text-foreground">72 <span className="text-sm font-normal text-muted-foreground">bpm</span></p>
                </div>
                <div className="bg-gradient-to-br from-medical-blue/10 to-cyan-50/50 p-4 rounded-xl border border-medical-blue/20">
                  <p className="text-xs font-semibold text-medical-blue mb-1">AVG BLOOD PRESSURE</p>
                  <p className="text-2xl font-bold text-foreground">120/80 <span className="text-sm font-normal text-muted-foreground">mmHg</span></p>
                </div>
                <div className="bg-gradient-to-br from-cyan-50 to-teal-50 p-4 rounded-xl border border-cyan-200">
                  <p className="text-xs font-semibold text-cyan-600 mb-1">AVG TEMPERATURE</p>
                  <p className="text-2xl font-bold text-foreground">98.6 <span className="text-sm font-normal text-muted-foreground">°F</span></p>
                </div>
                <div className="bg-gradient-to-br from-medical-pink/10 to-medical-blue/10 p-4 rounded-xl border border-medical-blue/20">
                  <p className="text-xs font-semibold text-medical-blue mb-1">AVG OXYGEN</p>
                  <p className="text-2xl font-bold text-foreground">98 <span className="text-sm font-normal text-muted-foreground">%</span></p>
                </div>
              </div>

              <VitalsChart />
            </div>
          </div>
        )}
      </main>

      {/* Clinical Notes Edit Modal */}
      {isEditingNotes && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-300">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-medical-blue to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
                  <Clipboard className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Edit Dr Notes</h2>
                  <p className="text-sm text-gray-600">Update doctor observations and clinical notes</p>
                </div>
              </div>
              <button
                onClick={() => setIsEditingNotes(false)}
                disabled={isSavingNotes}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              <textarea
                value={editedNotes}
                onChange={(e) => setEditedNotes(e.target.value)}
                placeholder="Enter clinical notes, observations, and recommendations here..."
                disabled={isSavingNotes}
                className="w-full h-96 p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-medical-blue focus:border-transparent resize-none text-gray-700 leading-relaxed disabled:bg-gray-50 disabled:cursor-not-allowed"
              />
              <div className="mt-2 flex items-center justify-between text-sm text-gray-500">
                <span>Use clear, professional language for medical documentation</span>
                <span>{editedNotes.length} characters</span>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-6 bg-gray-50 border-t border-gray-200">
              <button
                onClick={() => setIsEditingNotes(false)}
                disabled={isSavingNotes}
                className="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNotes}
                disabled={isSavingNotes}
                className="px-6 py-2.5 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-lg hover:shadow-lg hover:scale-105 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {isSavingNotes ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Notes
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Easter Egg: Bat Animation */}
      {showBats && (
        <BatEasterEgg onComplete={() => setShowBats(false)} />
      )}

      {/* Unregister Confirmation Modal */}
      {showUnregisterConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Unregister {patient?.name}?</h3>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to unregister <strong>{patient?.name}</strong>? They will no longer share medical data with you and any pending registration requests will be cancelled.
            </p>
            <div className="flex flex-col gap-3">
              <button
                onClick={handleUnregister}
                disabled={isUnregistering}
                className="w-full py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-sm transition-colors disabled:opacity-50"
              >
                {isUnregistering ? 'Unregistering...' : 'Yes, Unregister'}
              </button>
              <button
                onClick={() => setShowUnregisterConfirm(false)}
                disabled={isUnregistering}
                className="w-full py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold text-sm transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientProfilePage;