import { useState, useEffect } from "react";
import { Users, Bot, FileInput, AlertTriangle, BrainCircuit, Calendar, CalendarPlus, UserCheck, UserX, Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { DashboardCard } from "@/components/DashboardCard";
import { SummaryPanel } from "@/components/SummaryPanel";
import { AppointmentItem } from "@/components/AppointmentItem";
import { HighRiskCase } from "@/components/HighRiskCase";
import { RecentPatient } from "@/components/RecentPatient";
import { ChatInterface } from "@/components/ChatInterface";
import { RiskReportPanel } from "@/components/RiskReportPanel";
import { MetricsCard } from "@/components/MetricsCard";
import { RiskOverviewChart } from "@/components/RiskOverviewChart";
import { RiskTrendChart } from "@/components/RiskTrendChart";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { toast } from "@/components/ui/use-toast";
import { apiFetch } from "@/lib/apiClient";

const API_URL = "http://localhost:8000";

interface DashboardStats {
  user_role?: string;
  doctor_name?: string;
  total_patients: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  total_visits: number;
  assessments_this_week: number;
  high_risk_patients: Array<{
    id: number;
    patient_identifier: string;
    name: string;
    risk_level: string;
    clinical_notes: string | null;
    updated_at: string | null;
  }>;
  recent_patients: Array<{
    id: number;
    patient_identifier: string;
    name: string;
    risk_level: string;
    updated_at: string | null;
  }>;
}

interface Appointment {
  id: number;
  patient_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: string;
  notes: string | null;
}

interface RegistrationRequest {
  id: number;
  patient_id: number;
  patient_name: string;
  patient_email: string;
  doctor_id: number;
  appointment_id: number | null;
  appointment_date: string | null;
  appointment_start_time: string | null;
  status: string;
  created_at: string;
}

const formatApptDate = (d: string) =>
  new Date(d + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" });

const Index = () => {
  const navigate = useNavigate();
  const { user, tokens, setTokens, logout } = useAuth();
  const [showChat, setShowChat] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [apptLoading, setApptLoading] = useState(true);
  const [newBookingCount, setNewBookingCount] = useState(0);
  const [regRequests, setRegRequests] = useState<RegistrationRequest[]>([]);
  const [regRequestsLoading, setRegRequestsLoading] = useState(true);
  const [regRequestActionId, setRegRequestActionId] = useState<number | null>(null);

  useEffect(() => {
    if (user?.email) {
      fetchDashboardStats();
      fetchUpcomingAppointments();
      fetchRegistrationRequests();
      fetchNewBookingNotifications();
    }
  }, [user?.email]);

  const fetchDashboardStats = async () => {
    try {
      const response = await apiFetch(
        `/api/dashboard/stats`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

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
        const data: Appointment[] = await res.json();
        setAppointments(data);
      }
    } catch {
      // silently fail, appointments section will show nothing
    } finally {
      setApptLoading(false);
    }
  };

  const fetchNewBookingNotifications = async () => {
    try {
      const res = await apiFetch(
        `/appointments/new-booking-notifications`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data = await res.json();
        setNewBookingCount(data.count || 0);
      }
    } catch {
      // ignore
    }
  };

  const dismissNewBookingNotifications = async () => {
    try {
      await apiFetch(
        `/appointments/dismiss-new-booking-notifications`,
        { method: "PUT" },
        tokens,
        setTokens,
        logout,
      );
      setNewBookingCount(0);
    } catch {
      // ignore
    }
  };

  const fetchRegistrationRequests = async () => {
    try {
      const res = await apiFetch(
        `/appointments/registration-requests`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data: RegistrationRequest[] = await res.json();
        setRegRequests(data);
      }
    } catch {
      // silently fail
    } finally {
      setRegRequestsLoading(false);
    }
  };

  const approveRequest = async (id: number) => {
    if (regRequestActionId) return;
    setRegRequestActionId(id);
    try {
      const res = await apiFetch(
        `/appointments/registration-requests/${id}/approve`,
        { method: "PUT" },
        tokens,
        setTokens,
        logout,
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast({ variant: "destructive", title: "Approve failed", description: err.detail || "Could not approve request." });
        return;
      }
      fetchRegistrationRequests();
      fetchUpcomingAppointments();
      toast({ title: "Approved", description: "Registration request approved." });
    } catch {
      toast({ variant: "destructive", title: "Network error", description: "Could not approve request." });
    } finally {
      setRegRequestActionId(null);
    }
  };

  const declineRequest = async (id: number) => {
    if (regRequestActionId) return;
    setRegRequestActionId(id);
    try {
      const res = await apiFetch(
        `/appointments/registration-requests/${id}/decline`,
        { method: "PUT" },
        tokens,
        setTokens,
        logout,
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast({ variant: "destructive", title: "Decline failed", description: err.detail || "Could not decline request." });
        return;
      }
      fetchRegistrationRequests();
      toast({ title: "Declined", description: "Registration request declined." });
    } catch {
      toast({ variant: "destructive", title: "Network error", description: "Could not decline request." });
    } finally {
      setRegRequestActionId(null);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <Navbar />

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <div className="flex flex-col xl:flex-row gap-6">
          {/* Dashboard Section */}
          <div className={cn(
            "transition-all duration-500 ease-smooth",
            showReport ? "w-full xl:w-[60%]" : "w-full"
          )}>
            {/* Welcome Section */}
            <div className="mb-8">
              <div className="inline-block">
                <h2 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-medical-pink via-medical-blue to-medical-pink bg-clip-text text-transparent mb-3 animate-float">
                  Welcome back, {stats?.doctor_name || user?.full_name || 'Doctor'}
                </h2>
                <div className="h-1 w-32 bg-gradient-to-r from-medical-pink to-medical-blue rounded-full" />
              </div>
              <p className="text-muted-foreground mt-3 text-lg">
                Your comprehensive dashboard overview for today
              </p>
            </div>

            {/* Metrics Bar */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <MetricsCard
                title="Total Active Patients"
                value={loading ? "..." : String(stats?.total_patients || 0)}
                subtext="active in system"
                icon={Users}
                trend="up"
                trendValue=""
                color="blue"
              />
              <MetricsCard
                title="High-Risk Alerts"
                value={loading ? "..." : String(stats?.high_risk_count || 0)}
                subtext="need attention"
                icon={AlertTriangle}
                trend="down"
                trendValue=""
                color="pink"
              />
              <MetricsCard
                title="AI Assessments"
                value={loading ? "..." : String(stats?.assessments_this_week || 0)}
                subtext="this week"
                icon={BrainCircuit}
                trend="up"
                trendValue=""
                color="purple"
              />
            </div>

            {/* Empty State for No Patients */}
            {!loading && stats && stats.total_patients === 0 && (
              <div className="bg-gradient-to-br from-medical-pink/10 via-medical-blue/10 to-purple-500/10 rounded-2xl p-12 text-center mb-12 border border-medical-pink/20">
                <div className="max-w-md mx-auto">
                  <Users className="w-16 h-16 mx-auto mb-4 text-medical-blue" />
                  <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                    No Patients Yet
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    Get started by adding your first patient to begin tracking maternal health data and assessments.
                  </p>
                  <button
                    onClick={() => navigate("/patients")}
                    className="px-6 py-3 bg-gradient-to-r from-medical-pink to-medical-blue text-white rounded-lg font-semibold hover:shadow-lg transition-all duration-300 hover:scale-105"
                  >
                    Add First Patient
                  </button>
                </div>
              </div>
            )}

            {/* Main Action Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 mb-12">
              <DashboardCard
                title="Patients"
                icon={Users}
                variant="dual-glow"
                onClick={() => navigate("/patients")}
              />
              <DashboardCard
                title="AI Assistant"
                icon={Bot}
                variant="gradient"
                onClick={() => navigate("/chat")}
              />
              <DashboardCard
                title="New Data Entry"
                icon={FileInput}
                variant="dual-glow"
                onClick={() => navigate("/data-entry")}
              />
              <DashboardCard
                title="My Schedule"
                icon={CalendarPlus}
                variant="dual-glow"
                onClick={() => navigate("/schedule")}
              />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
              <div className="lg:col-span-1">
                <RiskOverviewChart />
              </div>
              <div className="lg:col-span-2">
                <RiskTrendChart />
              </div>
            </div>

            {/* Summary Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <SummaryPanel
                title={
                  <span className="flex items-center gap-2">
                    Upcoming Appointments
                    {newBookingCount > 0 && (
                      <span className="bg-medical-pink text-white text-xs px-2 py-0.5 rounded-full font-semibold">
                        {newBookingCount}
                      </span>
                    )}
                  </span>
                }
                gradient="blue"
                onViewAll={() => {
                  dismissNewBookingNotifications();
                  navigate("/appointments");
                }}
              >
                <div className="space-y-2">
                  {apptLoading ? (
                    <p className="text-sm text-gray-500">Loading...</p>
                  ) : appointments.length === 0 ? (
                    <div className="text-center py-4">
                      <Calendar className="h-8 w-8 mx-auto text-gray-300 mb-2" />
                      <p className="text-sm text-gray-500">No upcoming appointments</p>
                      <button
                        onClick={() => navigate("/schedule")}
                        className="text-xs text-medical-blue hover:underline mt-1"
                      >
                        Set your schedule →
                      </button>
                    </div>
                  ) : (
                    appointments.slice(0, 3).map((appt) => (
                      <div key={appt.id} className="flex items-center gap-3 py-3 border-b border-border last:border-0">
                        <div className="p-2 rounded-lg bg-muted">
                          <Clock className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-foreground truncate">{appt.patient_name}</p>
                            {appt.status === 'pending_approval' && (
                              <span className="flex-shrink-0 text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-semibold">Pending</span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{appt.notes || "Appointment"}</p>
                        </div>
                        <p className="text-sm font-medium text-muted-foreground whitespace-nowrap">{appt.start_time} · {formatApptDate(appt.appointment_date)}</p>
                      </div>
                    ))
                  )}
                </div>
              </SummaryPanel>

              <SummaryPanel title="High-Risk Cases" gradient="pink">
                <div className="space-y-2">
                  {loading ? (
                    <p className="text-sm text-gray-500">Loading...</p>
                  ) : stats && stats.high_risk_patients.length > 0 ? (
                    stats.high_risk_patients.slice(0, 3).map((patient) => (
                      <HighRiskCase
                        key={patient.id}
                        patientName={patient.name}
                        riskLevel="High"
                        condition={patient.clinical_notes?.substring(0, 50) || "Requires attention"}
                      />
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No high-risk cases</p>
                  )}
                </div>
              </SummaryPanel>

              <SummaryPanel title="Recent Patients" gradient="neutral">
                <div className="space-y-2">
                  {loading ? (
                    <p className="text-sm text-gray-500">Loading...</p>
                  ) : stats && stats.recent_patients.length > 0 ? (
                    stats.recent_patients.slice(0, 3).map((patient) => (
                      <RecentPatient
                        key={patient.id}
                        name={patient.name}
                        lastVisit={patient.updated_at ? new Date(patient.updated_at).toLocaleDateString() : "Unknown"}
                      />
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No recent patients</p>
                  )}
                </div>
              </SummaryPanel>
            </div>

            {/* Registration Requests */}
            {(regRequestsLoading || regRequests.length > 0) && (
              <div className="mt-8">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <UserCheck className="h-5 w-5 text-medical-blue" />
                  Patient Registration Requests
                  {regRequests.length > 0 && (
                    <span className="ml-2 bg-medical-pink text-white text-xs px-2 py-0.5 rounded-full font-semibold">{regRequests.length}</span>
                  )}
                </h3>
                {regRequestsLoading ? (
                  <p className="text-sm text-gray-500">Loading...</p>
                ) : (
                  <div className="space-y-3">
                    {regRequests.map(req => (
                      <div key={req.id} className="bg-white rounded-xl border border-yellow-200 shadow-sm p-4 flex flex-col sm:flex-row sm:items-center gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue flex items-center justify-center text-white font-bold text-xs">
                              {req.patient_name[0].toUpperCase()}
                            </div>
                            <div>
                              <p className="font-semibold text-gray-900 text-sm">{req.patient_name}</p>
                              <p className="text-xs text-gray-500">{req.patient_email}</p>
                            </div>
                          </div>
                          {req.appointment_date && (
                            <div className="flex items-center gap-1 text-xs text-gray-600 mt-1.5 ml-10">
                              <Clock className="h-3 w-3" />
                              <span>Appointment: {formatApptDate(req.appointment_date)} at {req.appointment_start_time}</span>
                            </div>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => approveRequest(req.id)}
                            disabled={regRequestActionId === req.id}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-600 text-white text-xs font-semibold hover:bg-green-700 transition-colors"
                          >
                            <UserCheck className="h-3 w-3" /> Approve
                          </button>
                          <button
                            onClick={() => declineRequest(req.id)}
                            disabled={regRequestActionId === req.id}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-100 text-red-700 border border-red-200 text-xs font-semibold hover:bg-red-200 transition-colors"
                          >
                            <UserX className="h-3 w-3" /> Decline
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Report Panel - Slides in from right */}
          {showReport && (
            <div className="w-full xl:w-[40%] transition-all duration-500 ease-smooth animate-in slide-in-from-right">
              <RiskReportPanel onClose={() => setShowReport(false)} />
            </div>
          )}
        </div>
      </main>

      {/* Chat Interface - Full Screen Overlay */}
      {showChat && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-in fade-in duration-300">
          <div className={cn(
            "w-full max-w-4xl h-[80vh] transition-all duration-500 ease-smooth",
            showReport ? "max-w-2xl" : "max-w-4xl"
          )}>
            <ChatInterface
              onClose={() => {
                setShowChat(false);
                setShowReport(false);
              }}
              showReport={showReport}
              onShowReport={setShowReport}
            />
          </div>

          {/* Report Panel in Chat View */}
          {showReport && (
            <div className="w-full max-w-2xl h-[80vh] ml-6 animate-in slide-in-from-right duration-500">
              <RiskReportPanel onClose={() => setShowReport(false)} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Index;