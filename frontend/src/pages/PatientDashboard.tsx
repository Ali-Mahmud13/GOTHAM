import { useState, useEffect } from "react";
import {
  User, Phone, Calendar, Heart, Activity, Clock, Stethoscope, BarChart3,
  AlertCircle, ChevronRight, Clipboard,
  CalendarCheck, PlusCircle, ShieldAlert
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { PatientNavbar } from "@/components/PatientNavbar";
import { VitalsChart } from "@/components/charts/VitalsChart";
import type { VisitVitalsPoint } from "@/components/charts/VitalsChart";
import { VisitTimeline } from "@/components/patient/VisitTimeline";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import { apiFetch } from "@/lib/apiClient";

interface PatientProfile {
  id: number;
  patient_identifier: string;
  name: string;
  age: number;
  contact_number: string;
  clinical_notes: string | null;
  doctor_id: number | null;
  is_registered_with_doctor: boolean;
  risk_level: 'unassessed' | 'high' | 'medium' | 'low';
  number_of_pregnancies: number | null;
  bmi_category: number | null;
  family_history: boolean | null;
  pcos: boolean | null;
  unexplained_prenatal_loss: boolean | null;
  large_child_or_birth_default: boolean | null;
  prediabetes: boolean | null;
  created_at: string;
  updated_at: string;
  latest_assessment_type: 'maternal' | 'fetal' | 'both' | null;
  latest_assessment_at: string | null;
  latest_assessment_outcomes: {
    gdm_risk_level?: number | null;
    anemia_diagnosis?: string | null;
    fetal_health_status?: number | null;
    preeclampsia_risk_level?: number | null;
  } | null;
  latest_assessment_freshness: Record<string, {
    oldest_input_age_days?: number | null;
    has_stale_inputs?: boolean;
  }> | null;
}

interface Appointment {
  id: number;
  doctor_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: string;
  notes?: string;
}

interface RegistrationRequestResult {
  id: number;
  doctor_name: string;
  status: string;
}

interface VisitRecord extends VisitVitalsPoint {
  visit_type?: string | null;
  notes?: string | null;
  note_source?: 'patient' | 'doctor' | 'current_doctor' | 'previous_doctor' | 'unknown';
  is_past_history?: boolean;
  ultrasound_images?: Array<{
    id: number;
    secure_url: string;
    thumbnail_url?: string | null;
    file_name?: string | null;
    uploaded_by_role?: string | null;
    uploaded_by_user_id?: number | null;
    created_at?: string | null;
  }>;
  wbc?: number | null;
  rbc?: number | null;
  hgb?: number | null;
  hct?: number | null;
  mcv?: number | null;
  mch?: number | null;
  mchc?: number | null;
  plt?: number | null;
  accelerations?: number | null;
  fetal_movement?: number | null;
  uterine_contractions?: number | null;
  light_decelerations?: number | null;
  severe_decelerations?: number | null;
  prolongued_decelerations?: number | null;
  abnormal_short_term_variability?: number | null;
  mean_value_of_short_term_variability?: number | null;
  percentage_of_time_with_abnormal_long_term_variability?: number | null;
  mean_value_of_long_term_variability?: number | null;
  histogram_width?: number | null;
  histogram_min?: number | null;
  histogram_max?: number | null;
  histogram_number_of_peaks?: number | null;
  histogram_number_of_zeroes?: number | null;
  histogram_mode?: number | null;
  histogram_mean?: number | null;
  histogram_median?: number | null;
  histogram_variance?: number | null;
  histogram_tendency?: number | null;
  fetal_health_status?: number | null;
  gdm_risk_level?: number | null;
  anemia_diagnosis?: string | null;
  body_temp?: number | null;
  heart_rate?: number | null;
  maternal_risk_level?: number | null;
  assessment_results?: Record<string, {
    status?: 'completed' | 'incomplete' | 'failed' | null;
    severity?: 'low' | 'medium' | 'high' | null;
    outcome?: string | null;
    oldest_input_age_days?: number | null;
    has_stale_inputs?: boolean;
  } | null>;
}

interface VisitStatsResponse {
  total_visits: number;
  recent_visits: VisitRecord[];
}

type TabType = 'overview' | 'medical' | 'notes' | 'visits' | 'vitals';

export const PatientDashboard = () => {
  const { isAuthenticated, user, logout, tokens, setTokens } = useAuth();
  const navigate = useNavigate();
  const localTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [visitStats, setVisitStats] = useState<VisitStatsResponse>({ total_visits: 0, recent_visits: [] });
  const [visits, setVisits] = useState<VisitRecord[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [pendingRegistrationDoctor, setPendingRegistrationDoctor] = useState<string | null>(null);

  // Get patient identifier from auth user
  const patientIdentifier = user?.patient_info?.patient_identifier;

  useEffect(() => {
    if (!isAuthenticated || !user || user.role !== 'patient' || !patientIdentifier) {
      navigate('/patient/login');
      return;
    }
    fetchPatientData();
  }, [isAuthenticated, user, patientIdentifier, navigate]);

  const fetchUpcomingAppointments = async () => {
    try {
      const res = await apiFetch(
        `/appointments/upcoming`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data = await res.json();
        setAppointments(data);
      }
    } catch (err) {
      console.error('Failed to fetch appointments:', err);
    }
  };

  const fetchPatientData = async () => {
    if (!patientIdentifier) return;

    try {
      // Fetch patient profile
      const profileResponse = await apiFetch(
        `/api/patient-portal/profile/${patientIdentifier}`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (!profileResponse.ok) {
        throw new Error('Failed to fetch patient profile');
      }
      const profileData = await profileResponse.json();
      setPatient(profileData);

      if (!profileData.doctor_id) {
        try {
          const regRes = await apiFetch(
            `/appointments/my-registration-requests`,
            { method: "GET" },
            tokens,
            setTokens,
            logout,
          );
          if (regRes.ok) {
            const regData: RegistrationRequestResult[] = await regRes.json();
            const pendingReq = regData.find((r) => r.status === 'pending');
            setPendingRegistrationDoctor(pendingReq?.doctor_name || null);
          } else {
            setPendingRegistrationDoctor(null);
          }
        } catch {
          setPendingRegistrationDoctor(null);
        }
      } else {
        setPendingRegistrationDoctor(null);
      }

      // Fetch visit history with assessment metrics for trend charts and summaries
      const visitsResponse = await apiFetch(
        `/api/dashboard/patient/${patientIdentifier}/visits`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (visitsResponse.ok) {
        const visitsData: VisitStatsResponse = await visitsResponse.json();
        setVisits(visitsData.recent_visits || []);
        setVisitStats(visitsData);
      }

      setError(null);
    } catch (err) {
      console.error('Error fetching patient data:', err);
      setError('Failed to load your profile. Please try again.');
    } finally {
      setLoading(false);
    }
    fetchUpcomingAppointments();
  };

  const handleDeleteUltrasound = async (imageId: number) => {
    try {
      const res = await apiFetch(
        `/api/ultrasound/${imageId}`,
        { method: "DELETE" },
        tokens,
        setTokens,
        logout,
      );
      if (!res.ok) {
        const errorPayload = await res.json();
        throw new Error(errorPayload.detail || 'Failed to delete ultrasound image');
      }

      setVisits((prev) =>
        prev.map((visit) => ({
          ...visit,
          ultrasound_images: (visit.ultrasound_images || []).filter((img) => img.id !== imageId),
        }))
      );
    } catch (err) {
      console.error(err);
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
      case 'unassessed':
      default:
        return {
          bgColor: 'from-gray-400 to-gray-500',
          textColor: 'text-gray-600',
          ringColor: 'stroke-gray-400',
          label: 'Not Assessed',
        };
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const timelineVisits = visits.map((visit) => ({
    id: visit.id,
    visit_date: visit.visit_date,
    visit_type: visit.visit_type || 'routine',
    notes: visit.notes || '',
    note_source: visit.note_source || 'unknown',
    is_past_history: Boolean(visit.is_past_history),
    ultrasound_images: visit.ultrasound_images || [],
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
    fetal_movement: visit.fetal_movement ?? null,
    uterine_contractions: visit.uterine_contractions ?? null,
    light_decelerations: visit.light_decelerations ?? null,
    severe_decelerations: visit.severe_decelerations ?? null,
    prolongued_decelerations: visit.prolongued_decelerations ?? null,
    abnormal_short_term_variability: visit.abnormal_short_term_variability ?? null,
    mean_value_of_short_term_variability: visit.mean_value_of_short_term_variability ?? null,
    percentage_of_time_with_abnormal_long_term_variability: visit.percentage_of_time_with_abnormal_long_term_variability ?? null,
    mean_value_of_long_term_variability: visit.mean_value_of_long_term_variability ?? null,
    histogram_width: visit.histogram_width ?? null,
    histogram_min: visit.histogram_min ?? null,
    histogram_max: visit.histogram_max ?? null,
    histogram_number_of_peaks: visit.histogram_number_of_peaks ?? null,
    histogram_number_of_zeroes: visit.histogram_number_of_zeroes ?? null,
    histogram_mode: visit.histogram_mode ?? null,
    histogram_mean: visit.histogram_mean ?? null,
    histogram_median: visit.histogram_median ?? null,
    histogram_variance: visit.histogram_variance ?? null,
    histogram_tendency: visit.histogram_tendency ?? null,
    fetal_health_status: visit.fetal_health_status ?? null,
    glucose_level: visit.glucose_level ?? null,
    blood_pressure_systolic: visit.blood_pressure_systolic ?? null,
    blood_pressure_diastolic: visit.blood_pressure_diastolic ?? null,
    bmi: visit.bmi ?? null,
    ogtt: visit.ogtt ?? null,
    gdm_risk_level: visit.gdm_risk_level ?? null,
    anemia_diagnosis: visit.anemia_diagnosis ?? null,
    body_temp: visit.body_temp ?? null,
    heart_rate: visit.heart_rate ?? null,
    maternal_risk_level: visit.maternal_risk_level ?? null,
    assessment_results: visit.assessment_results || {},
  }));

  const visitHistoryVisits = timelineVisits.filter((visit) => {
    // Keep visit history focused on true visits; exclude notepad-only entries.
    if (visit.visit_type === 'patient_notes' || visit.visit_type === 'doctor_notes') return false;
    return true;
  });

  const labeledNotes = timelineVisits
    .filter((visit) => Boolean(visit.notes))
    .map((visit) => {
      let label = 'Clinical Note';
      if (visit.note_source === 'patient' && visit.visit_type === 'clinical_notes') label = 'Self-Entered Clinical Note';
      else if (visit.note_source === 'patient') label = 'Patient Note';
      else if (visit.note_source === 'previous_doctor') label = 'Past Doctor Note';
      else if (visit.note_source === 'current_doctor' || visit.note_source === 'doctor') label = 'Doctor Visit Note';
      return { ...visit, noteLabel: label };
    });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
        <PatientNavbar />
        <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10">
          <div className="text-center text-lg">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent rounded-full text-medical-blue mb-4" />
            <p>Loading your profile...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
        <PatientNavbar />
        <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10">
          <div className="text-center text-red-500">
            <p>{error || 'Failed to load your profile.'}</p>
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
  const isRegisteredWithDoctor = Boolean(patient.is_registered_with_doctor || patient.doctor_id);
  const assessmentOutcomes = [
    {
      label: 'GDM',
      value: patient.latest_assessment_outcomes?.gdm_risk_level === 0
        ? 'Negative'
        : patient.latest_assessment_outcomes?.gdm_risk_level != null
          ? 'Positive'
          : null,
    },
    {
      label: 'Anemia',
      value: patient.latest_assessment_outcomes?.anemia_diagnosis || null,
    },
    {
      label: 'Fetal CTG',
      value: patient.latest_assessment_outcomes?.fetal_health_status === 1
        ? 'Normal'
        : patient.latest_assessment_outcomes?.fetal_health_status === 2
          ? 'Suspect'
          : patient.latest_assessment_outcomes?.fetal_health_status === 3
            ? 'Pathological'
            : null,
    },
    {
      label: 'Preeclampsia',
      value: patient.latest_assessment_outcomes?.preeclampsia_risk_level === 0
        ? 'Low'
        : patient.latest_assessment_outcomes?.preeclampsia_risk_level === 1
          ? 'Medium'
          : patient.latest_assessment_outcomes?.preeclampsia_risk_level === 2
            ? 'High'
            : null,
    },
  ].filter((item): item is { label: string; value: string } => Boolean(item.value));
  const agingModels = Object.entries(patient.latest_assessment_freshness || {})
    .filter(([, details]) => (
      details.has_stale_inputs
      || (details.oldest_input_age_days != null && details.oldest_input_age_days > 30)
    ));
  const historyStatus = (value: boolean | null, yesLabel: string) => {
    if (value === true) return yesLabel;
    if (value === false) return 'No';
    return 'Not provided';
  };

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: BarChart3 },
    { id: 'medical' as TabType, label: 'Medical History', icon: Stethoscope },
    { id: 'notes' as TabType, label: 'Notes', icon: Clipboard },
    { id: 'visits' as TabType, label: 'Visit History', icon: Clock },
    { id: 'vitals' as TabType, label: 'Vitals', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/20 to-pink-50/20">
      <PatientNavbar />

      {/* Hero Header Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50/30 to-pink-50/30 border-b border-gray-200">
        <div className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Left: Patient Info */}
            <div className="flex items-center gap-4">
              {/* Avatar */}
              <div className="relative flex-shrink-0">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue p-0.5 shadow-xl">
                  <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                    <User className="w-8 h-8 sm:w-10 sm:h-10 text-gray-700" />
                  </div>
                </div>
              </div>

              {/* Patient Details */}
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-gray-500 tracking-wide">{patient.patient_identifier}</span>
                </div>

                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                  {patient.name}
                </h1>

                <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-gray-600 text-sm">
                  {patient.age > 0 && (
                    <div className="flex items-center gap-1.5">
                      <User className="w-4 h-4" />
                      <span>{patient.age} years</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <Phone className="w-4 h-4" />
                    <span>{patient.contact_number}</span>
                  </div>
                </div>
              </div>
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
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "relative px-3 sm:px-6 py-4 font-semibold transition-all duration-300 flex items-center gap-1.5 group whitespace-nowrap flex-shrink-0",
                    isActive
                      ? "text-medical-blue"
                      : "text-gray-600 hover:text-gray-900"
                  )}
                >
                  <Icon className={cn(
                    "w-4 h-4 sm:w-5 sm:h-5 transition-transform",
                    isActive && "scale-110"
                  )} />
                  <span className="text-sm sm:text-base">{tab.label}</span>

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
        {!isRegisteredWithDoctor && (
          <div className="mb-6 rounded-2xl border border-amber-300 bg-amber-50 p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-amber-800">
                  {pendingRegistrationDoctor
                    ? `Waiting to be registered with Dr. ${pendingRegistrationDoctor}`
                    : 'You are currently not registered with a doctor'}
                </p>
                <p className="text-sm text-amber-700 mt-1">
                  {pendingRegistrationDoctor
                    ? 'Your registration request is pending. You can continue using Patient Notes while waiting.'
                    : 'You can add self-entered AI Clinical Visits (for vitals by date) and Patient Notes while unregistered.'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => navigate('/patient/book-appointment')}
                  className="px-3 py-2 rounded-lg bg-medical-blue text-white text-sm font-semibold hover:bg-medical-blue/90"
                >
                  Register With Doctor
                </button>
                <button
                  onClick={() => navigate(`/data-entry?patientId=${patient.patient_identifier}&returnTo=${encodeURIComponent('/patient/dashboard')}`)}
                  className="px-3 py-2 rounded-lg border border-medical-blue text-medical-blue bg-white text-sm font-semibold hover:bg-blue-50"
                >
                  Open AI Clinical Notes
                </button>
                <button
                  onClick={() => navigate('/patient/notes')}
                  className="px-3 py-2 rounded-lg border border-amber-400 text-amber-800 bg-white text-sm font-semibold hover:bg-amber-100"
                >
                  Open Patient Notes
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              {/* Total Visits */}
              <button
                onClick={() => setActiveTab('visits')}
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
                      ? `Last: ${new Date(visitStats.recent_visits[0].visit_date).toLocaleDateString()}`
                      : 'No visits yet'}
                  </p>
                </div>
              </button>

              {/* Assessment Status */}
              <div className="relative bg-gradient-to-br from-purple-50 to-violet-50 p-6 rounded-2xl border border-purple-200/50 shadow-sm overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-violet-500/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-violet-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <ShieldAlert className="w-6 h-6 text-white" />
                    </div>
                    <span className={cn(
                      "rounded-full bg-white/80 px-3 py-1 text-xs font-bold shadow-sm",
                      riskConfig.textColor,
                    )}>
                      {riskConfig.label}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Assessment Status</p>
                  <p className="text-xl font-bold text-gray-900 mb-2">{riskConfig.label}</p>
                  <p className="text-xs text-gray-500 font-semibold">
                    {patient.latest_assessment_at
                      ? `Last assessed ${formatDate(patient.latest_assessment_at)}`
                      : 'No completed model assessment yet'}
                  </p>
                  {assessmentOutcomes.length > 0 && (
                    <div className="mt-4 grid grid-cols-2 gap-2">
                      {assessmentOutcomes.map((outcome) => (
                        <div key={outcome.label} className="rounded-lg border border-white/80 bg-white/70 px-3 py-2">
                          <p className="text-[11px] font-semibold text-gray-500">{outcome.label}</p>
                          <p className="text-sm font-bold text-gray-800">{outcome.value}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {agingModels.length > 0 && (
                    <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                      Some assessment readings are more than 30 days old. Review them with your doctor.
                    </div>
                  )}
                </div>
              </div>
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
                      onClick={() => setActiveTab('visits')}
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
                    {visitStats.recent_visits.slice(0, 3).map((v, i) => (
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
                    <span className="text-sm font-semibold text-gray-600">Contact</span>
                    <span className="text-sm font-bold text-gray-900">{patient.contact_number}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Upcoming Appointments */}
            <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-gray-200/50">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <CalendarCheck className="w-5 h-5 text-medical-blue" />
                  Upcoming Appointments
                </h3>
                <span className="text-xs text-gray-500">Times in {localTz}</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate('/patient/appointments')}
                    className="text-sm text-medical-blue font-semibold hover:underline"
                  >
                    View all
                  </button>
                  <button
                    onClick={() => navigate('/patient/book-appointment')}
                    className="flex items-center gap-1 px-3 py-1.5 bg-medical-blue text-white rounded-lg text-sm font-semibold hover:bg-medical-blue/90 transition-colors"
                  >
                    <PlusCircle className="w-4 h-4" />
                    Book
                  </button>
                </div>
              </div>
              {appointments.length === 0 ? (
                <div className="text-center py-8">
                  <CalendarCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 font-medium">No upcoming appointments.</p>
                  <button
                    onClick={() => navigate('/patient/book-appointment')}
                    className="mt-3 text-medical-blue font-semibold hover:underline text-sm"
                  >
                    Book one now &rarr;
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {appointments.slice(0, 3).map((appt, idx) => (
                    <div key={appt.id} className={`flex items-center justify-between p-3 rounded-xl relative ${
                      idx === 0
                        ? 'bg-gradient-to-r from-medical-pink/10 to-medical-blue/10 border border-medical-blue/20'
                        : 'bg-blue-50'
                    }`}>
                      {idx === 0 && (
                        <span className="absolute top-2 right-2 text-[9px] font-bold uppercase bg-gradient-to-r from-medical-pink to-medical-blue text-white px-1.5 py-0.5 rounded-full leading-none">
                          Next
                        </span>
                      )}
                      <div className="flex items-center gap-3 pr-10">
                        <div className="w-10 h-10 bg-medical-blue/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Stethoscope className="w-5 h-5 text-medical-blue" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">Dr. {appt.doctor_name}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(appt.appointment_date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                            {' · '}{appt.start_time} – {appt.end_time}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs font-bold rounded-full capitalize flex-shrink-0 ${
                        appt.status === 'booked' ? 'bg-emerald-100 text-emerald-700' :
                        appt.status === 'pending_approval' ? 'bg-amber-100 text-amber-700' :
                        appt.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                        appt.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {appt.status === 'pending_approval' ? 'Pending' : appt.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {!isRegisteredWithDoctor && (
              <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-amber-200">
                <div className="flex items-center gap-3 mb-3">
                  <Clipboard className="w-5 h-5 text-amber-700" />
                  <h3 className="text-lg font-bold text-gray-900">Patient Notes</h3>
                </div>
                <p className="text-sm text-gray-700">
                  Since you are not registered with a doctor, your notes are self-reported.
                </p>
                <p className="text-xs text-gray-600 mt-2">
                  Disclaimer: You are responsible for the integrity and accuracy of submitted data and any decisions made based on that data.
                </p>
                <div className="mt-4 flex items-center gap-2">
                  <button
                    onClick={() => navigate(`/data-entry?patientId=${patient.patient_identifier}&returnTo=${encodeURIComponent('/patient/dashboard')}`)}
                    className="px-4 py-2 rounded-lg border border-medical-blue text-medical-blue text-sm font-semibold hover:bg-blue-50"
                  >
                    Add AI Clinical Visit
                  </button>
                  <button
                    onClick={() => navigate('/patient/notes')}
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-medical-pink to-medical-blue text-white text-sm font-semibold"
                  >
                    Add Patient Notes
                  </button>
                  <button
                    onClick={() => navigate('/patient/book-appointment')}
                    className="px-4 py-2 rounded-lg border border-medical-blue text-medical-blue text-sm font-semibold hover:bg-blue-50"
                  >
                    Find a Doctor
                  </button>
                </div>
              </div>
            )}

            {/* Doctor's Notes (Read-only for patient) */}
            {isRegisteredWithDoctor && patient.clinical_notes && (
              <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl p-8 border border-gray-200/50">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg">
                    <Clipboard className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Dr Notes</h2>
                    <p className="text-sm text-gray-600">Your doctor's observations</p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50/70 to-cyan-50/70 rounded-2xl p-6 border-l-4 border-blue-500">
                  <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {patient.clinical_notes}
                  </p>
                </div>

                <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  <span>Last updated: {formatDate(patient.updated_at)}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Medical History Tab */}
        {activeTab === 'medical' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Medical History</h2>
              <p className="text-gray-600">Information you or your care team have reported</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Family History */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                patient.family_history
                  ? "bg-gradient-to-br from-pink-50 to-rose-50 border-medical-pink/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    patient.family_history
                      ? "bg-gradient-to-br from-medical-pink to-pink-600"
                      : "bg-gray-200"
                  )}>
                    <User className="w-7 h-7 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Family History</h3>
                <p className="text-sm text-gray-600 mb-4">Diabetes in family</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  patient.family_history
                    ? "bg-pink-100 text-pink-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {historyStatus(patient.family_history, "Present")}
                </div>
              </div>

              {/* PCOS */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                patient.pcos
                  ? "bg-gradient-to-br from-purple-50 to-violet-50 border-purple-300/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    patient.pcos
                      ? "bg-gradient-to-br from-purple-500 to-violet-500"
                      : "bg-gray-200"
                  )}>
                    <Activity className="w-7 h-7 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">PCOS</h3>
                <p className="text-sm text-gray-600 mb-4">Polycystic Ovary Syndrome</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  patient.pcos
                    ? "bg-purple-100 text-purple-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {historyStatus(patient.pcos, "Diagnosed")}
                </div>
              </div>

              {/* Prenatal Loss */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                patient.unexplained_prenatal_loss
                  ? "bg-gradient-to-br from-orange-50 to-amber-50 border-orange-300/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    patient.unexplained_prenatal_loss
                      ? "bg-gradient-to-br from-orange-500 to-amber-500"
                      : "bg-gray-200"
                  )}>
                    <AlertCircle className="w-7 h-7 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Prenatal Loss</h3>
                <p className="text-sm text-gray-600 mb-4">Unexplained prenatal loss history</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  patient.unexplained_prenatal_loss
                    ? "bg-orange-100 text-orange-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {historyStatus(patient.unexplained_prenatal_loss, "Reported")}
                </div>
              </div>

              {/* Large Birth */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                patient.large_child_or_birth_default
                  ? "bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-300/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    patient.large_child_or_birth_default
                      ? "bg-gradient-to-br from-indigo-500 to-blue-500"
                      : "bg-gray-200"
                  )}>
                    <Heart className="w-7 h-7 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Large Birth</h3>
                <p className="text-sm text-gray-600 mb-4">Large child or birth complications</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  patient.large_child_or_birth_default
                    ? "bg-indigo-100 text-indigo-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {historyStatus(patient.large_child_or_birth_default, "Reported")}
                </div>
              </div>

              {/* Prediabetes */}
              <div className={cn(
                "group relative p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl",
                patient.prediabetes
                  ? "bg-gradient-to-br from-rose-50 to-pink-50 border-rose-300/30"
                  : "bg-white border-gray-200"
              )}>
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
                    patient.prediabetes
                      ? "bg-gradient-to-br from-rose-500 to-pink-500"
                      : "bg-gray-200"
                  )}>
                    <Activity className="w-7 h-7 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Prediabetes</h3>
                <p className="text-sm text-gray-600 mb-4">Elevated blood sugar levels</p>
                <div className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                  patient.prediabetes
                    ? "bg-rose-100 text-rose-700"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {historyStatus(patient.prediabetes, "Diagnosed")}
                </div>
              </div>

              {/* Number of Pregnancies */}
              <div className="group relative p-6 rounded-2xl border-2 bg-gradient-to-br from-teal-50 to-cyan-50 border-teal-300/30 transition-all duration-300 hover:shadow-xl">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform bg-gradient-to-br from-teal-500 to-cyan-500">
                    <Heart className="w-7 h-7 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Total Pregnancies</h3>
                <p className="text-sm text-gray-600 mb-4">Total pregnancies reported</p>
                <div className="px-3 py-1.5 rounded-full text-xs font-bold inline-block bg-teal-100 text-teal-700">
                  {patient.number_of_pregnancies !== null ? patient.number_of_pregnancies : "Not provided"}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Notes Tab */}
        {activeTab === 'notes' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl p-6 border border-gray-200/50">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Patient Notes</h2>
                {!isRegisteredWithDoctor && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => navigate('/patient/notes')}
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-medical-pink to-medical-blue text-white text-sm font-semibold"
                    >
                      Add Patient Note
                    </button>
                    <button
                      onClick={() => navigate(`/data-entry?patientId=${patient.patient_identifier}&returnTo=${encodeURIComponent('/patient/dashboard')}`)}
                      className="px-4 py-2 rounded-lg border border-medical-blue text-medical-blue text-sm font-semibold hover:bg-blue-50"
                    >
                      Open AI Clinical Notes
                    </button>
                  </div>
                )}
              </div>

              <p className="text-sm text-gray-600 mb-4">
                {isRegisteredWithDoctor
                  ? 'Showing doctor notes and historical notes by source label.'
                  : 'Showing your patient notes and historical notes by source label.'}
              </p>

              {labeledNotes.length === 0 ? (
                <p className="text-sm text-muted-foreground">No notes available.</p>
              ) : (
                <div className="space-y-3">
                  {labeledNotes.map((v) => (
                      <div key={v.id} className="rounded-xl border border-gray-200 p-4 bg-white">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-xs text-gray-500">{new Date(v.visit_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</p>
                          <span className={cn(
                            'text-xs font-semibold px-2 py-1 rounded-full',
                            v.note_source === 'current_doctor' || v.note_source === 'doctor'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-amber-100 text-amber-700'
                          )}>
                            {v.noteLabel}
                          </span>
                        </div>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap">{v.notes}</p>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Visit History Tab */}
        {activeTab === 'visits' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <VisitTimeline
              visits={visitHistoryVisits}
              hideCareStatusBadge={true}
              onDeleteUltrasound={handleDeleteUltrasound}
              canDeleteUltrasound={(image) => (
                image.uploaded_by_role === 'patient'
                && image.uploaded_by_user_id === user?.id
              )}
            />
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
                  <p className="text-sm text-muted-foreground">Monitor your key health metrics over time</p>
                </div>
              </div>

              <VitalsChart visits={visits.filter(v =>
                v.bmi != null || v.blood_pressure_systolic != null ||
                v.blood_pressure_diastolic != null || v.glucose_level != null ||
                v.ogtt != null || v.hgb != null || v.baseline_value != null
              )} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
