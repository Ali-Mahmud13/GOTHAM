import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Calendar, Clock, User, ChevronRight, AlertCircle, CheckCircle, ArrowLeft, UserCheck, UserX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PatientNavbar } from '@/components/PatientNavbar';
import { useAuth } from '@/context/AuthContext';

const API_URL = 'http://localhost:8000';
const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

interface Doctor {
  id: number;
  full_name: string;
  email: string;
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
}

type Step = 'select-doctor' | 'select-date' | 'select-time' | 'confirm';

export const BookAppointmentPage = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState<Step>('select-doctor');
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [availability, setAvailability] = useState<AvailabilitySlot[]>([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [notes, setNotes] = useState('');
  const [registeredDoctor, setRegisteredDoctor] = useState<Doctor | null | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [booking, setBooking] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showRegModal, setShowRegModal] = useState(false);
  const [isPendingApproval, setIsPendingApproval] = useState(false);
  const [showUnregisterConfirm, setShowUnregisterConfirm] = useState(false);
  const [unregistering, setUnregistering] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'patient') {
      navigate('/patient/login');
      return;
    }
    loadDoctors();
    loadRegisteredDoctor();
  }, [isAuthenticated, user]);

  const handleUnregister = async () => {
    setUnregistering(true);
    try {
      const res = await fetch(`${API_URL}/appointments/unregister`, {
        method: 'DELETE',
        headers: { 'X-User-Email': user!.email },
      });
      if (res.ok) {
        setRegisteredDoctor(null);
        setShowUnregisterConfirm(false);
      }
    } catch { } finally { setUnregistering(false); }
  };

  const loadRegisteredDoctor = async () => {
    try {
      const res = await fetch(`${API_URL}/appointments/my-doctor`, {
        headers: { 'X-User-Email': user!.email },
      });
      if (res.ok) {
        const data = await res.json();
        setRegisteredDoctor(data); // null if no registered doctor
      } else {
        setRegisteredDoctor(null);
      }
    } catch {
      setRegisteredDoctor(null);
    }
  };

  const loadDoctors = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/appointments/doctors`);
      const data: Doctor[] = await res.json();
      setDoctors(data);
    } catch {
      setMessage({ type: 'error', text: 'Could not load doctors. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const selectDoctor = async (doctor: Doctor) => {
    setSelectedDoctor(doctor);
    setSelectedDate('');
    setTimeSlots([]);
    setSelectedSlot(null);
    setMessage(null);

    // Load availability to know which days to enable
    try {
      const res = await fetch(`${API_URL}/appointments/doctors/${doctor.id}/availability`);
      const data: AvailabilitySlot[] = await res.json();
      setAvailability(data);
    } catch {
      setAvailability([]);
    }
    setStep('select-date');
  };

  const availableDays = new Set(availability.map(s => s.day_of_week));

  // Get the minimum bookable date (tomorrow)
  const minDate = (() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  })();

  const isDateAvailable = (dateStr: string): boolean => {
    const dow = new Date(dateStr + 'T12:00:00').getDay(); // 0=Sun, shift to Mon=0
    const mondayBased = (dow + 6) % 7;
    return availableDays.has(mondayBased);
  };

  const selectDate = async (dateStr: string) => {
    if (!isDateAvailable(dateStr)) return;
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setMessage(null);
    setSlotsLoading(true);
    try {
      const res = await fetch(`${API_URL}/appointments/doctors/${selectedDoctor!.id}/slots?date=${dateStr}`);
      const data: TimeSlot[] = await res.json();
      setTimeSlots(data);
    } catch {
      setTimeSlots([]);
    } finally {
      setSlotsLoading(false);
    }
    setStep('select-time');
  };

  const handleConfirmClick = () => {
    if (!selectedDoctor || !selectedDate || !selectedSlot) return;
    // If booking with a different doctor, show registration modal
    if (registeredDoctor !== undefined && selectedDoctor.id !== registeredDoctor?.id) {
      setShowRegModal(true);
    } else {
      confirmBooking(false);
    }
  };

  const confirmBooking = async (requestRegistration: boolean) => {
    if (!selectedDoctor || !selectedDate || !selectedSlot) return;
    setShowRegModal(false);
    setBooking(true);
    setMessage(null);
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const res = await fetch(`${API_URL}/appointments/book`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': user!.email },
        body: JSON.stringify({
          doctor_id: selectedDoctor.id,
          appointment_date: selectedDate,
          start_time: selectedSlot.start_time,
          end_time: selectedSlot.end_time,
          timezone: tz,
          notes: notes || null,
          request_registration: requestRegistration,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        const pending = data.status === 'pending_approval';
        setIsPendingApproval(pending);
        if (pending) {
          setMessage({ type: 'success', text: `Registration request sent to ${selectedDoctor.full_name}. Your appointment on ${formatDate(selectedDate)} at ${selectedSlot.start_time} is pending their approval.` });
        } else {
          setMessage({ type: 'success', text: `Appointment booked for ${formatDate(selectedDate)} at ${selectedSlot.start_time}!` });
        }
        setStep('confirm');
      } else {
        setMessage({ type: 'error', text: data.detail || 'Booking failed. Please try again.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setBooking(false);
    }
  };

  const formatDate = (d: string) => new Date(d + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  // Generate a 2-week date picker
  const dateOptions: string[] = [];
  for (let i = 1; i <= 14; i++) {
    const d = new Date();
    d.setDate(d.getDate() + i);
    dateOptions.push(d.toISOString().split('T')[0]);
  }

  return (
    <div className="min-h-screen bg-background">
      <PatientNavbar />
      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-2">
            Book Appointment
          </h1>
          <p className="text-muted-foreground">Schedule a consultation with your doctor.</p>
        </div>

        {/* Registered Doctor Banner */}
        {registeredDoctor !== undefined && (
          <div className={`flex items-center gap-3 p-4 rounded-xl mb-6 border ${
            registeredDoctor
              ? 'bg-blue-50 border-blue-200 text-blue-800'
              : 'bg-gray-50 border-gray-200 text-gray-600'
          }`}>
            {registeredDoctor ? (
              <UserCheck className="h-5 w-5 flex-shrink-0 text-medical-blue" />
            ) : (
              <UserX className="h-5 w-5 flex-shrink-0 text-gray-400" />
            )}
            <p className="text-sm font-medium flex-1">
              {registeredDoctor
                ? <>Your registered doctor: <strong>{registeredDoctor.full_name}</strong></>
                : 'You are not currently registered with a doctor.'}
            </p>
            {registeredDoctor && (
              <button
                onClick={() => setShowUnregisterConfirm(true)}
                className="ml-2 text-xs font-medium text-red-600 hover:text-red-800 border border-red-300 hover:border-red-500 rounded-lg px-2 py-1 bg-white hover:bg-red-50 transition-colors flex-shrink-0"
              >
                Unregister
              </button>
            )}
          </div>
        )}

        {/* Progress Steps */}
        <div className="flex items-center gap-2 mb-8">
          {(['select-doctor', 'select-date', 'select-time'] as const).map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step === s || (step === 'confirm' && i < 3) ? 'bg-gradient-to-r from-medical-pink to-medical-blue text-white' : 'bg-gray-100 text-gray-400'}`}>
                {i + 1}
              </div>
              <span className={`text-sm font-medium hidden sm:block ${step === s ? 'text-gray-900' : 'text-gray-400'}`}>
                {['Doctor', 'Date', 'Time'][i]}
              </span>
              {i < 2 && <ChevronRight className="h-4 w-4 text-gray-300" />}
            </div>
          ))}
        </div>

        {message && (
          <div className={`flex items-start gap-2 p-4 rounded-lg mb-6 ${message.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'}`}>
            {message.type === 'success' ? <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" /> : <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />}
            <p className="text-sm font-medium">{message.text}</p>
          </div>
        )}

        {/* Step: Select Doctor */}
        {step === 'select-doctor' && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="font-semibold text-lg text-gray-900 mb-4 flex items-center gap-2">
              <User className="h-5 w-5 text-medical-blue" /> Select a Doctor
            </h2>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-medical-blue" />
              </div>
            ) : doctors.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">No doctors available at this time.</p>
            ) : (
              <div className="space-y-3">
                {doctors.map(doctor => {
                  const isRegistered = registeredDoctor?.id === doctor.id;
                  return (
                    <button
                      key={doctor.id}
                      onClick={() => selectDoctor(doctor)}
                      className={`w-full flex items-center justify-between p-4 rounded-xl border transition-all text-left ${
                        isRegistered
                          ? 'border-medical-blue bg-blue-50/60 hover:bg-blue-100'
                          : 'border-gray-200 hover:border-medical-blue hover:bg-blue-50/50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-medical-pink to-medical-blue flex items-center justify-center text-white font-bold text-sm">
                          {(doctor.full_name || doctor.email)[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-gray-900">{doctor.full_name}</p>
                            {isRegistered && (
                              <span className="text-xs bg-medical-blue text-white px-2 py-0.5 rounded-full font-medium">Your Doctor</span>
                            )}
                          </div>
                          <p className="text-xs text-gray-500">{doctor.email}</p>
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-400" />
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Step: Select Date */}
        {step === 'select-date' && selectedDoctor && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-lg text-gray-900 flex items-center gap-2">
                <Calendar className="h-5 w-5 text-medical-blue" />
                Select a Date
              </h2>
              <button onClick={() => { setStep('select-doctor'); setSelectedDoctor(null); }} className="text-sm text-medical-blue hover:underline flex items-center gap-1">
                <ArrowLeft className="h-4 w-4" /> Change doctor
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Booking with <strong>{selectedDoctor.full_name}</strong>. Available days are highlighted.
            </p>
            {availability.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="h-10 w-10 mx-auto text-gray-300 mb-3" />
                <p className="text-sm font-medium text-gray-600">No slots available</p>
                <p className="text-xs text-gray-400 mt-1">This doctor has not set working hours yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                {dateOptions.map(d => {
                  const avail = isDateAvailable(d);
                  const dow = (new Date(d + 'T12:00:00').getDay() + 6) % 7;
                  const dayLabel = DAY_NAMES[dow].substring(0, 3);
                  const dayNum = new Date(d + 'T12:00:00').getDate();
                  const mon = new Date(d + 'T12:00:00').toLocaleString('default', { month: 'short' });
                  return (
                    <button
                      key={d}
                      disabled={!avail}
                      onClick={() => selectDate(d)}
                      className={`p-3 rounded-xl border text-center transition-all ${avail ? 'border-medical-blue/30 bg-blue-50/50 hover:bg-blue-100 cursor-pointer' : 'border-gray-200 bg-gray-50 opacity-40 cursor-not-allowed'} ${selectedDate === d ? 'bg-gradient-to-br from-medical-pink to-medical-blue text-white border-transparent' : ''}`}
                    >
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
        {step === 'select-time' && selectedDoctor && selectedDate && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-lg text-gray-900 flex items-center gap-2">
                <Clock className="h-5 w-5 text-medical-blue" />
                Select a Time
              </h2>
              <button onClick={() => { setStep('select-date'); setSelectedSlot(null); }} className="text-sm text-medical-blue hover:underline flex items-center gap-1">
                <ArrowLeft className="h-4 w-4" /> Change date
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              <strong>{formatDate(selectedDate)}</strong> — {selectedDoctor.full_name}
            </p>
            {slotsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-medical-blue" />
              </div>
            ) : timeSlots.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="h-10 w-10 mx-auto text-gray-300 mb-3" />
                <p className="text-sm font-medium text-gray-600">No slots available</p>
                <p className="text-xs text-gray-400 mt-1">All slots on this day are fully booked. Please choose another date.</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 mb-6">
                  {timeSlots.map((slot, i) => (
                    <button
                      key={i}
                      disabled={!slot.available}
                      onClick={() => setSelectedSlot(slot)}
                      className={`p-3 rounded-xl border text-center transition-all text-sm font-medium ${
                        !slot.available
                          ? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed line-through'
                          : selectedSlot?.start_time === slot.start_time
                          ? 'bg-gradient-to-br from-medical-pink to-medical-blue text-white border-transparent shadow-md'
                          : 'border-gray-200 hover:border-medical-blue hover:bg-blue-50/50 cursor-pointer'
                      }`}
                    >
                      {slot.start_time}
                      {!slot.available && <span className="block text-xs font-normal">Booked</span>}
                    </button>
                  ))}
                </div>

                {selectedSlot && (
                  <div className="border-t border-gray-100 pt-4">
                    <div className="p-4 bg-blue-50 rounded-xl mb-4">
                      <p className="text-sm font-semibold text-gray-800 mb-1">Selected slot</p>
                      <p className="text-medical-blue font-bold">{selectedSlot.start_time} – {selectedSlot.end_time}</p>
                      <p className="text-xs text-gray-600 mt-1">{formatDate(selectedDate)} · {selectedDoctor.full_name}</p>
                    </div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
                    <textarea
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                      placeholder="Any notes for the doctor..."
                      rows={2}
                      className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-medical-blue/50 resize-none mb-4"
                    />
                    <Button
                      onClick={handleConfirmClick}
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

        {/* Unregister Confirmation Modal */}
        {showUnregisterConfirm && registeredDoctor && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Unregister from Dr. {registeredDoctor.full_name}?</h3>
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to unregister? Dr. {registeredDoctor.full_name} will no longer have access to your shared medical records, and any pending registration requests will be cancelled.
              </p>
              <div className="flex flex-col gap-3">
                <Button
                  onClick={handleUnregister}
                  disabled={unregistering}
                  className="w-full bg-red-600 hover:bg-red-700 text-white"
                >
                  {unregistering ? 'Unregistering...' : 'Yes, Unregister'}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setShowUnregisterConfirm(false)}
                  className="w-full text-gray-500"
                  disabled={unregistering}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Registration Modal */}
        {showRegModal && selectedDoctor && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Book with {selectedDoctor.full_name}</h3>
              {registeredDoctor ? (
                <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3 mb-6">
                  You are already registered with <strong>Dr. {registeredDoctor.full_name}</strong>. You must unregister from your current doctor before registering with a new one.
                </div>
              ) : (
                <p className="text-sm text-gray-600 mb-6">
                  This doctor is not your registered doctor. Would you like to request to register under {selectedDoctor.full_name} and grant them access to your medical records?
                  Your appointment will be pending their approval.
                </p>
              )}
              <div className="flex flex-col gap-3">
                {!registeredDoctor && (
                  <Button
                    onClick={() => confirmBooking(true)}
                    className="w-full bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white"
                  >
                    <UserCheck className="mr-2 h-4 w-4" />
                    Request Registration &amp; Share Data
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={() => confirmBooking(false)}
                  className="w-full"
                >
                  Just Book Appointment
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setShowRegModal(false)}
                  className="w-full text-gray-500"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Confirmation */}
        {step === 'confirm' && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${
              isPendingApproval ? 'bg-yellow-100' : 'bg-green-100'
            }`}>
              {isPendingApproval
                ? <Clock className="h-9 w-9 text-yellow-600" />
                : <CheckCircle className="h-9 w-9 text-green-600" />}
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              {isPendingApproval ? 'Registration Request Sent!' : 'Appointment Confirmed!'}
            </h2>
            <p className="text-gray-600 text-sm mb-6">{message?.text}</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={() => navigate('/patient/appointments')} className="bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white">
                View My Appointments
              </Button>
              <Button variant="outline" onClick={() => { setStep('select-doctor'); setSelectedDoctor(null); setSelectedDate(''); setSelectedSlot(null); setNotes(''); setMessage(null); }}>
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
