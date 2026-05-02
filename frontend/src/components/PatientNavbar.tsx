import { User, LogOut, Edit, CalendarDays, LayoutDashboard, Bell, CheckCircle, XCircle, Clock } from "lucide-react";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "@/lib/apiClient";

const API_URL = "http://localhost:8000";

interface RegResult {
  id: number;
  patient_name: string; // reused for doctor name from our endpoint
  patient_email: string;
  appointment_date: string | null;
  appointment_start_time: string | null;
  status: string;
}

interface RescheduleNotif {
  id: number;
  doctor_name: string;
  appointment_date: string;
  start_time: string;
}

interface CancelNotif {
  id: number;
  doctor_name: string;
  appointment_date: string;
  start_time: string;
}

export const PatientNavbar = () => {
  const { user, logout, tokens, setTokens } = useAuth();
  const navigate = useNavigate();
  const [regResults, setRegResults] = useState<RegResult[]>([]);
  const [seenResultIds, setSeenResultIds] = useState<Set<number>>(new Set());
  const [rescheduleNotifs, setRescheduleNotifs] = useState<RescheduleNotif[]>([]);
  const [cancelNotifs, setCancelNotifs] = useState<CancelNotif[]>([]);

  const patientName = user?.patient_info?.name || user?.full_name || user?.email || 'Patient';

  // Load persisted seen IDs from localStorage
  useEffect(() => {
    if (user?.email) {
      const stored = localStorage.getItem(`pt_seen_reqs_${user.email}`);
      if (stored) setSeenResultIds(new Set(JSON.parse(stored)));
    }
  }, [user?.email]);

  useEffect(() => {
    if (user?.email && user?.role === "patient") {
      fetchRegResults();
      fetchRescheduleNotifs();
      fetchCancelNotifs();
      const interval = setInterval(() => { fetchRegResults(); fetchRescheduleNotifs(); fetchCancelNotifs(); }, 60000);
      return () => clearInterval(interval);
    }
  }, [user?.email]);

  const fetchRegResults = async () => {
    try {
      const res = await apiFetch(
        `/appointments/my-registration-requests`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data: RegResult[] = await res.json();
        setRegResults(data);
      }
    } catch {
      // silently fail
    }
  };

  const fetchRescheduleNotifs = async () => {
    try {
      const res = await apiFetch(
        `/appointments/reschedule-notifications`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data = await res.json();
        setRescheduleNotifs(data);
      }
    } catch { }
  };

  const fetchCancelNotifs = async () => {
    try {
      const res = await apiFetch(
        `/appointments/cancel-notifications`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data = await res.json();
        setCancelNotifs(data);
      }
    } catch { }
  };

  // Only show badge for actioned (approved/declined) results not yet seen, + reschedule/cancel notifs
  const actionedResults = regResults.filter(r => r.status === "approved" || r.status === "declined");
  const unseenActioned = actionedResults.filter(r => !seenResultIds.has(r.id));
  const unreadCount = unseenActioned.length + rescheduleNotifs.length + cancelNotifs.length;

  const handleNotifOpen = async (open: boolean) => {
    if (open) {
      // Persist seen actioned IDs
      const allIds = new Set([...seenResultIds, ...actionedResults.map(r => r.id)]);
      setSeenResultIds(allIds);
      if (user?.email) localStorage.setItem(`pt_seen_reqs_${user.email}`, JSON.stringify([...allIds]));
    } else {
      // Dismiss reschedule and cancel notifications server-side when closing
      if (rescheduleNotifs.length > 0) {
        try {
          await apiFetch(
            `/appointments/dismiss-reschedule-notifications`,
            { method: "PUT" },
            tokens,
            setTokens,
            logout,
          );
          setRescheduleNotifs([]);
        } catch { }
      }
      if (cancelNotifs.length > 0) {
        try {
          await apiFetch(
            `/appointments/dismiss-cancel-notifications`,
            { method: "PUT" },
            tokens,
            setTokens,
            logout,
          );
          setCancelNotifs([]);
        } catch { }
      }
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/patient/login');
  };

  return (
    <nav className="border-b border-border/40 bg-card/30 backdrop-blur-xl sticky top-0 z-50">
      <div className="container mx-auto px-3 sm:px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-lg blur-md opacity-20 animate-glow-pulse" />
              <div className="relative p-1 rounded-lg">
                <img src="/logo.png" alt="GOTHAM Logo" className="h-8 w-8 object-contain" />
              </div>
            </div>
            <div>
              <h1 className="text-base sm:text-xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                GOTHAM Patient Portal
              </h1>
              <p className="hidden sm:block text-xs text-muted-foreground -mt-1">
                Your Health Dashboard
              </p>
            </div>
          </div>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            <button
              onClick={() => navigate('/patient/dashboard')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => navigate('/patient/book-appointment')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
            >
              <CalendarDays className="w-4 h-4" />
              Book Appointment
            </button>
            <button
              onClick={() => navigate('/patient/appointments')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
            >
              <CalendarDays className="w-4 h-4" />
              Appointments
            </button>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-2">
            {/* Notifications */}
            <DropdownMenu onOpenChange={handleNotifOpen}>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="relative hover:bg-muted/50 transition-all duration-300">
                  <Bell className="h-5 w-5" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 h-4 w-4 bg-destructive rounded-full text-[10px] text-white font-bold flex items-center justify-center leading-none">
                      {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80 bg-card/95 backdrop-blur-xl border-border/50">
                <DropdownMenuLabel>Notifications</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {regResults.length === 0 && rescheduleNotifs.length === 0 && cancelNotifs.length === 0 ? (
                  <DropdownMenuItem className="py-3 text-muted-foreground text-sm justify-center" onSelect={(e) => e.preventDefault()}>
                    No notifications
                  </DropdownMenuItem>
                ) : (
                  <>
                    {cancelNotifs.slice(0, 3).map((n) => (
                      <DropdownMenuItem key={`cn-${n.id}`} className="py-3" onSelect={(e) => e.preventDefault()}>
                        <div className="flex items-start gap-2 w-full">
                          <XCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium text-sm">Appointment Cancelled</p>
                            <p className="text-xs text-muted-foreground">
                              Dr. {n.doctor_name} cancelled the appointment on {new Date(n.appointment_date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} at {n.start_time}
                            </p>
                          </div>
                        </div>
                      </DropdownMenuItem>
                    ))}
                    {rescheduleNotifs.slice(0, 3).map((n) => (
                      <DropdownMenuItem key={`rs-${n.id}`} className="py-3" onSelect={(e) => e.preventDefault()}>
                        <div className="flex items-start gap-2 w-full">
                          <Clock className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium text-sm">Appointment Rescheduled</p>
                            <p className="text-xs text-muted-foreground">
                              Dr. {n.doctor_name} rescheduled to {new Date(n.appointment_date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} at {n.start_time}
                            </p>
                          </div>
                        </div>
                      </DropdownMenuItem>
                    ))}
                    {regResults.slice(0, 5 - Math.min(cancelNotifs.length + rescheduleNotifs.length, 5)).map((req) => (
                      <DropdownMenuItem
                        key={req.id}
                        className="py-3"
                        onSelect={(e) => e.preventDefault()}
                      >
                        <div className="flex items-start gap-2 w-full">
                          {req.status === "approved" ? (
                            <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
                          ) : req.status === "declined" ? (
                            <XCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                          ) : (
                            <Clock className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                          )}
                          <div>
                            <p className="font-medium text-sm">
                              Registration {req.status === "approved" ? "Approved" : req.status === "declined" ? "Declined" : "Pending"}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Dr. {req.patient_name}
                              {req.appointment_date
                                ? ` · ${new Date(req.appointment_date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} at ${req.appointment_start_time}`
                                : ""}
                            </p>
                          </div>
                        </div>
                      </DropdownMenuItem>
                    ))}
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* User Profile */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="gap-2 hover:bg-muted/50 transition-all duration-300"
                >
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue flex items-center justify-center">
                    <User className="h-5 w-5 text-white" />
                  </div>
                  <div className="text-left hidden md:block">
                    <p className="text-sm font-semibold">{patientName || 'Patient'}</p>
                    <p className="text-xs text-muted-foreground">Patient</p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-card/95 backdrop-blur-xl border-border/50">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/patient/edit-profile')} className="cursor-pointer">
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Profile
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Mobile Quick Nav */}
        <div className="md:hidden mt-2 grid grid-cols-3 gap-2">
          <button
            onClick={() => navigate('/patient/dashboard')}
            className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Dashboard
          </button>
          <button
            onClick={() => navigate('/patient/book-appointment')}
            className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
          >
            <CalendarDays className="w-3.5 h-3.5" />
            Book
          </button>
          <button
            onClick={() => navigate('/patient/appointments')}
            className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
          >
            <CalendarDays className="w-3.5 h-3.5" />
            Appointments
          </button>
        </div>
      </div>
    </nav>
  );
};
