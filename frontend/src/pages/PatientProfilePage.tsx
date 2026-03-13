import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft, Hash, User, Phone, Calendar, FileText, Brain, AlertCircle,
  Activity, TrendingUp, Clock, Heart, ChevronRight,
  Stethoscope, Clipboard, BarChart3, CheckCircle2, XCircle, MinusCircle, X, Save, UserX, Edit, ShieldAlert
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { VitalsChart } from "@/components/charts/VitalsChart";
import type { VisitVitalsPoint } from "@/components/charts/VitalsChart";
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

interface VisitRecord extends VisitVitalsPoint {
  visit_type?: string | null;
  notes?: string | null;
  wbc?: number | null;
  rbc?: number | null;
  hgb?: number | null;
  hct?: number | null;
  mcv?: number | null;
  mch?: number | null;
  mchc?: number | null;
  plt?: number | null;
  accelerations?: number | null;
  fetal_health_status?: number | null;
  gdm_risk_level?: number | null;
  anemia_diagnosis?: string | null;
}

interface VisitStatsResponse {
  total_visits: number;
  recent_visits: VisitRecord[];
}

type TabType = 'overview' | 'medical' | 'notes' | 'ai' | 'visits' | 'vitals';

const VALID_TABS: TabType[] = ['overview', 'medical', 'notes', 'ai', 'visits', 'vitals'];

const getTabFromQuery = (value: string | null): TabType => {
  if (value && VALID_TABS.includes(value as TabType)) {
    return value as TabType;
  }
  return 'overview';
};

const PatientProfilePage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [medicalData, setMedicalData] = useState<PatientMedical | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>(() => getTabFromQuery(searchParams.get('tab')));
  const [visitStats, setVisitStats] = useState<VisitStatsResponse>({ total_visits: 0, recent_visits: [] });
  const [visits, setVisits] = useState<VisitRecord[]>([]);
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
    const tabFromQuery = getTabFromQuery(searchParams.get('tab'));
    if (tabFromQuery !== activeTab) {
      setActiveTab(tabFromQuery);
    }
  }, [searchParams, activeTab]);

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

      // Also record a visit entry so this note appears in Visit History.
      await fetch(`${API_URL}/api/visits`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patient_id: patient.patient_identifier,
          visit_type: 'clinical_notes',
          notes: editedNotes,
        }),
      });

      setIsEditingNotes(false);
      fetchPatientData();

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
        const visitsData: VisitStatsResponse = await visitsResponse.json();
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

  const selectTab = (tab: TabType) => {
    setActiveTab(tab);
    const nextParams = new URLSearchParams(searchParams);
    if (tab === 'overview') {
      nextParams.delete('tab');
    } else {
      nextParams.set('tab', tab);
    }
    setSearchParams(nextParams);
  };

  const getRiskConfig = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high':
        return {
          bgColor: 'from-rose-500 via-pink-500 to-red-500',
          textColor: 'text-rose-600',
          ringColor: 'stroke-rose-500',
          label: 'High Risk',
        };
      case 'medium':
        return {
          bgColor: 'from-violet-500 via-indigo-500 to-blue-500',
          textColor: 'text-violet-600',
          ringColor: 'stroke-violet-500',
          label: 'Medium Risk',
        };
      case 'low':
        return {
          bgColor: 'from-cyan-500 via-blue-500 to-teal-500',
          textColor: 'text-cyan-600',
          ringColor: 'stroke-cyan-500',
          label: 'Low Risk',
        };
      default:
        return {
          bgColor: 'from-gray-400 to-gray-500',
          textColor: 'text-gray-600',
          ringColor: 'stroke-gray-400',
          label: 'Unknown',
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
        <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10">
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
        <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10">
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
        <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10">
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
  const profileReturnTo = `/patients/${patient.patient_identifier}${activeTab === 'overview' ? '' : `?tab=${activeTab}`}`;
  const latestVisit = visitStats.recent_visits?.[0];

  const averageMetric = (selector: (visit: VisitVitalsPoint) => number | null | undefined) => {
    const values = visits
      .map(selector)
      .filter((v): v is number => typeof v === 'number' && !Number.isNaN(v));
    if (values.length === 0) return null;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  };

  const avgGlucose = averageMetric((visit) => visit.glucose_level ?? visit.ogtt);
  const avgSystolic = averageMetric((visit) => visit.blood_pressure_systolic);
  const avgDiastolic = averageMetric((visit) => visit.blood_pressure_diastolic);
  const avgBmi = averageMetric((visit) => visit.bmi);
  const avgHemoglobin = averageMetric((visit) => visit.hgb);

  const timelineVisits = visits.map((visit) => ({
    id: visit.id,
    visit_date: visit.visit_date,
    visit_type: visit.visit_type || 'routine',
    notes: visit.notes || '',
    wbc: visit.wbc ?? null,
    rbc: visit.rbc ?? null,
    hgb: visit.hgb ?? null,
    hct: visit.hct ?? null,
    mcv: visit.mcv ?? null,
    mch: visit.mch ?? null,
    mchc: visit.mchc ?? null,
    plt: visit.plt ?? null,
    baseline_value: visit.baseline_value ?? null,
    accelerations: visit.accelerations ?? null,
    fetal_health_status: visit.fetal_health_status ?? null,
    glucose_level: visit.glucose_level ?? null,
    blood_pressure_systolic: visit.blood_pressure_systolic ?? null,
    blood_pressure_diastolic: visit.blood_pressure_diastolic ?? null,
    bmi: visit.bmi ?? null,
    ogtt: visit.ogtt ?? null,
    gdm_risk_level: visit.gdm_risk_level ?? null,
    anemia_diagnosis: visit.anemia_diagnosis ?? null,
  }));

  const medicalConditions = [
    {
      key: 'family_history',
      label: 'Family History',
      description: 'Genetic predisposition to metabolic conditions',
      icon: User,
      activeStyles: 'bg-gradient-to-br from-pink-50 to-rose-50 border-medical-pink/30',
      activeIconStyles: 'bg-gradient-to-br from-medical-pink to-pink-600',
      activeTextStyles: 'bg-pink-100 text-pink-700',
      activeIconText: 'text-medical-pink',
      value: Boolean(medicalData?.family_history),
    },
    {
      key: 'pcos',
      label: 'PCOS',
      description: 'Polycystic ovary syndrome',
      icon: Activity,
      activeStyles: 'bg-gradient-to-br from-blue-50 to-cyan-50 border-medical-blue/30',
      activeIconStyles: 'bg-gradient-to-br from-medical-blue to-blue-600',
      activeTextStyles: 'bg-blue-100 text-blue-700',
      activeIconText: 'text-medical-blue',
      value: Boolean(medicalData?.pcos),
    },
    {
      key: 'unexplained_prenatal_loss',
      label: 'Prenatal Loss History',
      description: 'Unexplained prenatal loss in previous pregnancy',
      icon: Heart,
      activeStyles: 'bg-gradient-to-br from-purple-50 to-violet-50 border-purple-300/30',
      activeIconStyles: 'bg-gradient-to-br from-purple-500 to-violet-500',
      activeTextStyles: 'bg-purple-100 text-purple-700',
      activeIconText: 'text-purple-600',
      value: Boolean(medicalData?.unexplained_prenatal_loss),
    },
    {
      key: 'large_child_or_birth_default',
      label: 'Large Birth Complication',
      description: 'Prior large child or birth complication history',
      icon: User,
      activeStyles: 'bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-300/30',
      activeIconStyles: 'bg-gradient-to-br from-indigo-500 to-blue-500',
      activeTextStyles: 'bg-indigo-100 text-indigo-700',
      activeIconText: 'text-indigo-600',
      value: Boolean(medicalData?.large_child_or_birth_default),
    },
    {
      key: 'prediabetes',
      label: 'Prediabetes',
      description: 'Elevated blood glucose before diagnosis threshold',
      icon: Activity,
      activeStyles: 'bg-gradient-to-br from-rose-50 to-pink-50 border-rose-300/30',
      activeIconStyles: 'bg-gradient-to-br from-rose-500 to-pink-500',
      activeTextStyles: 'bg-rose-100 text-rose-700',
      activeIconText: 'text-rose-600',
      value: Boolean(medicalData?.prediabetes),
    },
  ];

  const activeConditionCount = medicalConditions.filter((c) => c.value).length;
  const clinicalSignals = [
    latestVisit?.blood_pressure_systolic >= 140 ? `Elevated BP: ${latestVisit.blood_pressure_systolic}/${latestVisit.blood_pressure_diastolic ?? '?'} mmHg` : null,
    latestVisit?.glucose_level >= 140 ? `High glucose: ${latestVisit.glucose_level} mg/dL` : null,
    latestVisit?.hgb && latestVisit.hgb < 11 ? `Low hemoglobin: ${latestVisit.hgb} g/dL` : null,
    latestVisit?.fetal_health_status === 2 ? 'Fetal status: suspect' : null,
    latestVisit?.fetal_health_status === 3 ? 'Fetal status: pathological' : null,
  ].filter(Boolean) as string[];

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
        <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-6 relative z-10">
          {/* Back Button */}
          <button
            onClick={() => navigate('/patients')}
            className="flex items-center gap-2 text-gray-600 hover:text-medical-blue transition-colors mb-4 sm:mb-6 group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="text-sm font-medium">Back to Patients</span>
          </button>

          {/* Hero Content */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Left: Patient Info */}
            <div className="flex items-center gap-4">
              {/* Avatar */}
              <div className="relative flex-shrink-0">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue p-0.5 shadow-xl">
                  <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                    <User className="w-8 h-8 text-gray-700" />
                  </div>
                </div>
              </div>

              {/* Patient Details */}
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-gray-500 tracking-wide">{patient.patient_identifier}</span>
                  <div className={cn(
                    "px-3 py-1 rounded-full text-xs font-bold text-white",
                    `bg-gradient-to-r ${riskConfig.bgColor}`,
                    patient.risk_level === 'high' && "animate-pulse"
                  )}>
                    {riskConfig.label}
                  </div>
                </div>

                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                  {patient.name}
                </h1>

                <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-gray-600 text-sm">
                  <div className="flex items-center gap-1.5">
                    <User className="w-4 h-4" />
                    <span>{patient.age} years</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Phone className="w-4 h-4" />
                    <span>{patient.contact_number}</span>
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
                  <span className="hidden sm:inline">Unregister Patient</span>
                  <span className="sm:hidden">Unregister</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="bg-white/90 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => selectTab(tab.id)}
                  className={cn(
                    "relative px-3 sm:px-5 py-4 font-semibold transition-all duration-300 flex items-center gap-1.5 group whitespace-nowrap flex-shrink-0",
                    isActive
                      ? "text-medical-blue"
                      : "text-gray-600 hover:text-gray-900"
                  )}
                >
                  <Icon className={cn(
                    "w-4 h-4 transition-transform",
                    isActive && "scale-110"
                  )} />
                  <span className="text-sm">{tab.label}</span>

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
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-10">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {/* Risk Level */}
              <div className="group relative bg-gradient-to-br from-medical-pink/5 to-rose-50/50 p-6 rounded-2xl border border-medical-pink/20 hover:shadow-xl transition-all duration-300 overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-medical-pink/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-medical-pink to-rose-400 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <ShieldAlert className="w-6 h-6 text-white" />
                    </div>
                    <TrendingUp className="w-5 h-5 text-medical-pink" />
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Risk Level</p>
                  <p className={cn("text-3xl font-bold mb-2", riskConfig.textColor)}>{riskConfig.label}</p>
                  <p className="text-xs text-gray-500 font-semibold">Based on latest assessment</p>
                </div>
              </div>

              {/* Total Visits */}
              <button
                onClick={() => selectTab('visits')}
                className="group relative bg-gradient-to-br from-medical-blue/5 to-cyan-50/50 p-6 rounded-2xl border border-medical-blue/20 hover:shadow-xl transition-all duration-300 overflow-hidden text-left w-full"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-medical-blue/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-medical-blue to-cyan-400 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <Stethoscope className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:translate-x-1 transition-transform" />
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Total Visits</p>
                  <p className="text-4xl font-bold text-gray-900 mb-2">{visitStats.total_visits}</p>
                  <p className="text-xs text-gray-500 font-semibold">
                    {visitStats.recent_visits[0]
                      ? `Last visit: ${new Date(visitStats.recent_visits[0].visit_date).toLocaleDateString()}`
                      : 'No visits yet'}
                  </p>
                </div>
              </button>

              {/* Risk Factors */}
              <button
                onClick={() => selectTab('medical')}
                className="group relative bg-gradient-to-br from-purple-50 to-violet-50 p-6 rounded-2xl border border-purple-200/50 hover:shadow-xl transition-all duration-300 overflow-hidden text-left w-full"
              >
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
              </button>
            </div>

            {/* Quick Summary Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Visits */}
              <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-gray-200/50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    <Stethoscope className="w-5 h-5 text-medical-blue" />
                    Recent Visits
                  </h3>
                  {visitStats.total_visits > 0 && (
                    <button
                      onClick={() => selectTab('visits')}
                      className="text-sm text-medical-blue font-semibold hover:underline"
                    >
                      View all
                    </button>
                  )}
                </div>
                {visitStats.recent_visits.length === 0 ? (
                  <div className="text-center py-6">
                    <Stethoscope className="w-10 h-10 text-gray-200 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No visits recorded yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {visitStats.recent_visits.slice(0, 3).map((v: any, i: number) => (
                      <div key={v.id ?? i} className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl">
                        <div className="w-2 h-2 bg-medical-blue rounded-full mt-2 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-900">
                            {v.visit_type ? v.visit_type.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) : 'Clinical Visit'}
                          </p>
                          <p className="text-xs text-gray-500">{new Date(v.visit_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</p>
                          {v.notes && <p className="text-xs text-gray-400 mt-1 truncate">{v.notes}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
              <p className="text-gray-600">Dynamic profile generated from patient records and latest visit indicators</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div className="bg-white/90 rounded-2xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Tracked Conditions</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{medicalConditions.length}</p>
              </div>
              <div className="bg-white/90 rounded-2xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Active Flags</p>
                <p className="text-2xl font-bold text-rose-600 mt-1">{activeConditionCount}</p>
              </div>
              <div className="bg-white/90 rounded-2xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Dynamic Visit Signals</p>
                <p className="text-2xl font-bold text-violet-600 mt-1">{clinicalSignals.length}</p>
              </div>
            </div>

            {clinicalSignals.length > 0 && (
              <div className="mb-6 bg-violet-50/60 rounded-2xl border border-violet-200 p-4">
                <h3 className="text-sm font-bold text-violet-700 mb-2">Latest Visit Signals</h3>
                <div className="flex flex-wrap gap-2">
                  {clinicalSignals.map((signal, idx) => (
                    <span key={idx} className="px-3 py-1 rounded-full text-xs font-semibold bg-white text-violet-700 border border-violet-200">
                      {signal}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {medicalConditions.map((condition) => {
                const Icon = condition.icon;
                return (
                  <div
                    key={condition.key}
                    className={cn(
                      "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                      condition.value ? condition.activeStyles : "bg-white border-gray-200"
                    )}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className={cn(
                        "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                        condition.value ? condition.activeIconStyles : "bg-gray-200"
                      )}>
                        <Icon className="w-7 h-7 text-white" />
                      </div>
                      {condition.value ? (
                        <CheckCircle2 className={cn("w-8 h-8", condition.activeIconText)} />
                      ) : (
                        <MinusCircle className="w-8 h-8 text-gray-400" />
                      )}
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">{condition.label}</h3>
                    <p className="text-sm text-gray-600 mb-4">{condition.description}</p>
                    <div className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                      condition.value ? condition.activeTextStyles : "bg-gray-100 text-gray-600"
                    )}>
                      {condition.value ? "Active" : "Not Present"}
                    </div>
                  </div>
                );
              })}
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

              <div className="mt-6 bg-white rounded-2xl border border-gray-200 p-6">
                <h3 className="text-lg font-bold text-gray-900">Continue in Clinical Notes</h3>
                <p className="text-sm text-gray-600 mt-2">
                  Open the Clinical Notes page to parse notes for this patient and save patient data as a new visit.
                </p>
                <button
                  onClick={() => navigate(`/data-entry?patientId=${patient.patient_identifier}&returnTo=${encodeURIComponent(profileReturnTo)}`)}
                  className="mt-4 px-4 py-2 rounded-lg bg-gradient-to-r from-medical-pink to-medical-blue text-white text-sm font-semibold"
                >
                  Open Clinical Notes
                </button>
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
            <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-gray-200/50 overflow-hidden">
              <div className="p-8 border-b border-gray-200/70 bg-gradient-to-r from-violet-50 via-fuchsia-50 to-blue-50">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-14 h-14 bg-gradient-to-br from-medical-pink to-medical-blue rounded-2xl flex items-center justify-center shadow-lg animate-glow-pulse">
                      <Brain className="w-7 h-7 text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">AI Analysis Report</h2>
                      <p className="text-sm text-gray-600">Data-backed summary from the latest patient records</p>
                    </div>
                  </div>
                  <button
                    className="px-5 py-2.5 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-xl hover:shadow-lg hover:scale-105 transition-all flex items-center gap-2"
                    onClick={() => navigate(`/chat?message=${encodeURIComponent(`run full assessment for ${patient.name} (${patient.patient_identifier})`)}&returnTo=${encodeURIComponent(profileReturnTo)}`)}
                  >
                    <Brain className="w-4 h-4" />
                    Regenerate
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/80 rounded-xl p-4 border border-violet-200">
                    <p className="text-xs uppercase tracking-wide font-semibold text-gray-500">Risk Level</p>
                    <div className={cn("mt-2 inline-flex px-3 py-1.5 rounded-full text-sm font-bold text-white bg-gradient-to-r", riskConfig.bgColor)}>
                      {riskConfig.label}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Source: patient profile risk field</p>
                  </div>
                  <div className="bg-white/80 rounded-xl p-4 border border-violet-200">
                    <p className="text-xs uppercase tracking-wide font-semibold text-gray-500">Latest Visit</p>
                    <p className="text-lg font-bold text-gray-900 mt-2">
                      {latestVisit ? new Date(latestVisit.visit_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'No visits yet'}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">{latestVisit?.visit_type ? latestVisit.visit_type.replace(/_/g, ' ') : 'No visit type available'}</p>
                  </div>
                  <div className="bg-white/80 rounded-xl p-4 border border-violet-200">
                    <p className="text-xs uppercase tracking-wide font-semibold text-gray-500">Signals</p>
                    <p className="text-lg font-bold text-gray-900 mt-2">{clinicalSignals.length}</p>
                    <p className="text-xs text-gray-500 mt-2">From latest vitals/lab entries</p>
                  </div>
                </div>
              </div>

              <div className="p-8">
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                  <div className="lg:col-span-3 bg-gradient-to-br from-pink-50/70 to-purple-50/70 rounded-2xl p-6 border-l-4 border-medical-pink">
                    <h3 className="text-sm font-semibold text-purple-600 mb-4 uppercase tracking-wide">Clinical Summary</h3>
                    <p className="text-gray-700 leading-relaxed text-base mb-4 whitespace-pre-wrap">
                      {patient.clinical_notes || 'No clinical summary available yet. Add or update doctor notes to improve this report.'}
                    </p>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Brain className="w-4 h-4" />
                      <span>Summary combines patient profile fields and visit history</span>
                    </div>
                  </div>

                  <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-200">
                    <h3 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">Latest Structured Metrics</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <span className="text-sm text-gray-600">Glucose</span>
                        <span className="text-sm font-bold text-gray-900">{latestVisit?.glucose_level ? `${latestVisit.glucose_level} mg/dL` : 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <span className="text-sm text-gray-600">Blood Pressure</span>
                        <span className="text-sm font-bold text-gray-900">
                          {latestVisit?.blood_pressure_systolic ? `${latestVisit.blood_pressure_systolic}/${latestVisit.blood_pressure_diastolic ?? '?'} mmHg` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <span className="text-sm text-gray-600">Hemoglobin</span>
                        <span className="text-sm font-bold text-gray-900">{latestVisit?.hgb ? `${latestVisit.hgb} g/dL` : 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <span className="text-sm text-gray-600">Fetal Status</span>
                        <span className="text-sm font-bold text-gray-900">
                          {latestVisit?.fetal_health_status === 1 && 'Normal'}
                          {latestVisit?.fetal_health_status === 2 && 'Suspect'}
                          {latestVisit?.fetal_health_status === 3 && 'Pathological'}
                          {!latestVisit?.fetal_health_status && 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
                  <Calendar className="w-4 h-4" />
                  <span>Last profile update: {formatDate(patient.updated_at)}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Visit History Tab */}
        {activeTab === 'visits' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <VisitTimeline visits={timelineVisits} />
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
                  <p className="text-xs font-semibold text-medical-pink mb-1">AVG GLUCOSE</p>
                  <p className="text-2xl font-bold text-foreground">
                    {avgGlucose !== null ? avgGlucose.toFixed(1) : 'N/A'}
                    {avgGlucose !== null && <span className="text-sm font-normal text-muted-foreground"> mg/dL</span>}
                  </p>
                </div>
                <div className="bg-gradient-to-br from-medical-blue/10 to-cyan-50/50 p-4 rounded-xl border border-medical-blue/20">
                  <p className="text-xs font-semibold text-medical-blue mb-1">AVG BLOOD PRESSURE</p>
                  <p className="text-2xl font-bold text-foreground">
                    {avgSystolic !== null && avgDiastolic !== null
                      ? `${Math.round(avgSystolic)}/${Math.round(avgDiastolic)}`
                      : 'N/A'}
                    {avgSystolic !== null && avgDiastolic !== null && <span className="text-sm font-normal text-muted-foreground"> mmHg</span>}
                  </p>
                </div>
                <div className="bg-gradient-to-br from-cyan-50 to-teal-50 p-4 rounded-xl border border-cyan-200">
                  <p className="text-xs font-semibold text-cyan-600 mb-1">AVG BMI</p>
                  <p className="text-2xl font-bold text-foreground">
                    {avgBmi !== null ? avgBmi.toFixed(1) : 'N/A'}
                  </p>
                </div>
                <div className="bg-gradient-to-br from-medical-pink/10 to-medical-blue/10 p-4 rounded-xl border border-medical-blue/20">
                  <p className="text-xs font-semibold text-medical-blue mb-1">AVG HEMOGLOBIN</p>
                  <p className="text-2xl font-bold text-foreground">
                    {avgHemoglobin !== null ? avgHemoglobin.toFixed(1) : 'N/A'}
                    {avgHemoglobin !== null && <span className="text-sm font-normal text-muted-foreground"> g/dL</span>}
                  </p>
                </div>
              </div>

              <VitalsChart visits={visits} />
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