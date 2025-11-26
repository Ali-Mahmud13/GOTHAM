import { useState } from "react";
import { Users, Bot, FileInput } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { DashboardCard } from "@/components/DashboardCard";
import { SummaryPanel } from "@/components/SummaryPanel";
import { AppointmentItem } from "@/components/AppointmentItem";
import { HighRiskCase } from "@/components/HighRiskCase";
import { RecentPatient } from "@/components/RecentPatient";
import { ChatInterface } from "@/components/ChatInterface";
import { RiskReportPanel } from "@/components/RiskReportPanel";
import { cn } from "@/lib/utils";

const Index = () => {
  const navigate = useNavigate();
  const [showChat, setShowChat] = useState(false);
  const [showReport, setShowReport] = useState(false);

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
            <div className="mb-10">
              <div className="inline-block">
                <h2 className="text-4xl font-bold bg-gradient-to-r from-medical-pink via-medical-blue to-medical-pink bg-clip-text text-transparent mb-3 animate-float">
                  Welcome back, Dr. Mahmud
                </h2>
                <div className="h-1 w-32 bg-gradient-to-r from-medical-pink to-medical-blue rounded-full" />
              </div>
              <p className="text-muted-foreground mt-3 text-lg">
                Your comprehensive dashboard overview for today
              </p>
            </div>

            {/* Main Action Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
              <DashboardCard
                title="Patients"
                icon={Users}
                variant="dual-glow"
                onClick={() => console.log("Navigate to patients")}
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
                  <HighRiskCase
                    patientName="Jennifer Wilson"
                    riskLevel="High"
                    condition="Gestational Diabetes"
                  />
                  <HighRiskCase
                    patientName="Amanda Brown"
                    riskLevel="Medium"
                    condition="Preeclampsia Risk"
                  />
                  <HighRiskCase
                    patientName="Lisa Anderson"
                    riskLevel="High"
                    condition="Multiple Pregnancy"
                  />
                </div>
              </SummaryPanel>

              <SummaryPanel title="Recent Patients" gradient="neutral">
                <div className="space-y-2">
                  <RecentPatient name="Rachel Green" lastVisit="2 days ago" />
                  <RecentPatient name="Monica Geller" lastVisit="5 days ago" />
                  <RecentPatient name="Phoebe Buffay" lastVisit="1 week ago" />
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
