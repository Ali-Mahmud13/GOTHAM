import { Bell, User, CalendarDays, LayoutDashboard, ShieldCheck, CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react";
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

interface RegRequest {
  id: number;
  patient_name: string;
  appointment_date: string | null;
  appointment_start_time: string | null;
}

interface RescheduleNotif {
  id: number;
  patient_name: string;
  appointment_date: string;
  start_time: string;
}

interface NewBookingNotif {
  id: number;
  patient_name: string;
  appointment_date: string;
  start_time: string;
  status: string;
}

export const Navbar = () => {
  const { user, logout, tokens, setTokens, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [regRequests, setRegRequests] = useState<RegRequest[]>([]);
  const [seenReqIds, setSeenReqIds] = useState<Set<number>>(new Set());
  const [rescheduleNotifs, setRescheduleNotifs] = useState<RescheduleNotif[]>([]);
  const [cancelNotifs, setCancelNotifs] = useState<RescheduleNotif[]>([]);
  const [regActionLoading, setRegActionLoading] = useState<number | null>(null);
  const [newBookings, setNewBookings] = useState<NewBookingNotif[]>([]);

  // Load persisted seen IDs from localStorage
  useEffect(() => {
    if (user?.email) {
      const stored = localStorage.getItem(`dr_seen_reqs_${user.email}`);
      if (stored) setSeenReqIds(new Set(JSON.parse(stored)));
    }
  }, [user?.email]);

  useEffect(() => {
    if (user?.email && user?.role === "doctor") {
      fetchRegRequests();
      fetchRescheduleNotifs();
      fetchCancelNotifs();
      fetchNewBookings();
      const interval = setInterval(() => {
        fetchRegRequests();
        fetchRescheduleNotifs();
        fetchCancelNotifs();
        fetchNewBookings();
      }, 60000);
      return () => clearInterval(interval);
    }
  }, [user?.email]);

  const fetchRegRequests = async () => {
    try {
      const res = await apiFetch(
        `/appointments/registration-requests`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        const data: RegRequest[] = await res.json();
        setRegRequests(data);
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

  const fetchNewBookings = async () => {
    try {
      const res = await apiFetch(
        `/appointments/new-booking-notifications`,
        { method: "GET" },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        setNewBookings(await res.json());
      }
    } catch { }
  };

  const handleNotifOpen = async (open: boolean) => {
    if (open) {
      // Persist seen reg request IDs to localStorage
      const allIds = new Set([...seenReqIds, ...regRequests.map(r => r.id)]);
      setSeenReqIds(allIds);
      if (user?.email) localStorage.setItem(`dr_seen_reqs_${user.email}`, JSON.stringify([...allIds]));
      // Dismiss new-booking-notifications
      if (newBookings.length > 0) {
        try {
          await apiFetch(
            `/appointments/dismiss-new-booking-notifications`,
            { method: "PUT" },
            tokens,
            setTokens,
            logout,
          );
          setNewBookings([]);
        } catch { }
      }
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

  const handleRegAction = async (reqId: number, action: 'approve' | 'decline') => {
    setRegActionLoading(reqId);
    try {
      const res = await apiFetch(
        `/appointments/registration-requests/${reqId}/${action}`,
        { method: 'PUT' },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        setRegRequests(prev => prev.filter(r => r.id !== reqId));
        const newSeen = new Set(seenReqIds);
        newSeen.delete(reqId);
        setSeenReqIds(newSeen);
      }
    } catch { } finally { setRegActionLoading(null); }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  // Get display name
  const displayName = user?.full_name || user?.email?.split("@")[0] || "Doctor";
  const displayRole = user?.role === "doctor" ? "Doctor" : "Patient";
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
              <h1 className="text-lg sm:text-xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                GOTHAM
              </h1>
              <p className="hidden sm:block text-xs text-muted-foreground -mt-1">
                Antenatal Risk Platform
              </p>
            </div>
          </div>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => navigate('/schedule')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
            >
              <CalendarDays className="w-4 h-4" />
              My Schedule
            </button>
            <button
              onClick={() => navigate('/appointments')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
            >
              <CalendarDays className="w-4 h-4" />
              Appointments
            </button>
            {isAdmin && (
              <button
                onClick={() => navigate('/admin')}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-amber-600 hover:text-amber-700 hover:bg-amber-500/10 transition-all"
              >
                <ShieldCheck className="w-4 h-4" />
                Admin
              </button>
            )}
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-2">
          {/* Notifications */}
            <DropdownMenu onOpenChange={handleNotifOpen}>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="relative hover:bg-muted/50 transition-all duration-300"
                >
                  <Bell className="h-5 w-5" />
                  {(regRequests.some(r => !seenReqIds.has(r.id)) || rescheduleNotifs.length > 0 || cancelNotifs.length > 0 || newBookings.length > 0) && (
                    <span className="absolute top-1 right-1 h-4 w-4 bg-destructive rounded-full text-[10px] text-white font-bold flex items-center justify-center leading-none">
                      {(regRequests.filter(r => !seenReqIds.has(r.id)).length + rescheduleNotifs.length + cancelNotifs.length + newBookings.length) > 9
                        ? "9+"
                        : regRequests.filter(r => !seenReqIds.has(r.id)).length + rescheduleNotifs.length + cancelNotifs.length + newBookings.length}
                    </span>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80 bg-card/95 backdrop-blur-xl border-border/50">
                <DropdownMenuLabel>Notifications</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {regRequests.length === 0 && rescheduleNotifs.length === 0 && cancelNotifs.length === 0 && newBookings.length === 0 ? (
                  <DropdownMenuItem className="py-4 text-muted-foreground text-sm justify-center" onSelect={(e) => e.preventDefault()}>
                    No new notifications
                  </DropdownMenuItem>
                ) : (
                  <>
                    {cancelNotifs.slice(0, 2).map((n) => (
                      <DropdownMenuItem key={`cn-${n.id}`} className="py-2.5" onSelect={(e) => e.preventDefault()}>
                        <div className="flex items-start gap-2 w-full">
                          <XCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium text-sm">Appointment Cancelled</p>
                            <p className="text-xs text-muted-foreground">
                              {n.patient_name} cancelled on{' '}
                              {new Date(n.appointment_date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} at {n.start_time}
                            </p>
                          </div>
                        </div>
                      </DropdownMenuItem>
                    ))}
                    {rescheduleNotifs.slice(0, 2).map((n) => (
                      <DropdownMenuItem key={`rs-${n.id}`} className="py-2.5" onSelect={(e) => e.preventDefault()}>
                        <div className="flex items-start gap-2 w-full">
                          <Clock className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium text-sm">Appointment Rescheduled</p>
                            <p className="text-xs text-muted-foreground">
                              {n.patient_name} moved to{' '}
                              {new Date(n.appointment_date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} at {n.start_time}
                            </p>
                          </div>
                        </div>
                      </DropdownMenuItem>
                    ))}
                    {newBookings.slice(0, 3).map((n) => (
                      <DropdownMenuItem
                        key={`nb-${n.id}`}
                        className="py-2.5 cursor-pointer"
                        onSelect={() => navigate('/appointments')}
                      >
                        <div className="flex items-start gap-2 w-full">
                          <Bell className="h-4 w-4 text-medical-blue flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium text-sm">
                              {n.status === 'pending_approval' ? 'Registration Request Booking' : 'New Appointment'}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {n.patient_name} ·{' '}
                              {new Date(n.appointment_date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} at {n.start_time}
                            </p>
                          </div>
                        </div>
                      </DropdownMenuItem>
                    ))}
                    {regRequests.length > 0 && (cancelNotifs.length > 0 || rescheduleNotifs.length > 0 || newBookings.length > 0) && (
                      <DropdownMenuSeparator />
                    )}
                    {regRequests.slice(0, 4).map((req) => (
                      <DropdownMenuItem
                        key={req.id}
                        className="py-2.5 flex-col items-start"
                        onSelect={(e) => e.preventDefault()}
                      >
                        <div className="flex items-start gap-2 w-full mb-2">
                          <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm">Registration Request</p>
                            <p className="text-xs text-muted-foreground truncate">
                              {req.patient_name} wants to register under you
                              {req.appointment_date
                                ? ` · ${new Date(req.appointment_date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} at ${req.appointment_start_time}`
                                : ""}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2 w-full pl-6">
                          <button
                            disabled={regActionLoading === req.id}
                            onClick={() => handleRegAction(req.id, 'approve')}
                            className="flex-1 inline-flex items-center justify-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50"
                          >
                            <CheckCircle className="h-3 w-3" />
                            {regActionLoading === req.id ? '…' : 'Approve'}
                          </button>
                          <button
                            disabled={regActionLoading === req.id}
                            onClick={() => handleRegAction(req.id, 'decline')}
                            className="flex-1 inline-flex items-center justify-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/20 transition-colors disabled:opacity-50"
                          >
                            <XCircle className="h-3 w-3" />
                            {regActionLoading === req.id ? '…' : 'Decline'}
                          </button>
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
                    <p className="text-sm font-semibold">{displayName}</p>
                    <p className="text-xs text-muted-foreground">{displayRole}</p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-card/95 backdrop-blur-xl border-border/50">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/doctor/edit-profile')} className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  Edit Profile
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive" onClick={handleLogout}>
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Mobile Quick Nav */}
        <div className={`mt-2 grid ${isAdmin ? 'grid-cols-4' : 'grid-cols-3'} gap-2 md:hidden`}>
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Dashboard
          </button>
          <button
            onClick={() => navigate('/schedule')}
            className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
          >
            <CalendarDays className="w-3.5 h-3.5" />
            Schedule
          </button>
          <button
            onClick={() => navigate('/appointments')}
            className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
          >
            <CalendarDays className="w-3.5 h-3.5" />
            Appts
          </button>
          {isAdmin && (
            <button
              onClick={() => navigate('/admin')}
              className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-medium text-amber-600 hover:text-amber-700 hover:bg-amber-500/10 transition-all"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Admin
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};
