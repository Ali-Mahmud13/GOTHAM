import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Loader2, AlertCircle, User, Phone, Calendar, Heart, ArrowLeft } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { PatientNavbar } from '@/components/PatientNavbar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';

const API_URL = 'http://localhost:8000';

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
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [age, setAge] = useState<string>('');
  const [contactNumber, setContactNumber] = useState('');
  const [numberOfPregnancies, setNumberOfPregnancies] = useState<string>('');
  const [bmiCategory, setBmiCategory] = useState<string>('');
  const [familyHistory, setFamilyHistory] = useState(false);
  const [pcos, setPcos] = useState(false);
  const [unexplainedPrenatalLoss, setUnexplainedPrenatalLoss] = useState(false);
  const [largeChildOrBirthDefault, setLargeChildOrBirthDefault] = useState(false);
  const [prediabetes, setPrediabetes] = useState(false);

  const patientIdentifier = user?.patient_info?.patient_identifier;

  useEffect(() => {
    if (!isAuthenticated || !user || user.role !== 'patient' || !patientIdentifier) {
      navigate('/patient/login');
      return;
    }
    fetchProfile();
  }, [isAuthenticated, user, patientIdentifier, navigate]);

  const fetchProfile = async () => {
    if (!patientIdentifier) return;

    try {
      const response = await fetch(`${API_URL}/api/patient-portal/profile/${patientIdentifier}`);
      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }
      
      const data: PatientProfile = await response.json();
      
      // Set form values
      setAge(data.age > 0 ? String(data.age) : '');
      setContactNumber(data.contact_number || '');
      setNumberOfPregnancies(data.number_of_pregnancies !== null ? String(data.number_of_pregnancies) : '');
      setBmiCategory(data.bmi_category !== null ? String(data.bmi_category) : '');
      setFamilyHistory(data.family_history || false);
      setPcos(data.pcos || false);
      setUnexplainedPrenatalLoss(data.unexplained_prenatal_loss || false);
      setLargeChildOrBirthDefault(data.large_child_or_birth_default || false);
      setPrediabetes(data.prediabetes || false);
      
      setError('');
    } catch (err: any) {
      console.error('Error fetching profile:', err);
      setError('Failed to load profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

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
      const updateData: any = {
        contact_number: contactNumber.trim()
      };

      // Only include fields that have values
      if (age) updateData.age = parseInt(age);
      if (numberOfPregnancies) updateData.number_of_pregnancies = parseInt(numberOfPregnancies);
      if (bmiCategory) updateData.bmi_category = parseInt(bmiCategory);
      
      updateData.family_history = familyHistory;
      updateData.pcos = pcos;
      updateData.unexplained_prenatal_loss = unexplainedPrenatalLoss;
      updateData.large_child_or_birth_default = largeChildOrBirthDefault;
      updateData.prediabetes = prediabetes;

      const response = await fetch(`${API_URL}/api/patient-portal/profile/${patientIdentifier}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update profile');
      }

      setSuccess('Profile updated successfully!');
      setTimeout(() => {
        navigate('/patient/dashboard');
      }, 1500);
    } catch (err: any) {
      console.error('Update error:', err);
      setError(err.message || 'Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30">
        <PatientNavbar />
        <main className="container mx-auto px-6 py-10">
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
      
      <main className="container mx-auto px-6 py-10">
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
                    Number of Pregnancies
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

              {/* Medical Conditions Checkboxes */}
              <div className="space-y-4">
                <Label className="text-sm font-medium">Medical Conditions</Label>
                
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="family-history"
                      checked={familyHistory}
                      onCheckedChange={(checked) => setFamilyHistory(checked as boolean)}
                    />
                    <label
                      htmlFor="family-history"
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      Family History of Diabetes
                    </label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pcos"
                      checked={pcos}
                      onCheckedChange={(checked) => setPcos(checked as boolean)}
                    />
                    <label htmlFor="pcos" className="text-sm font-medium leading-none">
                      PCOS (Polycystic Ovary Syndrome)
                    </label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="prenatal-loss"
                      checked={unexplainedPrenatalLoss}
                      onCheckedChange={(checked) => setUnexplainedPrenatalLoss(checked as boolean)}
                    />
                    <label htmlFor="prenatal-loss" className="text-sm font-medium leading-none">
                      History of Unexplained Prenatal Loss
                    </label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="large-child"
                      checked={largeChildOrBirthDefault}
                      onCheckedChange={(checked) => setLargeChildOrBirthDefault(checked as boolean)}
                    />
                    <label htmlFor="large-child" className="text-sm font-medium leading-none">
                      History of Large Child or Birth Complications
                    </label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="prediabetes"
                      checked={prediabetes}
                      onCheckedChange={(checked) => setPrediabetes(checked as boolean)}
                    />
                    <label htmlFor="prediabetes" className="text-sm font-medium leading-none">
                      Pre-existing Prediabetes
                    </label>
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
        </div>
      </main>
    </div>
  );
};
