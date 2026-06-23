import { useState } from "react";
import { Users, Bot, FileInput, AlertTriangle, BrainCircuit, Calendar, CalendarPlus, UserCheck, UserX, Clock, X, ArrowLeft, Loader2, ChevronRight } from "lucide-react";
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
import { useApiMutation, useApiQuery } from "@/hooks/useApiQuery";
import { queryKeys } from "@/lib/queryKeys";

interface DashboardStats {
  user_role?: string;
  doctor_name?: string;
  total_patients: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  unassessed_count: number;
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
  start_at_utc: string;
  end_at_utc: string;
  status: string;
  notes: string | null;
}

interface WeeklyAssessmentRun {
  visit_id: number;
  patient_name: string;
  patient_identifier: string;
  run_at: string;
  assessment_type: 'Complete' | 'Maternal' | 'Fetal';
  gdm: { risk_level: number | null; confidence: number | null; ai_report: string | null } | null;
  anemia: { diagnosis: string | null; confidence: number | null; ai_report: string | null } | null;
  fetal: { status: number | null; confidence: number | null; ai_report: string | null } | null;
  preeclampsia: { risk_level: number | null; confidence: number | null; ai_report: string | null } | null;
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
  const { user } = useAuth();
  const [showChat, setShowChat] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [selectedRun, setSelectedRun] = useState<WeeklyAssessmentRun | null>(null);
  const [regRequestActionId, setRegRequestActionId] = useState<number | null>(null);
  const statsQuery = useApiQuery<DashboardStats>(
    queryKeys.dashboard.stats,
    "/api/dashboard/stats",
  );
  const appointmentsQuery = useApiQuery<Appointment[]>(
    queryKeys.appointments.upcoming,
    "/appointments/upcoming",
  );
  const regRequestsQuery = useApiQuery<RegistrationRequest[]>(
    queryKeys.registration.doctorRequests,
    "/appointments/registration-requests",
  );
  const newBookingsQuery = useApiQuery<Array<{ id: number }>>(
    queryKeys.notifications.newBookings,
    "/appointments/new-booking-notifications",
  );
  const weeklyAssessmentsQuery = useApiQuery<WeeklyAssessmentRun[]>(
    queryKeys.dashboard.weeklyAssessments,
    "/api/dashboard/assessments/week",
    { enabled: showAssessmentModal },
  );
  const stats = statsQuery.data ?? null;
  const appointments = appointmentsQuery.data ?? [];
  const regRequests = regRequestsQuery.data ?? [];
  const weeklyAssessments = weeklyAssessmentsQuery.data ?? [];
  const newBookingCount = newBookingsQuery.data?.length ?? 0;
  const registrationAction = useApiMutation<void, { id: number; action: "approve" | "decline" }>({
    invalidate: [
      queryKeys.registration.doctorRequests,
      queryKeys.appointments.all,
      queryKeys.patients.all,
      queryKeys.dashboard.stats,
    ],
    mutationFn: ({ id, action }, request) =>
      request<void>(`/appointments/registration-requests/${id}/${action}`, {
        method: "PUT",
      }),
  });
  const dismissNewBookings = useApiMutation<void, void>({
    invalidate: [queryKeys.notifications.newBookings],
    mutationFn: (_, request) =>
      request<void>("/appointments/dismiss-new-booking-notifications", {
        method: "PUT",
      }),
  });

  const dismissNewBookingNotifications = () => dismissNewBookings.mutateAsync();

  const approveRequest = async (id: number) => {
    if (regRequestActionId) return;
    setRegRequestActionId(id);
    try {
      await registrationAction.mutateAsync({ id, action: "approve" });
      toast({ title: "Approved", description: "Registration request approved." });
    } catch (error) {
      toast({ variant: "destructive", title: "Approve failed", description: error instanceof Error ? error.message : "Could not approve request." });
    } finally {
      setRegRequestActionId(null);
    }
  };

  const declineRequest = async (id: number) => {
    if (regRequestActionId) return;
    setRegRequestActionId(id);
    try {
      await registrationAction.mutateAsync({ id, action: "decline" });
      toast({ title: "Declined", description: "Registration request declined." });
    } catch (error) {
      toast({ variant: "destructive", title: "Decline failed", description: error instanceof Error ? error.message : "Could not decline request." });
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
                value={statsQuery.isPending ? "..." : String(stats?.total_patients || 0)}
                subtext="active in system"
                icon={Users}
                trend="up"
                trendValue=""
                color="blue"
              />
              <MetricsCard
                title="High-Risk Alerts"
                value={statsQuery.isPending ? "..." : String(stats?.high_risk_count || 0)}
                subtext="need attention"
                icon={AlertTriangle}
                trend="down"
                trendValue=""
                color="pink"
              />
              <MetricsCard
                title="AI Assessments"
                value={statsQuery.isPending ? "..." : String(stats?.assessments_this_week || 0)}
                subtext="this week"
                icon={BrainCircuit}
                trend="up"
                trendValue=""
                color="purple"
                onClick={() => setShowAssessmentModal(true)}
              />
            </div>

            {/* Empty State for No Patients */}
            {!statsQuery.isPending && stats && stats.total_patients === 0 && (
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
                  {appointmentsQuery.isPending ? (
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
                        <p className="text-sm font-medium text-muted-foreground whitespace-nowrap">
                          {new Date(appt.start_at_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · {new Date(appt.start_at_utc).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </SummaryPanel>

              <SummaryPanel title="High-Risk Cases" gradient="pink">
                <div className="space-y-2">
                  {statsQuery.isPending ? (
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
                  {statsQuery.isPending ? (
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
            {(regRequestsQuery.isPending || regRequests.length > 0) && (
              <div className="mt-8">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <UserCheck className="h-5 w-5 text-medical-blue" />
                  Patient Registration Requests
                  {regRequests.length > 0 && (
                    <span className="ml-2 bg-medical-pink text-white text-xs px-2 py-0.5 rounded-full font-semibold">{regRequests.length}</span>
                  )}
                </h3>
                {regRequestsQuery.isPending ? (
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

      {/* AI Assessments Modal */}
      {showAssessmentModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card/95 backdrop-blur-xl rounded-2xl border border-border/50 shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
              {selectedRun ? (
                <button onClick={() => setSelectedRun(null)} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
                  <ArrowLeft className="h-4 w-4" /> Back
                </button>
              ) : (
                <h2 className="text-lg font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                  AI Assessments This Week
                </h2>
              )}
              <button onClick={() => { setShowAssessmentModal(false); setSelectedRun(null); }}
                className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors">
                <X className="h-5 w-5 text-muted-foreground" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6">
              {!selectedRun && (
                weeklyAssessmentsQuery.isLoading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
                  </div>
                ) : weeklyAssessmentsQuery.isError ? (
                  <div className="text-center py-12">
                    <AlertTriangle className="h-10 w-10 mx-auto text-destructive mb-3" />
                    <p className="text-sm font-semibold text-foreground">Could not load assessments.</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {weeklyAssessmentsQuery.error?.message || "Please try again in a moment."}
                    </p>
                    <button
                      onClick={() => weeklyAssessmentsQuery.refetch()}
                      className="mt-4 px-4 py-2 rounded-lg bg-gradient-to-r from-medical-pink to-medical-blue text-white text-xs font-semibold hover:opacity-90 transition-opacity"
                    >
                      Retry
                    </button>
                  </div>
                ) : weeklyAssessments.length === 0 ? (
                  <p className="text-center text-muted-foreground py-12 text-sm">No assessments run this week.</p>
                ) : (
                  <div className="space-y-3">
                    {weeklyAssessmentsQuery.isFetching && (
                      <p className="text-xs text-muted-foreground text-right">Updating...</p>
                    )}
                    {weeklyAssessments.map(run => (
                      <button key={run.visit_id} onClick={() => setSelectedRun(run)}
                        className="w-full text-left p-4 rounded-xl bg-background/50 border border-border/50 hover:border-medical-blue/40 hover:bg-muted/30 transition-all group">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="font-semibold text-foreground">{run.patient_name}</p>
                            <p className="text-xs text-muted-foreground">{run.patient_identifier} · {new Date(run.run_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                              run.assessment_type === 'Complete' ? 'bg-purple-100 text-purple-700' :
                              run.assessment_type === 'Maternal' ? 'bg-pink-100 text-pink-700' :
                              'bg-blue-100 text-blue-700'
                            }`}>{run.assessment_type}</span>
                            <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )
              )}

              {selectedRun && (
                <div className="space-y-4">
                  <div className="mb-2">
                    <h3 className="text-base font-bold text-foreground">{selectedRun.patient_name}</h3>
                    <p className="text-xs text-muted-foreground">{selectedRun.patient_identifier} · {new Date(selectedRun.run_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
                  </div>

                  {selectedRun.gdm && (
                    <div className="p-4 rounded-xl border border-medical-pink/20 bg-medical-pink/5">
                      <p className="text-xs font-bold uppercase tracking-wide text-medical-pink mb-2">GDM Assessment</p>
                      <p className="text-sm font-semibold">Result: {['Normal', 'Elevated', 'High'][selectedRun.gdm.risk_level ?? 0]}</p>
                      {selectedRun.gdm.confidence != null && (
                        <p className="text-xs text-muted-foreground">Confidence: {(selectedRun.gdm.confidence * 100).toFixed(1)}%</p>
                      )}
                      {selectedRun.gdm.ai_report && (
                        <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{selectedRun.gdm.ai_report}</p>
                      )}
                    </div>
                  )}

                  {selectedRun.anemia && (
                    <div className="p-4 rounded-xl border border-violet-200 bg-violet-50/50">
                      <p className="text-xs font-bold uppercase tracking-wide text-violet-700 mb-2">Anemia Assessment</p>
                      <p className="text-sm font-semibold">Result: {selectedRun.anemia.diagnosis ?? '—'}</p>
                      {selectedRun.anemia.confidence != null && (
                        <p className="text-xs text-muted-foreground">Confidence: {(selectedRun.anemia.confidence * 100).toFixed(1)}%</p>
                      )}
                      {selectedRun.anemia.ai_report && (
                        <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{selectedRun.anemia.ai_report}</p>
                      )}
                    </div>
                  )}

                  {selectedRun.fetal && (
                    <div className="p-4 rounded-xl border border-medical-blue/20 bg-medical-blue/5">
                      <p className="text-xs font-bold uppercase tracking-wide text-medical-blue mb-2">Fetal Health Assessment</p>
                      <p className="text-sm font-semibold">Result: {['', 'Normal', 'Suspect', 'Pathological'][selectedRun.fetal.status ?? 0] ?? '—'}</p>
                      {selectedRun.fetal.confidence != null && (
                        <p className="text-xs text-muted-foreground">Confidence: {(selectedRun.fetal.confidence * 100).toFixed(1)}%</p>
                      )}
                      {selectedRun.fetal.ai_report && (
                        <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{selectedRun.fetal.ai_report}</p>
                      )}
                    </div>
                  )}

                  {selectedRun.preeclampsia && (
                    <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/60">
                      <p className="text-xs font-bold uppercase tracking-wide text-amber-700 mb-2">Preeclampsia Assessment</p>
                      <p className="text-sm font-semibold">Result: {['Low', 'Medium', 'High'][selectedRun.preeclampsia.risk_level ?? 0] ?? '—'}</p>
                      {selectedRun.preeclampsia.confidence != null && (
                        <p className="text-xs text-muted-foreground">Confidence: {(selectedRun.preeclampsia.confidence * 100).toFixed(1)}%</p>
                      )}
                      {selectedRun.preeclampsia.ai_report && (
                        <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{selectedRun.preeclampsia.ai_report}</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Index;
