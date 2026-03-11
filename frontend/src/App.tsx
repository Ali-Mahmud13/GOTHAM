import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
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
import { EditProfilePage } from "./pages/EditProfilePage";
import { DoctorSchedulePage } from "./pages/DoctorSchedulePage";
import { BookAppointmentPage } from "./pages/BookAppointmentPage";
import { AppointmentsPage } from "./pages/AppointmentsPage";
import { AuthProvider } from "./context/AuthContext";
import { PatientAuthProvider } from "./context/PatientAuthContext";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
    },
  },
});

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
              <Route path="/dashboard" element={<Index />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/patients" element={<PatientsPage />} />
              <Route path="/patients/:patientId" element={<PatientProfilePage />} />
              <Route path="/data-entry" element={<DataEntry />} />
              <Route path="/schedule" element={<DoctorSchedulePage />} />
              <Route path="/appointments" element={<AppointmentsPage />} />
              
              {/* Patient Portal Routes */}
              <Route path="/patient/login" element={<PatientLoginPage />} />
              <Route path="/patient/signup" element={<PatientSignupPage />} />
              <Route path="/patient/dashboard" element={<PatientDashboard />} />
              <Route path="/patient/edit-profile" element={<EditProfilePage />} />
              <Route path="/patient/book-appointment" element={<BookAppointmentPage />} />
              <Route path="/patient/appointments" element={<AppointmentsPage />} />
              
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