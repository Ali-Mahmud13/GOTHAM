import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft, User, Phone, Calendar, Brain, AlertCircle,
  Activity, Clock, Heart, ChevronRight,
  Stethoscope, Clipboard, BarChart3, CheckCircle2, MinusCircle, HelpCircle, Save, UserX, Edit, ShieldAlert
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { VitalsChart } from "@/components/charts/VitalsChart";
import type { VisitVitalsPoint } from "@/components/charts/VitalsChart";
import { VisitTimeline } from "@/components/patient/VisitTimeline";
import { BatEasterEgg } from "@/components/BatEasterEgg";
import { MicButton } from "@/components/MicButton";
import { cn } from "@/lib/utils";
import { insertAtCaret } from "@/lib/text";
import { formatPakistanDate, formatPakistanDateTime } from "@/lib/dateTime";
import type { TranscriptionLanguage } from "@/lib/transcribe";
import ReactMarkdown from "react-markdown";
import { ApiError } from "@/lib/apiClient";
import { useToast } from "@/hooks/use-toast";
import { useApiMutation, useApiQuery, useSessionCache } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface AssessmentOutcomes {
  gdm_risk_level?: number | null;
  gdm_confidence?: number | null;
  anemia_diagnosis?: string | null;
  anemia_confidence?: number | null;
  fetal_health_status?: number | null;
  fetal_confidence?: number | null;
  preeclampsia_risk_level?: number | null;
  preeclampsia_confidence?: number | null;
}

interface AssessmentFreshness {
  oldest_input_age_days?: number | null;
  has_stale_inputs?: boolean;
  input_provenance?: Record<string, {
    measured_at?: string;
    age_days?: number;
    freshness?: 'fresh' | 'aging' | 'stale' | 'profile';
    source_visit_id?: number;
  }>;
}

interface PatientProfile {
  id: number;
  patient_identifier: string;
  name: string;
  age: number;
  contact_number: string;
  clinical_notes: string | null;
  latest_ai_report?: string | null;
  latest_assessment_type?: 'maternal' | 'fetal' | 'both' | null;
  latest_assessment_at?: string | null;
  latest_assessment_outcomes?: AssessmentOutcomes | null;
  latest_assessment_freshness?: Record<string, AssessmentFreshness> | null;
  risk_level: 'unassessed' | 'high' | 'medium' | 'low';
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
  total_clinical_visits?: number;
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
  const [activeTab, setActiveTab] = useState<TabType>(() => getTabFromQuery(searchParams.get('tab')));
  const [showBats, setShowBats] = useState(false);
  const [keySequence, setKeySequence] = useState('');
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [editedNotes, setEditedNotes] = useState('');
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const editedNotesRef = useRef<HTMLTextAreaElement>(null);
  const [notesDictationLanguage, setNotesDictationLanguage] = useState<TranscriptionLanguage>("en");

  const dictateIntoEditedNotes = (text: string) => {
    const result = insertAtCaret(editedNotes, text, editedNotesRef.current);
    setEditedNotes(result.value);
    requestAnimationFrame(() => {
      const el = editedNotesRef.current;
      if (el) {
        el.focus();
        el.setSelectionRange(result.caret, result.caret);
      }
    });
  };
  const [showUnregisterConfirm, setShowUnregisterConfirm] = useState(false);
  const [isUnregistering, setIsUnregistering] = useState(false);
  const [ultrasoundToDelete, setUltrasoundToDelete] = useState<number | null>(null);
  const [isDeletingUltrasound, setIsDeletingUltrasound] = useState(false);
  const { toast } = useToast();
  const { queryClient, key } = useSessionCache();
  const profileKey = queryKeys.patients.detail(patientId ?? "missing");
  const visitsKey = queryKeys.patients.visits(patientId ?? "missing");
  const profileQuery = useApiQuery<PatientProfile>(
    profileKey,
    `/api/patients/${patientId ?? ""}`,
    { enabled: Boolean(patientId), retry: false },
  );
  const visitsQuery = useApiQuery<VisitStatsResponse>(
    visitsKey,
    `/api/dashboard/patient/${patientId ?? ""}/visits`,
    { enabled: Boolean(patientId) },
  );
  const patient = profileQuery.data ?? null;
  const medicalData: PatientMedical | null = patient;
  const loading = profileQuery.isPending;
  const error = profileQuery.error instanceof ApiError && profileQuery.error.status === 404
    ? "not_found"
    : profileQuery.isError ? "error" : null;
  const visitStats = visitsQuery.data ?? { total_visits: 0, recent_visits: [] };
  const visits = visitStats.recent_visits ?? [];
  const isLoadingVisits = visitsQuery.isPending;
  const visitsError = visitsQuery.isError ? "Visit history could not be loaded." : null;
  const unregisterPatient = useApiMutation<void, void>({
    invalidate: [
      queryKeys.patients.all,
      queryKeys.dashboard.stats,
      queryKeys.appointments.all,
      queryKeys.registration.all,
    ],
    mutationFn: (_, request) =>
      request<void>(`/appointments/unregister/patient/${patientId}`, {
        method: "DELETE",
      }),
  });
  const updateNotes = useApiMutation<PatientProfile, string>({
    invalidate: [profileKey, queryKeys.patients.all],
    mutationFn: (clinicalNotes, request) =>
      request<PatientProfile>(`/api/patients/${patientId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clinical_notes: clinicalNotes }),
      }),
  });
  const deleteUltrasound = useApiMutation<void, number>({
    invalidate: [visitsKey],
    mutationFn: (imageId, request) =>
      request<void>(`/api/ultrasound/${imageId}`, { method: "DELETE" }),
  });
  const fetchPatientData = () => Promise.all([
    profileQuery.refetch(),
    visitsQuery.refetch(),
  ]);

  useEffect(() => {
    const tabFromQuery = getTabFromQuery(searchParams.get('tab'));
    if (tabFromQuery !== activeTab) {
      setActiveTab(tabFromQuery);
    }
  }, [searchParams, activeTab]);

  const handleUnregister = async () => {
    if (!patientId) return;
    setIsUnregistering(true);
    try {
      await unregisterPatient.mutateAsync();
      toast({
        title: "Patient unregistered",
        description: "The patient is no longer assigned to your care.",
      });
      navigate("/patients");
    } catch (err) {
      toast({
        title: "Unable to unregister patient",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUnregistering(false);
      setShowUnregisterConfirm(false);
    }
  };

  // Easter egg keyboard listener
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only track alphanumeric keys
      if (e.key.length === 1 && /[a-zA-Z0-9]/.test(e.key)) {
        setKeySequence(prev => {
          const newSequence = (prev + e.key.toLowerCase()).slice(-5);

          // Check if the sequence matches "eza13" and patient is high risk
          if (newSequence === 'eza13' && patient?.risk_level === 'high') {
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
      const updatedPatient = await updateNotes.mutateAsync(editedNotes);
      queryClient.setQueryData(key(profileKey), updatedPatient);
      setIsEditingNotes(false);
      toast({
        title: "Notes saved",
        description: "The global doctor notepad has been updated.",
      });
    } catch (err) {
      toast({
        title: "Unable to save notes",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSavingNotes(false);
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

  const handleDeleteUltrasound = async () => {
    if (ultrasoundToDelete === null) return;
    const imageId = ultrasoundToDelete;
    setIsDeletingUltrasound(true);
    try {
      queryClient.setQueryData<VisitStatsResponse>(key(visitsKey), (previous) =>
        previous
          ? {
              ...previous,
              recent_visits: previous.recent_visits.map((visit) => ({
                ...visit,
                ultrasound_images: (visit.ultrasound_images || []).filter((img) => img.id !== imageId),
              })),
            }
          : previous,
      );
      await deleteUltrasound.mutateAsync(imageId);
      toast({
        title: "Ultrasound deleted",
        description: "The image has been removed from this visit.",
      });
    } catch (err) {
      toast({
        title: "Unable to delete ultrasound",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsDeletingUltrasound(false);
      setUltrasoundToDelete(null);
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
      default:
        return {
          bgColor: 'from-gray-400 to-gray-500',
          textColor: 'text-gray-600',
          ringColor: 'stroke-gray-400',
          label: 'Not Assessed',
        };
    }
  };

  const formatDate = (dateString: string) => formatPakistanDateTime(dateString);

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

  const hasCompletedAssessment = patient.risk_level !== 'unassessed';
  const riskConfig = getRiskConfig(patient.risk_level);
  const profileReturnTo = `/patients/${patient.patient_identifier}${activeTab === 'overview' ? '' : `?tab=${activeTab}`}`;
  const sortedClinicalVisits = [...visits]
    .filter((visit) => visit.visit_type !== 'patient_notes' && visit.visit_type !== 'doctor_notes')
    .sort((a, b) => new Date(b.visit_date).getTime() - new Date(a.visit_date).getTime());
  const latestVisit = sortedClinicalVisits[0];

  const latestAvailable = <T,>(selector: (visit: VisitRecord) => T | null | undefined) => {
    for (const visit of sortedClinicalVisits) {
      const value = selector(visit);
      if (value !== null && value !== undefined) {
        return { value, visitDate: visit.visit_date };
      }
    }
    return null;
  };

  const latestGlucose = latestAvailable((visit) => visit.glucose_level);
  const latestOgtt = latestAvailable((visit) => visit.ogtt);
  const latestBloodPressure = latestAvailable((visit) => {
    if (visit.blood_pressure_systolic == null && visit.blood_pressure_diastolic == null) return null;
    return {
      systolic: visit.blood_pressure_systolic,
      diastolic: visit.blood_pressure_diastolic,
    };
  });
  const latestBmi = latestAvailable((visit) => visit.bmi);
  const latestHemoglobin = latestAvailable((visit) => visit.hgb);
  const latestFetalBaseline = latestAvailable((visit) => visit.baseline_value);
  const latestFetalStatus = latestAvailable((visit) => visit.fetal_health_status);
  const latestGdmRisk = latestAvailable((visit) => visit.gdm_risk_level);
  const latestPreeclampsiaRisk = latestAvailable((visit) => visit.maternal_risk_level);

  const formatMeasurementDate = (date?: string) => formatPakistanDate(date, 'No reading');

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
      else if (visit.note_source === 'current_doctor' || visit.note_source === 'doctor') label = 'Current Doctor Visit Note';
      return { ...visit, noteLabel: label };
    });

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
      value: medicalData?.family_history ?? null,
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
      value: medicalData?.pcos ?? null,
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
      value: medicalData?.unexplained_prenatal_loss ?? null,
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
      value: medicalData?.large_child_or_birth_default ?? null,
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
      value: medicalData?.prediabetes ?? null,
    },
  ];

  const activeConditionCount = medicalConditions.filter((condition) => condition.value === true).length;
  const absentConditionCount = medicalConditions.filter((condition) => condition.value === false).length;
  const unknownConditionCount = medicalConditions.filter((condition) => condition.value === null).length;
  const clinicalSignals = [
    latestBloodPressure?.value.systolic != null && latestBloodPressure.value.systolic >= 140
      ? `Elevated blood pressure: ${latestBloodPressure.value.systolic}/${latestBloodPressure.value.diastolic ?? '?'} mmHg`
      : null,
    latestGlucose?.value != null && latestGlucose.value >= 140
      ? `Elevated glucose: ${latestGlucose.value} mg/dL`
      : null,
    latestHemoglobin?.value != null && latestHemoglobin.value < 11
      ? `Low hemoglobin: ${latestHemoglobin.value} g/dL`
      : null,
    latestFetalStatus?.value === 2 ? 'Fetal model result: suspect' : null,
    latestFetalStatus?.value === 3 ? 'Fetal model result: pathological' : null,
    latestGdmRisk?.value === 1 ? 'GDM model result: elevated risk' : null,
    latestGdmRisk?.value === 2 ? 'GDM model result: high risk' : null,
    latestPreeclampsiaRisk?.value === 1 ? 'Preeclampsia model result: elevated risk' : null,
    latestPreeclampsiaRisk?.value === 2 ? 'Preeclampsia model result: high risk' : null,
  ].filter(Boolean) as string[];

  const formatConfidence = (confidence?: number | null) => {
    if (confidence == null) return null;
    const percentage = confidence <= 1 ? confidence * 100 : confidence;
    return `${percentage.toFixed(1)}% confidence`;
  };
  const riskOutcomeLabel = (value?: number | null) => {
    if (value === 0) return 'Normal';
    if (value === 1) return 'Elevated risk';
    if (value === 2) return 'High risk';
    return null;
  };
  const fetalOutcomeLabel = (value?: number | null) => {
    if (value === 1) return 'Normal';
    if (value === 2) return 'Suspect';
    if (value === 3) return 'Pathological';
    return null;
  };
  const freshnessLabel = (model: string) => {
    const freshness = patient.latest_assessment_freshness?.[model];
    if (!freshness || freshness.oldest_input_age_days == null) return null;
    const age = freshness.oldest_input_age_days;
    const category = age <= 30 ? 'Fresh' : age <= 90 ? 'Aging' : 'Stale';
    return `${category} inputs · oldest reading ${age} day${age === 1 ? '' : 's'} old`;
  };
  const outcomeDetail = (model: string, confidence?: number | null) => {
    return [formatConfidence(confidence), freshnessLabel(model)].filter(Boolean).join(' · ') || null;
  };
  const assessmentOutcomes = [
    {
      label: 'Gestational Diabetes',
      value: riskOutcomeLabel(patient.latest_assessment_outcomes?.gdm_risk_level),
      detail: outcomeDetail('gdm', patient.latest_assessment_outcomes?.gdm_confidence),
    },
    {
      label: 'Anemia',
      value: patient.latest_assessment_outcomes?.anemia_diagnosis || null,
      detail: outcomeDetail('anemia', patient.latest_assessment_outcomes?.anemia_confidence),
    },
    {
      label: 'Fetal Health',
      value: fetalOutcomeLabel(patient.latest_assessment_outcomes?.fetal_health_status),
      detail: outcomeDetail('fetal', patient.latest_assessment_outcomes?.fetal_confidence),
    },
    {
      label: 'Preeclampsia',
      value: riskOutcomeLabel(patient.latest_assessment_outcomes?.preeclampsia_risk_level),
      detail: outcomeDetail('preeclampsia', patient.latest_assessment_outcomes?.preeclampsia_confidence),
    },
  ].filter((outcome) => outcome.value !== null);
  const staleModels = Object.entries(patient.latest_assessment_freshness || {})
    .filter(([, freshness]) => freshness.has_stale_inputs)
    .map(([model]) => model === 'gdm' ? 'Gestational Diabetes' :
      model === 'anemia' ? 'Anemia' :
      model === 'fetal' ? 'Fetal Health' : 'Preeclampsia');
  const provenanceRows = Object.entries(patient.latest_assessment_freshness || {}).flatMap(
    ([model, freshness]) => Object.entries(freshness.input_provenance || {}).map(
      ([field, source]) => ({
        key: `${model}-${field}`,
        model: model === 'gdm' ? 'GDM' :
          model === 'anemia' ? 'Anemia' :
          model === 'fetal' ? 'Fetal' : 'Preeclampsia',
        field: field.replace(/_/g, ' '),
        measuredAt: source.measured_at,
        ageDays: source.age_days,
        freshness: source.freshness,
      })
    )
  ).sort((a, b) => (b.ageDays ?? -1) - (a.ageDays ?? -1));

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
                    hasCompletedAssessment && patient.risk_level === 'high' && "animate-pulse"
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
                    <span>{patient.age && patient.age > 0 ? `${patient.age} years` : 'Age not set'}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Phone className="w-4 h-4" />
                    {patient.contact_number
                      ? <a href={`tel:${patient.contact_number}`} className="hover:underline">{patient.contact_number}</a>
                      : <span className="text-gray-400">Not set</span>}
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Quick Actions */}
            <div className="flex items-center gap-2">
              {user?.role === 'doctor' && (
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
                    {hasCompletedAssessment
                      ? <CheckCircle2 className="w-5 h-5 text-medical-pink" />
                      : <HelpCircle className="w-5 h-5 text-gray-400" />}
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Assessment Status</p>
                  <p className={cn("text-3xl font-bold mb-2", riskConfig.textColor)}>{riskConfig.label}</p>
                  <p className="text-xs text-gray-500 font-semibold">
                    {patient.latest_assessment_at
                      ? `Completed ${formatPakistanDateTime(patient.latest_assessment_at)}`
                      : 'No completed model assessment'}
                  </p>
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
                  <p className="text-sm font-semibold text-gray-600 mb-1">Clinical Visits</p>
                  <p className="text-4xl font-bold text-gray-900 mb-2">{visitStats.total_clinical_visits ?? visitHistoryVisits.length}</p>
                  <p className="text-xs text-gray-500 font-semibold">
                    {latestVisit
                      ? `Last visit: ${formatMeasurementDate(latestVisit.visit_date)}`
                      : 'No visits yet'}
                  </p>
                </div>
              </button>

              {/* Confirmed history */}
              <button
                onClick={() => selectTab('medical')}
                className="group relative bg-gradient-to-br from-purple-50 to-violet-50 p-6 rounded-2xl border border-purple-200/50 hover:shadow-xl transition-all duration-300 overflow-hidden text-left w-full"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-violet-500/10 rounded-full blur-2xl" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-violet-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <Clipboard className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                  <p className="text-sm font-semibold text-gray-600 mb-1">Confirmed History Factors</p>
                  <p className="text-4xl font-bold text-gray-900 mb-2">{activeConditionCount}</p>
                  <p className="text-xs text-gray-500 font-semibold">
                    {unknownConditionCount > 0 ? `${unknownConditionCount} not recorded` : 'All history fields recorded'}
                  </p>
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
                  {visitHistoryVisits.length > 0 && (
                    <button
                      onClick={() => selectTab('visits')}
                      className="text-sm text-medical-blue font-semibold hover:underline"
                    >
                      View all
                    </button>
                  )}
                </div>
                {isLoadingVisits ? (
                  <div className="text-center py-6 text-sm text-gray-500">Loading visits...</div>
                ) : visitsError ? (
                  <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    <p>{visitsError}</p>
                    <button onClick={fetchPatientData} className="mt-2 font-semibold underline">Retry</button>
                  </div>
                ) : visitHistoryVisits.length === 0 ? (
                  <div className="text-center py-6">
                    <Stethoscope className="w-10 h-10 text-gray-200 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No visits recorded yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {visitHistoryVisits.slice(0, 3).map((visit) => (
                      <div key={visit.id} className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl">
                        <div className="w-2 h-2 bg-medical-blue rounded-full mt-2 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-900">
                            {visit.visit_type ? visit.visit_type.replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) : 'Clinical Visit'}
                          </p>
                          <p className="text-xs text-gray-500">{formatMeasurementDate(visit.visit_date)}</p>
                          {visit.notes && <p className="text-xs text-gray-400 mt-1 truncate">{visit.notes}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Latest measurements */}
              <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-gray-200/50">
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-medical-pink" />
                  Latest Available Measurements
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <div>
                      <p className="text-sm font-semibold text-gray-600">Blood Pressure</p>
                      <p className="text-xs text-gray-400">{formatMeasurementDate(latestBloodPressure?.visitDate)}</p>
                    </div>
                    <span className="text-sm font-bold text-gray-900">
                      {latestBloodPressure
                        ? `${latestBloodPressure.value.systolic ?? '?'}/${latestBloodPressure.value.diastolic ?? '?'} mmHg`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <div>
                      <p className="text-sm font-semibold text-gray-600">Glucose</p>
                      <p className="text-xs text-gray-400">{formatMeasurementDate(latestGlucose?.visitDate)}</p>
                    </div>
                    <span className="text-sm font-bold text-gray-900">{latestGlucose ? `${latestGlucose.value} mg/dL` : 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <div>
                      <p className="text-sm font-semibold text-gray-600">Hemoglobin</p>
                      <p className="text-xs text-gray-400">{formatMeasurementDate(latestHemoglobin?.visitDate)}</p>
                    </div>
                    <span className="text-sm font-bold text-gray-900">{latestHemoglobin ? `${latestHemoglobin.value} g/dL` : 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <div>
                      <p className="text-sm font-semibold text-gray-600">BMI</p>
                      <p className="text-xs text-gray-400">{formatMeasurementDate(latestBmi?.visitDate)}</p>
                    </div>
                    <span className="text-sm font-bold text-gray-900">{latestBmi?.value ?? 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <div>
                      <p className="text-sm font-semibold text-gray-600">OGTT</p>
                      <p className="text-xs text-gray-400">{formatMeasurementDate(latestOgtt?.visitDate)}</p>
                    </div>
                    <span className="text-sm font-bold text-gray-900">{latestOgtt ? `${latestOgtt.value} mg/dL` : 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <div>
                      <p className="text-sm font-semibold text-gray-600">Fetal Baseline Heart Rate</p>
                      <p className="text-xs text-gray-400">{formatMeasurementDate(latestFetalBaseline?.visitDate)}</p>
                    </div>
                    <span className="text-sm font-bold text-gray-900">{latestFetalBaseline ? `${latestFetalBaseline.value} bpm` : 'N/A'}</span>
                  </div>
                </div>
                <button onClick={() => selectTab('vitals')} className="mt-4 text-sm font-semibold text-medical-blue hover:underline">
                  View measurement trends
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Medical History Tab */}
        {activeTab === 'medical' && medicalData && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Medical History</h2>
              <p className="text-gray-600">Recorded history factors and current clinical alerts are shown separately.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div className="bg-white/90 rounded-2xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Present</p>
                <p className="text-2xl font-bold text-rose-600 mt-1">{activeConditionCount}</p>
              </div>
              <div className="bg-white/90 rounded-2xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Not Present</p>
                <p className="text-2xl font-bold text-cyan-600 mt-1">{absentConditionCount}</p>
              </div>
              <div className="bg-white/90 rounded-2xl border border-gray-200 p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Unknown</p>
                <p className="text-2xl font-bold text-gray-600 mt-1">{unknownConditionCount}</p>
              </div>
            </div>

            <div className="mb-6 bg-violet-50/60 rounded-2xl border border-violet-200 p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4 text-violet-700" />
                <h3 className="text-sm font-bold text-violet-700">Latest Clinical Alerts</h3>
              </div>
              {clinicalSignals.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {clinicalSignals.map((signal, idx) => (
                    <span key={idx} className="px-3 py-1 rounded-full text-xs font-semibold bg-white text-violet-700 border border-violet-200">
                      {signal}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-violet-700/80">No alerts were derived from the latest available measurements and model results.</p>
              )}
              <p className="text-xs text-gray-500 mt-3">These alerts are display rules, not a combined risk score or diagnosis.</p>
            </div>

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
                      {condition.value === true ? (
                        <CheckCircle2 className={cn("w-8 h-8", condition.activeIconText)} />
                      ) : condition.value === false ? (
                        <MinusCircle className="w-8 h-8 text-cyan-500" />
                      ) : (
                        <HelpCircle className="w-8 h-8 text-gray-400" />
                      )}
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">{condition.label}</h3>
                    <p className="text-sm text-gray-600 mb-4">{condition.description}</p>
                    <div className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-bold inline-block",
                      condition.value === true
                        ? condition.activeTextStyles
                        : condition.value === false
                          ? "bg-cyan-50 text-cyan-700"
                          : "bg-gray-100 text-gray-600"
                    )}>
                      {condition.value === true ? "Present" : condition.value === false ? "Not Present" : "Unknown"}
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
                  {patient.clinical_notes ? 'Edit Notes' : 'Add Notes'}
                </button>
              </div>

              <div className="bg-gradient-to-br from-blue-50/70 to-cyan-50/70 rounded-2xl p-8 border-l-4 border-blue-500 min-h-[300px]">
                {!isEditingNotes && (
                  <div className="mb-6">
                    <h3 className="text-sm font-bold text-blue-700 mb-2">Doctor Notepad (Global)</h3>
                    <p className="text-gray-700 leading-relaxed text-base whitespace-pre-wrap">
                      {patient.clinical_notes || "No global doctor notepad content yet. Click 'Add Notes' to create one."}
                    </p>
                  </div>
                )}

                {isEditingNotes ? (
                  <div>
                    <textarea
                      ref={editedNotesRef}
                      value={editedNotes}
                      onChange={(e) => setEditedNotes(e.target.value)}
                      placeholder="Enter clinical notes here, or click the mic to dictate."
                      disabled={isSavingNotes}
                      className="w-full min-h-[240px] p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-medical-blue focus:border-transparent resize-y text-gray-700 leading-relaxed disabled:bg-gray-50 disabled:cursor-not-allowed"
                    />
                    <div className="mt-4 flex items-center justify-between">
                      <p className="text-xs text-gray-500">{editedNotes.length} characters</p>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center rounded-full border border-gray-300 bg-white/70 p-0.5">
                          <button
                            type="button"
                            onClick={() => setNotesDictationLanguage("en")}
                            disabled={isSavingNotes}
                            className={cn(
                              "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                              notesDictationLanguage === "en"
                                ? "bg-white text-medical-blue shadow-sm"
                                : "text-gray-500 hover:text-gray-800 hover:bg-gray-50",
                            )}
                            title="Dictate in English"
                            aria-pressed={notesDictationLanguage === "en"}
                          >
                            EN
                          </button>
                          <button
                            type="button"
                            onClick={() => setNotesDictationLanguage("ur")}
                            disabled={isSavingNotes}
                            className={cn(
                              "px-2 py-1 text-[11px] font-semibold rounded-full transition-colors",
                              notesDictationLanguage === "ur"
                                ? "bg-white text-medical-blue shadow-sm"
                                : "text-gray-500 hover:text-gray-800 hover:bg-gray-50",
                            )}
                            title="Dictate in Urdu / Minglish"
                            aria-pressed={notesDictationLanguage === "ur"}
                          >
                            اردو
                          </button>
                        </div>
                        <MicButton
                          onTranscript={dictateIntoEditedNotes}
                          language={notesDictationLanguage}
                          disabled={isSavingNotes}
                          size="sm"
                        />
                        <button
                          onClick={() => setIsEditingNotes(false)}
                          disabled={isSavingNotes}
                          className="px-4 py-2 bg-white border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveNotes}
                          disabled={isSavingNotes}
                          className="px-4 py-2 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-lg hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-50"
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
                ) : null}

                {!isEditingNotes && (
                  <div className="mt-4">
                    <h3 className="text-sm font-bold text-amber-700 mb-2">Notes by Source</h3>
                    {labeledNotes.length === 0 ? (
                      <p className="text-sm text-gray-500">No source notes found.</p>
                    ) : (
                      <div className="space-y-2">
                        {labeledNotes.slice(0, 8).map((v) => (
                          <div key={v.id} className="rounded-lg border border-amber-200 bg-amber-50/50 p-3">
                            <div className="flex items-center justify-between gap-2">
                              <p className="text-xs text-amber-700">{formatMeasurementDate(v.visit_date)}</p>
                              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-amber-100 text-amber-700">{v.noteLabel}</span>
                            </div>
                            <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{v.notes}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
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
                      <p className="text-sm text-gray-600">Latest completed model assessment</p>
                    </div>
                  </div>
                  <button
                    className="px-5 py-2.5 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-xl hover:shadow-lg hover:scale-105 transition-all flex items-center gap-2"
                    onClick={() => navigate(`/chat?message=${encodeURIComponent(`run full assessment for ${patient.name} (${patient.patient_identifier})`)}&returnTo=${encodeURIComponent(profileReturnTo)}`)}
                  >
                    <Brain className="w-4 h-4" />
                    Run New Assessment
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/80 rounded-xl p-4 border border-violet-200">
                    <p className="text-xs uppercase tracking-wide font-semibold text-gray-500">Assessment Type</p>
                    <p className="text-lg font-bold text-gray-900 mt-2 capitalize">
                      {patient.latest_assessment_type === 'both'
                        ? 'Maternal and fetal'
                        : patient.latest_assessment_type || 'Not assessed'}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">Models included in the latest run</p>
                  </div>
                  <div className="bg-white/80 rounded-xl p-4 border border-violet-200">
                    <p className="text-xs uppercase tracking-wide font-semibold text-gray-500">Completed</p>
                    <p className="text-lg font-bold text-gray-900 mt-2">
                      {patient.latest_assessment_at ? formatPakistanDateTime(patient.latest_assessment_at) : 'Not assessed'}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">Assessment completion date</p>
                  </div>
                  <div className="bg-white/80 rounded-xl p-4 border border-violet-200">
                    <p className="text-xs uppercase tracking-wide font-semibold text-gray-500">Overall Risk</p>
                    <div className={cn("mt-2 inline-flex px-3 py-1.5 rounded-full text-sm font-bold text-white bg-gradient-to-r", riskConfig.bgColor)}>
                      {riskConfig.label}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Shown only after a completed assessment</p>
                  </div>
                </div>
                {staleModels.length > 0 && (
                  <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-900">
                    <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-semibold">Assessment used stale readings</p>
                      <p className="text-xs mt-1">
                        {staleModels.join(', ')} included at least one measurement older than 90 days. Review the dated inputs before clinical use.
                      </p>
                    </div>
                  </div>
                )}
                {provenanceRows.length > 0 && (
                  <details className="mt-4 rounded-xl border border-violet-200 bg-white/70">
                    <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-violet-800">
                      Review model input dates
                    </summary>
                    <div className="max-h-72 overflow-y-auto border-t border-violet-100 px-4 py-2">
                      {provenanceRows.map((row) => (
                        <div key={row.key} className="flex items-center justify-between gap-4 border-b border-gray-100 py-2 last:border-0">
                          <div>
                            <p className="text-xs font-semibold text-gray-800 capitalize">{row.field}</p>
                            <p className="text-[11px] text-gray-500">{row.model}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-gray-700">
                              {row.measuredAt ? formatMeasurementDate(row.measuredAt) : 'Patient profile'}
                            </p>
                            {row.ageDays != null && (
                              <p className={cn(
                                "text-[11px] font-semibold capitalize",
                                row.freshness === 'stale' ? 'text-amber-700' :
                                  row.freshness === 'aging' ? 'text-violet-600' : 'text-emerald-600'
                              )}>
                                {row.freshness} · {row.ageDays}d old
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>

              <div className="p-8">
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                  <div className="lg:col-span-3 bg-gradient-to-br from-pink-50/70 to-purple-50/70 rounded-2xl p-6 border-l-4 border-medical-pink">
                    <h3 className="text-sm font-semibold text-purple-600 mb-4 uppercase tracking-wide">Assessment Summary</h3>
                    <div className="text-gray-700 leading-relaxed text-base">
                      <ReactMarkdown
                       components={{
                        p: ({ node, ...props }) => <p className="mb-2 whitespace-pre-wrap" {...props} />,
                        img: ({ node, ...props}) => (<img {...props} className="rounded-xl shadow-lg my-3 max-w-full border" />),
                        h1: ({ node, ...props}) => <h1 className="text-lg font-bold mt-3 mb-2" {...props} />,
                        h2: ({ node, ...props }) => <h2 className="text-base font-semibold mt-3 mb-2" {...props} />,
                        h3: ({ node, ...props }) => <h3 className="text-sm font-semibold mt-2 mb-1" {...props} />,
                        li: ({ node, ...props }) => <li className="ml-4 list-disc" {...props} />,
                        table: ({ node, ...props }) => <table className="w-full text-sm border my-2" {...props} />,
                        th: ({ node, ...props }) => <th className="border px-2 py-1 bg-gray-50" {...props} />,
                        td: ({ node, ...props }) => <td className="border px-2 py-1" {...props} />,
                       }}>
                        {patient.latest_ai_report || "No completed assessment report is available."}
                       </ReactMarkdown>
                    </div>
                  </div>

                  <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-200">
                    <h3 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">Model Outcomes</h3>
                    {assessmentOutcomes.length > 0 ? (
                      <div className="space-y-3">
                        {assessmentOutcomes.map((outcome) => (
                          <div key={outcome.label} className="p-3 bg-gray-50 rounded-xl">
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-sm text-gray-600">{outcome.label}</span>
                              <span className="text-sm font-bold text-gray-900 text-right">{outcome.value}</span>
                            </div>
                            {outcome.detail && <p className="text-xs text-gray-400 mt-1 text-right">{outcome.detail}</p>}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">No structured model outcomes were stored for this report.</p>
                    )}
                  </div>
                </div>

                <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
                  <Calendar className="w-4 h-4" />
                  <span>
                    {patient.latest_assessment_at
                      ? `Assessment completed ${formatDate(patient.latest_assessment_at)}`
                      : 'No completed assessment'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Visit History Tab */}
        {activeTab === 'visits' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isLoadingVisits ? (
              <div className="bg-white rounded-2xl border border-gray-200 p-10 text-center text-gray-500">Loading visit history...</div>
            ) : visitsError ? (
              <div className="bg-red-50 rounded-2xl border border-red-200 p-8 text-center">
                <p className="text-red-700">{visitsError}</p>
                <button onClick={fetchPatientData} className="mt-3 text-sm font-semibold text-red-700 underline">Retry</button>
              </div>
            ) : (
              <VisitTimeline visits={visitHistoryVisits} onDeleteUltrasound={setUltrasoundToDelete} />
            )}
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

              {isLoadingVisits ? (
                <div className="py-16 text-center text-gray-500">Loading measurements...</div>
              ) : visitsError ? (
                <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
                  <p className="text-red-700">{visitsError}</p>
                  <button onClick={fetchPatientData} className="mt-3 text-sm font-semibold text-red-700 underline">Retry</button>
                </div>
              ) : (
                <VitalsChart visits={visits.filter(v =>
                  v.bmi != null || v.blood_pressure_systolic != null ||
                  v.blood_pressure_diastolic != null || v.glucose_level != null ||
                  v.ogtt != null || v.hgb != null || v.baseline_value != null
                )} />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Easter Egg: Bat Animation */}
      {showBats && (
        <BatEasterEgg onComplete={() => setShowBats(false)} />
      )}

      <AlertDialog open={showUnregisterConfirm} onOpenChange={setShowUnregisterConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Unregister {patient.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes the patient from your assigned list, clears doctor-owned notes, cancels future appointments and pending registration requests, and preserves existing clinical and appointment history.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isUnregistering}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                void handleUnregister();
              }}
              disabled={isUnregistering}
              className="bg-red-600 text-white hover:bg-red-700"
            >
              {isUnregistering ? 'Unregistering...' : 'Unregister Patient'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={ultrasoundToDelete !== null} onOpenChange={(open) => !open && setUltrasoundToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete ultrasound image?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently removes the image from the visit and cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeletingUltrasound}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                void handleDeleteUltrasound();
              }}
              disabled={isDeletingUltrasound}
              className="bg-red-600 text-white hover:bg-red-700"
            >
              {isDeletingUltrasound ? 'Deleting...' : 'Delete Image'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default PatientProfilePage;
