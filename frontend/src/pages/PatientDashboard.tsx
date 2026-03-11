import { useState, useEffect } from "react";
import {
  User, Phone, Calendar, Heart, Activity, Clock, Stethoscope, BarChart3,
  AlertCircle, TrendingUp, ChevronRight, Zap, FileText, Clipboard, Brain,
  CalendarCheck, PlusCircle
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { PatientNavbar } from "@/components/PatientNavbar";
import { VitalsChart } from "@/components/charts/VitalsChart";
import { VisitTimeline } from "@/components/patient/VisitTimeline";
import { useAuth } from "@/context/AuthContext";
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
  bmi_category: number | null;
  family_history: boolean | null;
  pcos: boolean | null;
  unexplained_prenatal_loss: boolean | null;
  large_child_or_birth_default: boolean | null;
  prediabetes: boolean | null;
  created_at: string;
  updated_at: string;
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

type TabType = 'overview' | 'medical' | 'visits' | 'vitals';

export const PatientDashboard = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [visitStats, setVisitStats] = useState<{ total_visits: number; recent_visits: any[] }>({ total_visits: 0, recent_visits: [] });
  const [visits, setVisits] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

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
    if (!user?.email) return;
    try {
      const res = await fetch(`${API_URL}/appointments/upcoming`, {
        headers: { 'X-User-Email': user.email },
      });
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
      const profileResponse = await fetch(`${API_URL}/api/patient-portal/profile/${patientIdentifier}`);
      if (!profileResponse.ok) {
        throw new Error('Failed to fetch patient profile');
      }
      const profileData = await profileResponse.json();
      setPatient(profileData);

      // Fetch visit history
      const visitsResponse = await fetch(`${API_URL}/api/patient-portal/visits/${patientIdentifier}`);
      if (visitsResponse.ok) {
        const visitsData = await visitsResponse.json();
        setVisits(visitsData);
        setVisitStats({
          total_visits: visitsData.length,
          recent_visits: visitsData.slice(0, 5)
        });
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
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
        <PatientNavbar />
        <main className="container mx-auto px-6 py-10">
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
        <main className="container mx-auto px-6 py-10">
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

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: BarChart3 },
    { id: 'medical' as TabType, label: 'Medical History', icon: Stethoscope },
    { id: 'visits' as TabType, label: 'Visit History', icon: Clock },
    { id: 'vitals' as TabType, label: 'Vitals', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/20 to-pink-50/20">
      <PatientNavbar />

      {/* Hero Header Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50/30 to-pink-50/30 border-b border-gray-200">
        <div className="container mx-auto px-6 py-8 relative z-10">
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
                  {patient.age > 0 && (
                    <>
                      <div className="flex items-center gap-1.5">
                        <User className="w-4 h-4" />
                        <span>{patient.age} years</span>
                      </div>
                      <span className="text-gray-300">•</span>
                    </>
                  )}
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
                  <p className="text-xs text-medical-pink font-semibold">Risk: {patient.risk_level}</p>
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
                      ? `Last: ${new Date(visitStats.recent_visits[0].visit_date).toLocaleDateString()}`
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
                  <p className="text-4xl font-bold text-gray-900 mb-2">
                    {[patient.family_history, patient.pcos, patient.prediabetes, patient.unexplained_prenatal_loss].filter(Boolean).length}
                  </p>
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
                      <p className="text-sm font-semibold text-gray-900">Account Created</p>
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

            {/* Upcoming Appointments */}
            <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-gray-200/50">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <CalendarCheck className="w-5 h-5 text-medical-blue" />
                  Upcoming Appointments
                </h3>
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
                  {appointments.slice(0, 3).map((appt) => (
                    <div key={appt.id} className="flex items-center justify-between p-3 bg-blue-50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-medical-blue/10 rounded-lg flex items-center justify-center">
                          <Stethoscope className="w-5 h-5 text-medical-blue" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">{appt.doctor_name}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(appt.appointment_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                            {' · '}{appt.start_time} – {appt.end_time}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs font-bold rounded-full capitalize ${
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

            {/* Doctor's Notes (Read-only for patient) */}
            {patient.clinical_notes && (
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
              <p className="text-gray-600">Overview of your medical conditions and risk factors</p>
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
                  {patient.family_history ? "Present" : "Not Reported"}
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
                  {patient.pcos ? "Diagnosed" : "Not Reported"}
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
                  {patient.unexplained_prenatal_loss ? "Reported" : "Not Reported"}
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
                  {patient.large_child_or_birth_default ? "Reported" : "Not Reported"}
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
                  {patient.prediabetes ? "Diagnosed" : "Not Reported"}
                </div>
              </div>

              {/* Number of Pregnancies */}
              <div className="group relative p-6 rounded-2xl border-2 bg-gradient-to-br from-teal-50 to-cyan-50 border-teal-300/30 transition-all duration-300 hover:shadow-xl">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform bg-gradient-to-br from-teal-500 to-cyan-500">
                    <Heart className="w-7 h-7 text-white" />
                  </div>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Pregnancies</h3>
                <p className="text-sm text-gray-600 mb-4">Number of previous pregnancies</p>
                <div className="px-3 py-1.5 rounded-full text-xs font-bold inline-block bg-teal-100 text-teal-700">
                  {patient.number_of_pregnancies !== null ? `${patient.number_of_pregnancies} Previous` : "Not Reported"}
                </div>
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
                  <p className="text-sm text-muted-foreground">Monitor your key health metrics over time</p>
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
    </div>
  );
};
