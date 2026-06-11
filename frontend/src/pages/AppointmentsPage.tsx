import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, User, Loader2, CheckCircle, AlertCircle, XCircle, RefreshCw, UserX, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Navbar } from '@/components/Navbar';
import { PatientNavbar } from '@/components/PatientNavbar';
import { useAuth } from '@/context/AuthContext';
import { apiFetch } from '@/lib/apiClient';

interface Appointment {
  id: number;
  doctor_id: number;
  doctor_name: string;
  patient_id: number;
  patient_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  timezone: string;
  status: string;
  notes: string | null;
  created_at: string;
  is_registered: boolean;
}

interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  booked: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
  rescheduled: 'bg-yellow-100 text-yellow-800',
  pending_approval: 'bg-amber-100 text-amber-800',
};

const STATUS_LABELS: Record<string, string> = {
  booked: 'Booked',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rescheduled: 'Rescheduled',
  pending_approval: 'Pending Approval',
};

const formatDate = (d: string) =>
  new Date(d + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });

function tomorrowISO(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().split('T')[0];
}

function todayISO(): string {
  return new Date().toISOString().split('T')[0];
}

function isFuture(appt: Appointment): boolean {
  const today = todayISO();
  const now = new Date().toTimeString().slice(0, 5);
  if (appt.appointment_date > today) return true;
  if (appt.appointment_date === today && appt.start_time >= now) return true;
  return false;
}

function getStatusDisplay(appt: Appointment): { label: string; color: string } {
  if (!isFuture(appt)) {
    if (appt.status === 'booked') return { label: 'Completed', color: 'bg-green-100 text-green-800' };
    if (appt.status === 'pending_approval') return { label: 'Expired', color: 'bg-gray-100 text-gray-600' };
  }
  return {
    label: STATUS_LABELS[appt.status] ?? appt.status,
    color: STATUS_COLORS[appt.status] ?? 'bg-muted text-muted-foreground',
  };
}

export const AppointmentsPage = () => {
  const { user, isAuthenticated, tokens, setTokens, logout } = useAuth();
  const navigate = useNavigate();
  const isDoctor = user?.role === 'doctor';
  const localTz = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [filter, setFilter] = useState<'upcoming' | 'all'>('upcoming');

  // Patient-only: registered doctor + unregister
  const [registeredDoctor, setRegisteredDoctor] = useState<{ id: number; full_name: string } | null | undefined>(undefined);
  const [showUnregisterConfirm, setShowUnregisterConfirm] = useState(false);
  const [unregistering, setUnregistering] = useState(false);

  // Cancel flow
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null);

  // Reschedule flow
  const [rescheduleFor, setRescheduleFor] = useState<Appointment | null>(null);
  const [rescheduleDate, setRescheduleDate] = useState('');
  const [rescheduleSlots, setRescheduleSlots] = useState<TimeSlot[]>([]);
  const [rescheduleSelectedSlot, setRescheduleSelectedSlot] = useState<TimeSlot | null>(null);
  const [rescheduleLoading, setRescheduleLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate(isDoctor ? '/doctor/login' : '/patient/login');
      return;
    }
    fetchAppointments();
    if (!isDoctor) loadRegisteredDoctor();
  }, [isAuthenticated, filter]);

  const loadRegisteredDoctor = async () => {
    try {
      const res = await apiFetch(`/appointments/my-doctor`, { method: 'GET' }, tokens, setTokens, logout);
      if (res.ok) setRegisteredDoctor(await res.json());
      else setRegisteredDoctor(null);
    } catch { setRegisteredDoctor(null); }
  };

  const handleUnregister = async () => {
    setUnregistering(true);
    try {
      const res = await apiFetch(`/appointments/unregister`, { method: 'DELETE' }, tokens, setTokens, logout);
      if (res.ok) { setRegisteredDoctor(null); setShowUnregisterConfirm(false); }
    } catch { } finally { setUnregistering(false); }
  };

  const fetchAppointments = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const endpoint = filter === 'upcoming' ? '/appointments/upcoming' : '/appointments/my';
      const res = await apiFetch(endpoint, { method: 'GET' }, tokens, setTokens, logout);
      if (res.ok) setAppointments(await res.json());
    } catch {
      setMessage({ type: 'error', text: 'Failed to load appointments.' });
    } finally {
      setLoading(false);
    }
  };

  const confirmCancel = async () => {
    if (!cancelTarget) return;
    const id = cancelTarget.id;
    setActionLoading(id);
    setMessage(null);
    try {
      const res = await apiFetch(`/appointments/${id}/cancel`, { method: 'PUT' }, tokens, setTokens, logout);
      if (res.ok) {
        setMessage({ type: 'success', text: 'Appointment cancelled.' });
        setCancelTarget(null);
        fetchAppointments();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Could not cancel appointment.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error.' });
    } finally { setActionLoading(null); }
  };

  const openReschedule = (appt: Appointment) => {
    setRescheduleFor(appt);
    setRescheduleDate('');
    setRescheduleSlots([]);
    setRescheduleSelectedSlot(null);
  };

  const fetchRescheduleSlots = async (dateStr: string, doctorId: number) => {
    setRescheduleSelectedSlot(null);
    setRescheduleLoading(true);
    try {
      const res = await apiFetch(
        `/appointments/doctors/${doctorId}/slots?date=${dateStr}`,
        { method: 'GET' },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) setRescheduleSlots(await res.json());
      else setRescheduleSlots([]);
    } catch { setRescheduleSlots([]); } finally { setRescheduleLoading(false); }
  };

  const handleRescheduleDateChange = (dateStr: string) => {
    setRescheduleDate(dateStr);
    if (dateStr && rescheduleFor) fetchRescheduleSlots(dateStr, rescheduleFor.doctor_id);
  };

  const submitReschedule = async () => {
    if (!rescheduleFor || !rescheduleSelectedSlot || !rescheduleDate) return;
    setActionLoading(rescheduleFor.id);
    setMessage(null);
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const res = await apiFetch(
        `/appointments/${rescheduleFor.id}/reschedule`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            appointment_date: rescheduleDate,
            start_time: rescheduleSelectedSlot.start_time,
            end_time: rescheduleSelectedSlot.end_time,
            timezone: tz,
          }),
        },
        tokens,
        setTokens,
        logout,
      );
      if (res.ok) {
        setMessage({ type: 'success', text: 'Appointment rescheduled successfully.' });
        setRescheduleFor(null);
        fetchAppointments();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Could not reschedule appointment.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error.' });
    } finally { setActionLoading(null); }
  };

  // Split appointments into future / past for the "All" view
  const futureAppts = appointments.filter(isFuture);
  const pastAppts = appointments.filter(a => !isFuture(a));

  const NavbarComponent = isDoctor ? Navbar : PatientNavbar;

  const AppointmentCard = ({ appt }: { appt: Appointment }) => (
    <div className="bg-card/60 backdrop-blur-sm rounded-2xl border border-border/50 shadow-sm overflow-hidden">
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-medical-pink/20 to-medical-blue/20 flex items-center justify-center flex-shrink-0">
              <User className="h-5 w-5 text-medical-blue" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-foreground truncate">
                {isDoctor ? appt.patient_name : `Dr. ${appt.doctor_name}`}
              </p>
              {isDoctor && !appt.is_registered && appt.status !== 'pending_approval' && (
                <span className="inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-muted text-muted-foreground border border-border">
                  Unregistered
                </span>
              )}
              <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1">
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3 flex-shrink-0" />
                  {formatDate(appt.appointment_date)}
                </span>
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3 flex-shrink-0" />
                  {appt.start_time} – {appt.end_time}
                </span>
              </div>
              {appt.notes && (
                <p className="text-xs text-muted-foreground mt-1.5 italic">"{appt.notes}"</p>
              )}
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex-shrink-0 ${getStatusDisplay(appt).color}`}>
            {getStatusDisplay(appt).label}
          </span>
        </div>
      </div>

      {(appt.status === 'booked' || appt.status === 'pending_approval') && isFuture(appt) && (
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 px-5 pb-4">
          <Button
            size="sm"
            variant="outline"
            disabled={actionLoading === appt.id}
            onClick={() => openReschedule(appt)}
            className="w-full sm:w-auto text-xs h-8 gap-1 border-border/60 hover:bg-muted/50"
          >
            <RefreshCw className="h-3 w-3" /> Reschedule
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={actionLoading === appt.id}
            onClick={() => setCancelTarget(appt)}
            className="w-full sm:w-auto text-xs h-8 gap-1 text-red-600 border-red-200 hover:bg-red-50"
          >
            {actionLoading === appt.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <XCircle className="h-3 w-3" />}
            Cancel
          </Button>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <NavbarComponent />
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-3xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-1">
              Appointments
            </h1>
            <p className="text-muted-foreground text-sm">
              {isDoctor ? 'Manage your patient appointments.' : 'View and manage your scheduled appointments.'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Times shown in <strong>{localTz}</strong>
            </p>
          </div>
          {!isDoctor && (
            <Button
              onClick={() => navigate('/patient/book-appointment')}
              className="w-full sm:w-auto bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white"
            >
              + Book New
            </Button>
          )}
        </div>

        {/* Patient: Registered Doctor Banner */}
        {!isDoctor && registeredDoctor !== undefined && (
          <div className={`flex items-start sm:items-center gap-3 p-4 rounded-xl mb-6 border ${
            registeredDoctor
              ? 'bg-blue-500/10 border-medical-blue/30 text-blue-800 dark:text-blue-300'
              : 'bg-muted/40 border-border text-muted-foreground'
          }`}>
            <UserX className="h-5 w-5 flex-shrink-0 opacity-70" />
            <p className="text-sm font-medium flex-1">
              {registeredDoctor
                ? <>Registered with <strong>Dr. {registeredDoctor.full_name}</strong></>
                : 'You are not currently registered with a doctor.'}
            </p>
            {registeredDoctor && (
              <button
                onClick={() => setShowUnregisterConfirm(true)}
                className="ml-2 text-xs font-medium text-destructive hover:text-destructive/80 border border-destructive/30 hover:border-destructive/60 rounded-lg px-2 py-1 bg-background hover:bg-destructive/10 transition-colors flex-shrink-0"
              >
                Unregister
              </button>
            )}
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {(['upcoming', 'all'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                filter === f
                  ? 'bg-gradient-to-r from-medical-pink to-medical-blue text-white shadow'
                  : 'bg-muted/60 text-muted-foreground hover:bg-muted'
              }`}
            >
              {f === 'upcoming' ? 'Upcoming' : 'All'}
            </button>
          ))}
          <button onClick={fetchAppointments} className="sm:ml-auto p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground transition-colors">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {message && (
          <div className={`flex items-start gap-2 p-4 rounded-lg mb-4 border ${
            message.type === 'success'
              ? 'bg-green-500/10 border-green-500/30 text-green-800 dark:text-green-300'
              : 'bg-destructive/10 border-destructive/30 text-destructive'
          }`}>
            {message.type === 'success'
              ? <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
              : <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />}
            <p className="text-sm font-medium">{message.text}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
          </div>
        ) : appointments.length === 0 ? (
          <div className="bg-card/60 rounded-2xl border border-border/50 shadow-sm p-12 text-center">
            <Calendar className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
            <p className="font-semibold text-foreground mb-1">No appointments found</p>
            <p className="text-sm text-muted-foreground">
              {filter === 'upcoming' ? 'You have no upcoming appointments.' : 'No appointment history yet.'}
            </p>
            {!isDoctor && (
              <Button
                className="mt-4 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white"
                onClick={() => navigate('/patient/book-appointment')}
              >
                Book an Appointment
              </Button>
            )}
          </div>
        ) : filter === 'upcoming' ? (
          <div className="space-y-4">
            {appointments.map(appt => <AppointmentCard key={appt.id} appt={appt} />)}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Future appointments */}
            {futureAppts.length > 0 && (
              <>
                {futureAppts.map(appt => <AppointmentCard key={appt.id} appt={appt} />)}
              </>
            )}

            {/* Divider between past and future */}
            {futureAppts.length > 0 && pastAppts.length > 0 && (
              <div className="flex items-center gap-3 py-2">
                <div className="flex-1 h-px bg-border/60" />
                <span className="text-xs font-medium text-muted-foreground px-2">Past</span>
                <div className="flex-1 h-px bg-border/60" />
              </div>
            )}

            {/* Past appointments */}
            {pastAppts.length > 0 && (
              <div className="space-y-4 opacity-70">
                {pastAppts.map(appt => <AppointmentCard key={appt.id} appt={appt} />)}
              </div>
            )}
          </div>
        )}

        {/* Unregister Confirmation Modal */}
        {showUnregisterConfirm && registeredDoctor && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-2xl shadow-xl border border-border/50 max-w-md w-full p-6">
              <h3 className="text-lg font-bold text-foreground mb-2">Unregister from Dr. {registeredDoctor.full_name}?</h3>
              <p className="text-sm text-muted-foreground mb-6">
                Dr. {registeredDoctor.full_name} will no longer have access to your shared medical records.
              </p>
              <div className="flex flex-col gap-3">
                <Button onClick={handleUnregister} disabled={unregistering} className="w-full bg-destructive hover:bg-destructive/90 text-destructive-foreground">
                  {unregistering ? 'Unregistering...' : 'Yes, Unregister'}
                </Button>
                <Button variant="ghost" onClick={() => setShowUnregisterConfirm(false)} disabled={unregistering} className="w-full">
                  Keep Registration
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Cancel Confirmation Modal */}
        {cancelTarget && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-2xl shadow-xl border border-border/50 max-w-md w-full p-6">
              <h3 className="text-lg font-bold text-foreground mb-2">Cancel Appointment?</h3>
              <p className="text-sm text-muted-foreground mb-1">
                {isDoctor
                  ? <>Cancel the appointment with <strong>{cancelTarget.patient_name}</strong>?</>
                  : <>Cancel your appointment with <strong>Dr. {cancelTarget.doctor_name}</strong>?</>}
              </p>
              <p className="text-xs text-muted-foreground mb-6">
                {formatDate(cancelTarget.appointment_date)} at {cancelTarget.start_time}
              </p>
              <div className="flex flex-col gap-3">
                <Button
                  onClick={confirmCancel}
                  disabled={actionLoading === cancelTarget.id}
                  className="w-full bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                >
                  {actionLoading === cancelTarget.id ? 'Cancelling...' : 'Yes, Cancel Appointment'}
                </Button>
                <Button variant="ghost" onClick={() => setCancelTarget(null)} disabled={actionLoading === cancelTarget.id} className="w-full">
                  Keep Appointment
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Reschedule Modal — slot picker */}
        {rescheduleFor && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-2xl shadow-2xl border border-border/50 w-full max-w-md max-h-[90vh] flex flex-col">
              <div className="p-6 border-b border-border/50">
                <h3 className="text-lg font-bold text-foreground">Reschedule Appointment</h3>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Current: <strong>{formatDate(rescheduleFor.appointment_date)}</strong> at <strong>{rescheduleFor.start_time}</strong>
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                {/* Date picker */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1.5">New Date</label>
                  <input
                    type="date"
                    value={rescheduleDate}
                    min={tomorrowISO()}
                    onChange={e => handleRescheduleDateChange(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-medical-blue/50"
                  />
                </div>

                {/* Slot picker */}
                {rescheduleDate && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Available Slots
                      <span className="ml-1.5 text-xs font-normal text-muted-foreground">— {localTz}</span>
                    </label>

                    {rescheduleLoading ? (
                      <div className="flex items-center justify-center py-6">
                        <Loader2 className="h-5 w-5 animate-spin text-medical-blue" />
                      </div>
                    ) : rescheduleSlots.filter(s => s.available).length === 0 ? (
                      <div className="text-center py-6 rounded-xl border border-border/50 bg-muted/30">
                        <Clock className="h-8 w-8 mx-auto text-muted-foreground/40 mb-2" />
                        <p className="text-sm text-muted-foreground">No available slots on this date.</p>
                        <button
                          onClick={() => { setRescheduleDate(''); setRescheduleSlots([]); }}
                          className="inline-flex items-center gap-1 text-xs text-medical-blue hover:underline mt-2"
                        >
                          <ArrowLeft className="h-3 w-3" /> Pick another date
                        </button>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-2">
                        {rescheduleSlots.filter(s => s.available).map((slot, i) => (
                          <button
                            key={i}
                            onClick={() => setRescheduleSelectedSlot(slot)}
                            className={`p-2.5 rounded-xl border text-center text-sm font-medium transition-all ${
                              rescheduleSelectedSlot?.start_time === slot.start_time
                                ? 'bg-gradient-to-br from-medical-pink to-medical-blue text-white border-transparent shadow'
                                : 'border-border/60 hover:border-medical-blue/50 hover:bg-blue-500/5 text-foreground'
                            }`}
                          >
                            <span className="block">{slot.start_time}</span>
                            <span className="block text-[10px] opacity-70 mt-0.5">
                              {(() => {
                                const [sh, sm] = slot.start_time.split(':').map(Number);
                                const [eh, em] = slot.end_time.split(':').map(Number);
                                return `${(eh * 60 + em) - (sh * 60 + sm)} min`;
                              })()}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                    {rescheduleSelectedSlot && (
                      <div className="mt-3 p-3 bg-blue-500/10 border border-medical-blue/20 rounded-xl">
                        <p className="text-xs font-semibold text-foreground">Selected slot</p>
                        <p className="text-sm font-bold text-medical-blue mt-0.5">
                          {rescheduleSelectedSlot.start_time} – {rescheduleSelectedSlot.end_time}
                        </p>
                        <p className="text-xs text-muted-foreground">{formatDate(rescheduleDate)}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="p-6 border-t border-border/50 flex gap-3">
                <Button
                  onClick={submitReschedule}
                  disabled={!rescheduleSelectedSlot || !rescheduleDate || actionLoading === rescheduleFor.id}
                  className="flex-1 bg-gradient-to-r from-medical-pink to-medical-blue text-white hover:opacity-90"
                >
                  {actionLoading === rescheduleFor.id ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Confirm Reschedule'}
                </Button>
                <Button variant="outline" className="flex-1 border-border/60" onClick={() => setRescheduleFor(null)}>
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
