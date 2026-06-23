import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Calendar, Clock, ChevronRight, AlertCircle, CheckCircle, ArrowLeft, UserSearch } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PatientNavbar } from '@/components/PatientNavbar';
import { useAuth } from '@/context/AuthContext';
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery';
import { queryKeys } from '@/lib/queryKeys';

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

interface Doctor {
  id: number;
  full_name: string;
  email: string;
  specialty?: string | null;
  clinic_name?: string | null;
  bio?: string | null;
}

interface AvailabilitySlot {
  day_of_week: number;
  start_time: string;
  end_time: string;
  timezone: string;
  slot_duration_minutes: number;
}

interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
  schedule_timezone: string;
  start_at_utc: string;
  end_at_utc: string;
}

interface ScheduleException {
  id: number;
  doctor_id: number;
  exception_date: string;
  kind: string;
  start_time: string | null;
  end_time: string | null;
  slot_duration_minutes: number | null;
  timezone: string;
  notes: string | null;
  created_at: string;
}

type Step = 'select-date' | 'select-time' | 'confirm';

export const BookAppointmentPage = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const localTz = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const [step, setStep] = useState<Step>('select-date');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [notes, setNotes] = useState('');
  const [booking, setBooking] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'patient') {
      navigate('/patient/login');
    }
  }, [isAuthenticated, navigate, user]);
  const enabled = isAuthenticated && user?.role === "patient";
  const doctorQuery = useApiQuery<Doctor | null>(
    queryKeys.appointments.myDoctor,
    "/appointments/my-doctor",
    { enabled, retry: false },
  );
  const configQuery = useApiQuery<{
    min_booking_lead_hours?: number;
    booking_horizon_days?: number;
  }>(
    queryKeys.appointments.bookingConfig,
    "/appointments/booking-config",
    { enabled, staleTime: 30 * 60_000 },
  );
  const registeredDoctor = doctorQuery.isPending ? undefined : doctorQuery.data ?? null;
  const doctorId = registeredDoctor?.id ?? "none";
  const from = new Date();
  from.setDate(from.getDate() + 1);
  const fromStr = from.toISOString().split("T")[0];
  const to = new Date();
  to.setDate(to.getDate() + 14);
  const toStr = to.toISOString().split("T")[0];
  const availabilityQuery = useApiQuery<AvailabilitySlot[]>(
    queryKeys.appointments.availability(doctorId),
    `/appointments/doctors/${doctorId}/availability`,
    { enabled: Boolean(registeredDoctor), staleTime: 5 * 60_000 },
  );
  const exceptionsQuery = useApiQuery<ScheduleException[]>(
    queryKeys.appointments.exceptions(doctorId),
    `/appointments/doctors/${doctorId}/exceptions?date_from=${encodeURIComponent(fromStr)}&date_to=${encodeURIComponent(toStr)}`,
    { enabled: Boolean(registeredDoctor), staleTime: 5 * 60_000 },
  );
  const slotsQuery = useApiQuery<TimeSlot[]>(
    queryKeys.appointments.slots(doctorId, selectedDate),
    `/appointments/doctors/${doctorId}/slots?date=${selectedDate}`,
    { enabled: Boolean(registeredDoctor && selectedDate), staleTime: 30_000 },
  );
  const availability = availabilityQuery.data ?? [];
  const scheduleExceptions = useMemo(
    () => exceptionsQuery.data ?? [],
    [exceptionsQuery.data],
  );
  const timeSlots = slotsQuery.data ?? [];
  const loading = doctorQuery.isPending;
  const slotsLoading = slotsQuery.isPending;
  const minLeadHours = configQuery.data?.min_booking_lead_hours ?? 2;
  const bookingHorizonDays = configQuery.data?.booking_horizon_days ?? 14;
  const bookAppointment = useApiMutation<void, {
    doctor_id: number;
    appointment_date: string;
    start_time: string;
    end_time: string;
    notes: string | null;
  }>({
    invalidate: [
      queryKeys.appointments.all,
      queryKeys.notifications.newBookings,
      queryKeys.dashboard.stats,
    ],
    mutationFn: (body, request) =>
      request<void>("/appointments/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
  });

  const availableDays = new Set(availability.map(s => s.day_of_week));

  const blockedDateSet = useMemo(
    () => new Set(scheduleExceptions.filter(e => e.kind === 'blocked').map(e => e.exception_date)),
    [scheduleExceptions],
  );
  const customDateSet = useMemo(
    () => new Set(scheduleExceptions.filter(e => e.kind === 'custom').map(e => e.exception_date)),
    [scheduleExceptions],
  );

  const isDateAvailable = (dateStr: string): boolean => {
    if (blockedDateSet.has(dateStr)) return false;
    if (customDateSet.has(dateStr)) return true;
    const dow = new Date(dateStr + 'T12:00:00').getDay();
    const mondayBased = (dow + 6) % 7;
    return availableDays.has(mondayBased);
  };

  const selectDate = (dateStr: string) => {
    if (!isDateAvailable(dateStr) || !registeredDoctor) return;
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setMessage(null);
    setStep('select-time');
  };

  const confirmBooking = async () => {
    if (booking || !registeredDoctor || !selectedDate || !selectedSlot) return;
    setBooking(true);
    setMessage(null);
    try {
      await bookAppointment.mutateAsync({
        doctor_id: registeredDoctor.id,
        appointment_date: selectedDate,
        start_time: selectedSlot.start_time,
        end_time: selectedSlot.end_time,
        notes: notes || null,
      });
      setMessage({ type: 'success', text: `Appointment booked for ${formatDate(selectedDate)} at ${selectedSlot.start_time}!` });
      setStep('confirm');
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Network error. Please try again.' });
    } finally { setBooking(false); }
  };

  const formatDate = (d: string) => new Date(d + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  const slotDurationMins = (slot: TimeSlot): number => {
    const [sh, sm] = slot.start_time.split(':').map(Number);
    const [eh, em] = slot.end_time.split(':').map(Number);
    return (eh * 60 + em) - (sh * 60 + sm);
  };

  const isSlotTooSoon = (slot: TimeSlot): boolean =>
    new Date(slot.start_at_utc).getTime() < Date.now() + minLeadHours * 60 * 60 * 1000;

  const localSlotTime = (slot: TimeSlot): string =>
    `${new Date(slot.start_at_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - ${new Date(slot.end_at_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

  const dateOptions: string[] = [];
  for (let i = 0; i <= bookingHorizonDays; i++) {
    const d = new Date();
    d.setDate(d.getDate() + i);
    dateOptions.push(d.toISOString().split('T')[0]);
  }

  return (
    <div className="min-h-screen bg-background">
      <PatientNavbar />
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-2xl">
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-2">
            {registeredDoctor ? `Book with Dr. ${registeredDoctor.full_name}` : 'Book Appointment'}
          </h1>
          <p className="text-muted-foreground">
            {registeredDoctor
              ? 'Schedule a consultation with your registered doctor.'
              : 'Register with a doctor before booking an appointment.'}
          </p>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-medical-blue" />
          </div>
        )}

        {/* No doctor registered */}
        {!loading && registeredDoctor === null && (
          <div className="bg-card/60 backdrop-blur-sm rounded-2xl border border-border/50 shadow-sm p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-4">
              <UserSearch className="h-8 w-8 text-muted-foreground" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2">No Doctor Registered</h2>
            <p className="text-sm text-muted-foreground mb-6 max-w-xs mx-auto">
              You need to register with a doctor before you can book appointments. Browse verified doctors and send a registration request.
            </p>
            <Button
              onClick={() => navigate('/patient/find-doctor')}
              className="bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white"
            >
              <UserSearch className="mr-2 h-4 w-4" />
              Find a Doctor
            </Button>
          </div>
        )}

        {/* Booking wizard — only when registered doctor is known */}
        {!loading && registeredDoctor && step !== 'confirm' && (
          <>
            {/* Progress Steps */}
            <div className="flex items-center gap-1.5 sm:gap-2 mb-8 overflow-x-auto pb-1">
              {(['select-date', 'select-time'] as const).map((s, i) => (
                <div key={s} className="flex items-center gap-2">
                  <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold flex-shrink-0 ${step === s ? 'bg-gradient-to-r from-medical-pink to-medical-blue text-white' : 'bg-muted text-muted-foreground'}`}>
                    {i + 1}
                  </div>
                  <span className={`text-xs sm:text-sm font-medium hidden sm:block ${step === s ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {['Date', 'Time'][i]}
                  </span>
                  {i < 1 && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                </div>
              ))}
            </div>

            {message && (
              <div className={`flex items-start gap-2 p-4 rounded-lg mb-6 border ${message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400' : 'bg-destructive/10 border-destructive/30 text-destructive'}`}>
                {message.type === 'success' ? <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" /> : <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />}
                <p className="text-sm font-medium">{message.text}</p>
              </div>
            )}
          </>
        )}

        {/* Step: Select Date */}
        {!loading && registeredDoctor && step === 'select-date' && (
          <div className="bg-card/60 backdrop-blur-sm rounded-2xl border border-border/50 shadow-sm p-6">
            <h2 className="font-semibold text-lg text-foreground mb-1 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-medical-blue" />
              Select a Date
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              Available days are highlighted. One-off replacement hours show a &quot;Custom&quot; tag.
            </p>
            {availability.length === 0 && scheduleExceptions.filter(e => e.kind === 'custom').length === 0 ? (
              <div className="text-center py-8">
                <Clock className="h-10 w-10 mx-auto text-muted-foreground/30 mb-3" />
                <p className="text-sm font-medium text-foreground">No slots available</p>
                <p className="text-xs text-muted-foreground mt-1">Dr. {registeredDoctor.full_name} has not set working hours yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {dateOptions.map(d => {
                  const avail = isDateAvailable(d);
                  const dow = (new Date(d + 'T12:00:00').getDay() + 6) % 7;
                  const dayLabel = DAY_NAMES[dow].substring(0, 3);
                  const dayNum = new Date(d + 'T12:00:00').getDate();
                  const mon = new Date(d + 'T12:00:00').toLocaleString('default', { month: 'short' });
                  const isCustomDay = customDateSet.has(d);
                  return (
                    <button
                      key={d}
                      disabled={!avail}
                      onClick={() => selectDate(d)}
                      className={`p-3 rounded-xl border text-center transition-all relative ${avail ? 'border-medical-blue/30 bg-blue-50/50 dark:bg-blue-900/10 hover:bg-blue-100 dark:hover:bg-blue-900/20 cursor-pointer' : 'border-border/50 bg-muted/30 opacity-40 cursor-not-allowed'} ${selectedDate === d ? 'bg-gradient-to-br from-medical-pink to-medical-blue text-white border-transparent' : ''}`}
                    >
                      {isCustomDay && avail && (
                        <span className="absolute top-1 right-1 text-[9px] font-bold uppercase bg-amber-400 text-amber-950 px-1 rounded">Custom</span>
                      )}
                      <p className="text-xs font-medium">{dayLabel}</p>
                      <p className="text-lg font-bold leading-none my-1">{dayNum}</p>
                      <p className="text-xs">{mon}</p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Step: Select Time */}
        {!loading && registeredDoctor && step === 'select-time' && selectedDate && (
          <div className="bg-card/60 backdrop-blur-sm rounded-2xl border border-border/50 shadow-sm p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
              <h2 className="font-semibold text-lg text-foreground flex items-center gap-2">
                <Clock className="h-5 w-5 text-medical-blue" />
                Select a Time
              </h2>
              <button onClick={() => { setStep('select-date'); setSelectedSlot(null); }} className="text-sm text-medical-blue hover:underline flex items-center gap-1">
                <ArrowLeft className="h-4 w-4" /> Change date
              </button>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              <strong>{formatDate(selectedDate)}</strong>
              <span className="text-xs text-muted-foreground"> · Times shown in {localTz}</span>
            </p>
            {slotsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-medical-blue" />
              </div>
            ) : timeSlots.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="h-10 w-10 mx-auto text-muted-foreground/30 mb-3" />
                <p className="text-sm font-medium text-foreground">No slots available on this date</p>
                <p className="text-xs text-muted-foreground mt-1 mb-4">All slots are fully booked or outside working hours. Pick another day.</p>
                <button
                  onClick={() => { setStep('select-date'); setSelectedSlot(null); }}
                  className="inline-flex items-center gap-1.5 text-sm text-medical-blue hover:underline"
                >
                  <ArrowLeft className="h-3.5 w-3.5" /> Choose a different date
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-6">
                  {timeSlots.map((slot, i) => {
                    const tooSoon = slot.available && isSlotTooSoon(slot);
                    const disabled = !slot.available || tooSoon;
                    return (
                      <button
                        key={i}
                        disabled={disabled}
                        onClick={() => !disabled && setSelectedSlot(slot)}
                        className={`p-3 rounded-xl border text-center transition-all text-sm font-medium ${
                          disabled
                            ? 'border-border/50 bg-muted/30 text-muted-foreground cursor-not-allowed line-through'
                            : selectedSlot?.start_time === slot.start_time
                            ? 'bg-gradient-to-br from-medical-pink to-medical-blue text-white border-transparent shadow-md'
                            : 'border-border/60 hover:border-medical-blue hover:bg-blue-50/50 dark:hover:bg-blue-900/10 cursor-pointer'
                        }`}
                      >
                        <span className="block">
                          {new Date(slot.start_at_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        <span className="block text-[10px] font-normal mt-0.5 opacity-70">{slotDurationMins(slot)} min</span>
                        {!slot.available && <span className="block text-[10px] font-normal text-destructive">Booked</span>}
                        {slot.available && tooSoon && <span className="block text-[10px] font-normal text-amber-500">Too soon</span>}
                      </button>
                    );
                  })}
                </div>

                {selectedSlot && (
                  <div className="border-t border-border/50 pt-4">
                    <div className="p-4 bg-blue-500/10 border border-medical-blue/20 rounded-xl mb-4">
                      <p className="text-sm font-semibold text-foreground mb-1">Selected slot</p>
                      <p className="text-medical-blue font-bold">{localSlotTime(selectedSlot)}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Your timezone: {localTz}. Doctor schedule: {selectedSlot.start_time} - {selectedSlot.end_time} ({selectedSlot.schedule_timezone})
                      </p>
                    </div>
                    <label className="block text-sm font-medium text-foreground mb-1">Notes (optional)</label>
                    <textarea
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                      placeholder="Any notes for the doctor..."
                      rows={2}
                      className="w-full px-3 py-2 rounded-lg border border-border/60 bg-background/50 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 resize-none mb-4"
                    />
                    <Button
                      onClick={confirmBooking}
                      disabled={booking}
                      className="w-full h-11 bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white font-semibold"
                    >
                      {booking ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Booking...</> : 'Confirm Appointment'}
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Step: Confirmation */}
        {step === 'confirm' && (
          <div className="bg-card/60 backdrop-blur-sm rounded-2xl border border-border/50 shadow-sm p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-9 w-9 text-emerald-600" />
            </div>
            <h2 className="text-xl font-bold text-foreground mb-2">Appointment Confirmed!</h2>
            <p className="text-muted-foreground text-sm mb-6">{message?.text}</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={() => navigate('/patient/appointments')} className="bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white">
                View My Appointments
              </Button>
              <Button variant="outline" onClick={() => {
                setStep('select-date');
                setSelectedDate('');
                setSelectedSlot(null);
                setNotes('');
                setMessage(null);
              }}>
                Book Another
              </Button>
              <Button variant="outline" onClick={() => navigate('/patient/dashboard')}>
                Back to Dashboard
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
