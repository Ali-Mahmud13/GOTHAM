import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import { ChatPage } from "./pages/ChatPage";
import PatientsPage from "./pages/PatientsPage";
import PatientProfilePage from "./pages/PatientProfilePage";
import DataEntry from "./pages/DataEntry";
import { LandingPage } from "./pages/LandingPage";
import { PatientLoginPage } from "./pages/PatientLoginPage";
import { PatientSignupPage } from "./pages/PatientSignupPage";
import { DoctorLoginPage } from "./pages/DoctorLoginPage";
import { DoctorSignupPage } from "./pages/DoctorSignupPage";
import { PatientDashboard } from "./pages/PatientDashboard";
import { PatientNotesPage } from "./pages/PatientNotesPage";
import { EditProfilePage } from "./pages/EditProfilePage";
import { DoctorSchedulePage } from "./pages/DoctorSchedulePage";
import { BookAppointmentPage } from "./pages/BookAppointmentPage";
import { AppointmentsPage } from "./pages/AppointmentsPage";
import { AuthProvider } from "./context/AuthContext";
import { PatientAuthProvider } from "./context/PatientAuthContext";
import { GothamWelcomePage } from "./pages/GothamWelcomePage";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { FindDoctorPage } from "./pages/FindDoctorPage";
import { DoctorEditProfilePage } from "./pages/DoctorEditProfilePage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
    },
  },
});

function RequireDoctor({ children }: { children: JSX.Element }) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/doctor/login" replace />;
  if (user?.role !== "doctor") return <Navigate to="/patient/dashboard" replace />;
  return children;
}

function RequireAdmin({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isAdmin } = useAuth();
  if (!isAuthenticated) return <Navigate to="/doctor/login" replace />;
  if (!isAdmin) return <Navigate to="/dashboard" replace />;
  return children;
}

function RequirePatient({ children }: { children: JSX.Element }) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/patient/login" replace />;
  if (user?.role !== "patient") return <Navigate to="/dashboard" replace />;
  return children;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <PatientAuthProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              {/* Landing Page */}
              <Route path="/" element={<LandingPage />} />
              
              {/* Doctor Login & Dashboard Routes */}
              <Route path="/doctor/login" element={<DoctorLoginPage />} />
              <Route path="/doctor/signup" element={<DoctorSignupPage />} />
              <Route path="/login" element={<Navigate to="/doctor/login" replace />} />
              <Route path="/signup" element={<Navigate to="/doctor/signup" replace />} />
              <Route path="/dashboard" element={<RequireDoctor><Index /></RequireDoctor>} />
              <Route path="/chat" element={<RequireDoctor><ChatPage /></RequireDoctor>} />
              <Route path="/patients" element={<RequireDoctor><PatientsPage /></RequireDoctor>} />
              <Route path="/patients/:patientId" element={<RequireDoctor><PatientProfilePage /></RequireDoctor>} />
              <Route path="/data-entry" element={<RequireDoctor><DataEntry /></RequireDoctor>} />
              <Route path="/schedule" element={<RequireDoctor><DoctorSchedulePage /></RequireDoctor>} />
              <Route path="/appointments" element={<RequireDoctor><AppointmentsPage /></RequireDoctor>} />
              <Route path="/doctor/welcome" element={<RequireDoctor><GothamWelcomePage /></RequireDoctor>} />
              <Route path="/admin" element={<RequireAdmin><AdminDashboardPage /></RequireAdmin>} />
              
              {/* Patient Portal Routes */}
              <Route path="/patient/login" element={<PatientLoginPage />} />
              <Route path="/patient/signup" element={<PatientSignupPage />} />
              <Route path="/patient/dashboard" element={<RequirePatient><PatientDashboard /></RequirePatient>} />
              <Route path="/patient/notes" element={<RequirePatient><PatientNotesPage /></RequirePatient>} />
              <Route path="/patient/edit-profile" element={<RequirePatient><EditProfilePage /></RequirePatient>} />
              <Route path="/patient/book-appointment" element={<RequirePatient><BookAppointmentPage /></RequirePatient>} />
              <Route path="/patient/appointments" element={<RequirePatient><AppointmentsPage /></RequirePatient>} />
              <Route path="/patient/find-doctor" element={<RequirePatient><FindDoctorPage /></RequirePatient>} />
              <Route path="/doctor/edit-profile" element={<RequireDoctor><DoctorEditProfilePage /></RequireDoctor>} />
              
              {/* 404 */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </PatientAuthProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;