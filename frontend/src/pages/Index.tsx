import { useState, useEffect } from "react";
import { Users, Bot, FileInput, Activity, AlertTriangle, BrainCircuit } from "lucide-react";
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

const Index = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [showChat, setShowChat] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.email) {
      fetchDashboardStats();
    }
  }, [user?.email]);

  const fetchDashboardStats = async () => {
    try {
      const headers: HeadersInit = {};
      if (user?.email) {
        headers['X-User-Email'] = user.email;
      }
      
      const response = await fetch(`${API_URL}/api/dashboard/stats`, { headers });
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

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <Navbar />

      {/* Main Content */}
      <main className="container mx-auto px-6 py-10">
        <div className="flex gap-6">
          {/* Dashboard Section */}
          <div className={cn(
            "transition-all duration-500 ease-smooth",
            showReport ? "w-[60%]" : "w-full"
          )}>
            {/* Welcome Section */}
            <div className="mb-8">
              <div className="inline-block">
                <h2 className="text-4xl font-bold bg-gradient-to-r from-medical-pink via-medical-blue to-medical-pink bg-clip-text text-transparent mb-3 animate-float">
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
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
              <SummaryPanel title="Upcoming Appointments" gradient="blue">
                <div className="space-y-2">
                  <AppointmentItem
                    patientName="Sarah Johnson"
                    time="10:00 AM"
                    type="Routine Checkup"
                  />
                  <AppointmentItem
                    patientName="Emily Davis"
                    time="11:30 AM"
                    type="Ultrasound"
                  />
                  <AppointmentItem
                    patientName="Maria Garcia"
                    time="2:00 PM"
                    type="Follow-up"
                  />
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
          </div>

          {/* Report Panel - Slides in from right */}
          {showReport && (
            <div className="w-[40%] transition-all duration-500 ease-smooth animate-in slide-in-from-right">
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