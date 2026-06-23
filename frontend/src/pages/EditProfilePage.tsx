import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Loader2, AlertCircle, User, Heart, ArrowLeft, UserX } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { PatientNavbar } from '@/components/PatientNavbar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useApiMutation, useApiQuery } from '@/hooks/useApiQuery';
import { queryKeys } from '@/lib/queryKeys';

type HistoryAnswer = 'unknown' | 'yes' | 'no';

interface PatientProfile {
  id: number;
  patient_identifier: string;
  age: number;
  contact_number: string;
  number_of_pregnancies: number | null;
  bmi_category: number | null;
  family_history: boolean | null;
  pcos: boolean | null;
  unexplained_prenatal_loss: boolean | null;
  large_child_or_birth_default: boolean | null;
  prediabetes: boolean | null;
}

export const EditProfilePage = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [closeConfirmation, setCloseConfirmation] = useState('');
  const [closingAccount, setClosingAccount] = useState(false);
  
  const [age, setAge] = useState<string>('');
  const [contactNumber, setContactNumber] = useState('');
  const [numberOfPregnancies, setNumberOfPregnancies] = useState<string>('');
  const [bmiCategory, setBmiCategory] = useState<string>('');
  const [familyHistory, setFamilyHistory] = useState<HistoryAnswer>('unknown');
  const [pcos, setPcos] = useState<HistoryAnswer>('unknown');
  const [unexplainedPrenatalLoss, setUnexplainedPrenatalLoss] = useState<HistoryAnswer>('unknown');
  const [largeChildOrBirthDefault, setLargeChildOrBirthDefault] = useState<HistoryAnswer>('unknown');
  const [prediabetes, setPrediabetes] = useState<HistoryAnswer>('unknown');

  const patientIdentifier = user?.patient_info?.patient_identifier;

  useEffect(() => {
    if (!isAuthenticated || !user || user.role !== 'patient' || !patientIdentifier) {
      navigate('/patient/login');
      return;
    }
  }, [isAuthenticated, user, patientIdentifier, navigate]);
  const profileQuery = useApiQuery<PatientProfile>(
    queryKeys.patients.portalProfile,
    `/api/patient-portal/profile/${patientIdentifier ?? ""}`,
    { enabled: Boolean(isAuthenticated && patientIdentifier) },
  );
  const updateProfile = useApiMutation<void, Record<string, string | number | boolean | null>>({
    invalidate: [
      queryKeys.patients.portalProfile,
      queryKeys.patients.all,
      queryKeys.dashboard.stats,
    ],
    mutationFn: (body, request) =>
      request<void>(`/api/patient-portal/profile/${patientIdentifier}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
  });
  const closeAccountMutation = useApiMutation<void, string>({
    mutationFn: (confirmation, request) =>
      request<void>("/auth/me/close-account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmation }),
      }),
  });

  useEffect(() => {
    const data = profileQuery.data;
    if (!data) return;
      setAge(data.age > 0 ? String(data.age) : '');
      setContactNumber(data.contact_number || '');
      setNumberOfPregnancies(data.number_of_pregnancies !== null ? String(data.number_of_pregnancies) : '');
      setBmiCategory(data.bmi_category !== null ? String(data.bmi_category) : '');
      const answer = (value: boolean | null): HistoryAnswer => (
        value === true ? 'yes' : value === false ? 'no' : 'unknown'
      );
      setFamilyHistory(answer(data.family_history));
      setPcos(answer(data.pcos));
      setUnexplainedPrenatalLoss(answer(data.unexplained_prenatal_loss));
      setLargeChildOrBirthDefault(answer(data.large_child_or_birth_default));
      setPrediabetes(answer(data.prediabetes));
      setError('');
  }, [profileQuery.data]);

  useEffect(() => {
    if (profileQuery.isError) {
      setError('Failed to load profile. Please try again.');
    }
  }, [profileQuery.isError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!patientIdentifier) {
      setError('Patient identifier not found');
      return;
    }

    // Validate age
    if (age && (parseInt(age) < 10 || parseInt(age) > 100)) {
      setError('Please enter a valid age between 10 and 100');
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const updateData: Record<string, string | number | boolean | null> = {
        contact_number: contactNumber.trim()
      };

      // Only include fields that have values
      if (age) updateData.age = parseInt(age);
      if (numberOfPregnancies) updateData.number_of_pregnancies = parseInt(numberOfPregnancies);
      if (bmiCategory) updateData.bmi_category = parseInt(bmiCategory);
      
      const answerValue = (value: HistoryAnswer): boolean | null => (
        value === 'yes' ? true : value === 'no' ? false : null
      );
      updateData.family_history = answerValue(familyHistory);
      updateData.pcos = answerValue(pcos);
      updateData.unexplained_prenatal_loss = answerValue(unexplainedPrenatalLoss);
      updateData.large_child_or_birth_default = answerValue(largeChildOrBirthDefault);
      updateData.prediabetes = answerValue(prediabetes);

      await updateProfile.mutateAsync(updateData);
      setSuccess('Profile updated successfully!');
      setTimeout(() => {
        navigate('/patient/dashboard');
      }, 1500);
    } catch (err: unknown) {
      console.error('Update error:', err);
      setError(err instanceof Error ? err.message : 'Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const closeAccount = async () => {
    if (closeConfirmation.trim().toUpperCase() !== 'CLOSE') {
      setError('Type CLOSE to confirm account closure.');
      return;
    }
    setClosingAccount(true);
    setError('');
    try {
      await closeAccountMutation.mutateAsync(closeConfirmation);
      logout();
      navigate('/patient/login', { replace: true });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to close account.');
    } finally {
      setClosingAccount(false);
    }
  };

  if (profileQuery.isPending) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
        <PatientNavbar />
        <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10">
          <div className="text-center text-lg">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent rounded-full text-medical-blue mb-4" />
            <p>Loading profile...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
      <PatientNavbar />
      
      <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <div className="max-w-3xl mx-auto">
          {/* Back Button */}
          <Button
            variant="ghost"
            onClick={() => navigate('/patient/dashboard')}
            className="mb-6 text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-2">
              Edit Profile
            </h1>
            <p className="text-muted-foreground">
              Update your personal and medical information
            </p>
          </div>

          {/* Alert Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-800">{success}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Basic Information */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-medical-blue" />
                Basic Information
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="age" className="text-sm font-medium mb-2">
                    Age <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="age"
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="Enter your age"
                    min="10"
                    max="100"
                    required
                    className="w-full"
                  />
                </div>

                <div>
                  <Label htmlFor="contact" className="text-sm font-medium mb-2">
                    Contact Info <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="contact"
                    type="tel"
                    value={contactNumber}
                    onChange={(e) => setContactNumber(e.target.value)}
                    placeholder="Enter your contact info"
                    required
                    className="w-full"
                  />
                </div>
              </div>
            </div>

            {/* Pregnancy & Medical History */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Heart className="w-5 h-5 text-medical-pink" />
                Pregnancy & Medical History
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <Label htmlFor="pregnancies" className="text-sm font-medium mb-2">
                    Total Pregnancies
                  </Label>
                  <Input
                    id="pregnancies"
                    type="number"
                    value={numberOfPregnancies}
                    onChange={(e) => setNumberOfPregnancies(e.target.value)}
                    placeholder="Total pregnancies"
                    min="0"
                    className="w-full"
                  />
                </div>

                <div>
                  <Label htmlFor="bmi" className="text-sm font-medium mb-2">
                    BMI Category (1-6)
                  </Label>
                  <Input
                    id="bmi"
                    type="number"
                    value={bmiCategory}
                    onChange={(e) => setBmiCategory(e.target.value)}
                    placeholder="Enter BMI category"
                    min="1"
                    max="6"
                    className="w-full"
                  />
                </div>
              </div>

              {/* Medical History */}
              <div className="space-y-4">
                <div>
                  <Label className="text-sm font-medium">Medical History</Label>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Choose Not provided when you do not know the answer.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="family-history">Family History of Diabetes</Label>
                    <select
                      id="family-history"
                      value={familyHistory}
                      onChange={(event) => setFamilyHistory(event.target.value as HistoryAnswer)}
                      className="mt-2 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    >
                      <option value="unknown">Not provided</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="pcos">PCOS (Polycystic Ovary Syndrome)</Label>
                    <select
                      id="pcos"
                      value={pcos}
                      onChange={(event) => setPcos(event.target.value as HistoryAnswer)}
                      className="mt-2 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    >
                      <option value="unknown">Not provided</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="prenatal-loss">History of Unexplained Prenatal Loss</Label>
                    <select
                      id="prenatal-loss"
                      value={unexplainedPrenatalLoss}
                      onChange={(event) => setUnexplainedPrenatalLoss(event.target.value as HistoryAnswer)}
                      className="mt-2 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    >
                      <option value="unknown">Not provided</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="large-child">History of Large Child or Birth Complications</Label>
                    <select
                      id="large-child"
                      value={largeChildOrBirthDefault}
                      onChange={(event) => setLargeChildOrBirthDefault(event.target.value as HistoryAnswer)}
                      className="mt-2 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    >
                      <option value="unknown">Not provided</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="prediabetes">Pre-existing Prediabetes</Label>
                    <select
                      id="prediabetes"
                      value={prediabetes}
                      onChange={(event) => setPrediabetes(event.target.value as HistoryAnswer)}
                      className="mt-2 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    >
                      <option value="unknown">Not provided</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/patient/dashboard')}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={saving}
                className="bg-gradient-to-r from-medical-pink to-medical-blue text-white hover:shadow-lg transition-all duration-300"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </form>

          <div className="mt-10 rounded-2xl border border-red-200 bg-red-50/70 p-6 shadow-sm">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-red-800">
              <UserX className="h-5 w-5" />
              Close Patient Account
            </h2>
            <p className="mt-2 text-sm text-red-700">
              This disables your sign-in, ends your doctor registration, and cancels future appointments. Your medical record and appointment history are retained.
            </p>
            <Label htmlFor="close-confirmation" className="mt-4 block text-sm font-medium text-red-800">
              Type CLOSE to confirm
            </Label>
            <div className="mt-2 flex flex-col gap-3 sm:flex-row">
              <Input
                id="close-confirmation"
                value={closeConfirmation}
                onChange={(event) => setCloseConfirmation(event.target.value)}
                placeholder="CLOSE"
                className="bg-white"
              />
              <Button
                type="button"
                onClick={closeAccount}
                disabled={closingAccount || closeConfirmation.trim().toUpperCase() !== 'CLOSE'}
                className="bg-red-600 text-white hover:bg-red-700 sm:min-w-40"
              >
                {closingAccount ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Close Account'}
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
