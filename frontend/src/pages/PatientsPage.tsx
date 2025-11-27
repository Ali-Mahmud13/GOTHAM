import { useState, useEffect } from "react";
import { Plus } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { PatientCard } from "@/components/PatientCard";
import { AddPatientModal } from "@/components/AddPatientModal";

interface PatientProfile {
  id: number;
  patient_identifier: string;
  name: string;
  age: number;
  contact_number: string;
  doctor_notes: string | null;
  ai_report: string | null;
  risk_level: 'high' | 'medium' | 'low';
  created_at: string;
  updated_at: string;
}

const API_URL = "http://localhost:8000";

const PatientsPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [patients, setPatients] = useState<PatientProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/patient-profiles/`);
      
      if (! response.ok) {
        throw new Error('Failed to fetch patients');
      }
      
      const data: PatientProfile[] = await response. json();
      setPatients(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching patients:', err);
      setError('Failed to load patients. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddPatient = async (newPatient: { id: string; name: string; age: string; phone: string }) => {
    try {
      // First, create the patient in patients table
      const patientResponse = await fetch(`${API_URL}/api/patients/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patient_identifier: newPatient.id,
          family_history: null,
          pcos: null,
          unexplained_prenatal_loss: null,
          large_child_or_birth_default: null,
          prediabetes: null,
        }),
      });
      
      if (!patientResponse.ok) {
        const errorData = await patientResponse. json();
        throw new Error(errorData.detail || 'Failed to create patient record');
      }

      // Then, create the patient profile
      const profileResponse = await fetch(`${API_URL}/api/patient-profiles/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patient_identifier: newPatient.id,
          name: newPatient.name,
          age: parseInt(newPatient.age),
          contact_number: newPatient.phone,
          doctor_notes: null,
          ai_report: null,
          risk_level: 'low',
        }),
      });
      
      if (!profileResponse. ok) {
        const errorData = await profileResponse.json();
        throw new Error(errorData. detail || 'Failed to create patient profile');
      }
      
      await fetchPatients(); // Refresh the list
      setIsModalOpen(false);
    } catch (err) {
      console.error('Error adding patient:', err);
      alert(`Failed to add patient: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-6 py-10">
          <div className="text-center text-lg">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent rounded-full text-medical-blue mb-4" />
            <p>Loading patients...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-6 py-10">
          <div className="text-center text-red-500">
            <p>{error}</p>
            <button 
              onClick={fetchPatients}
              className="mt-4 px-6 py-2 bg-medical-blue text-white rounded-lg hover:bg-medical-blue/90"
            >
              Retry
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-6 py-10">
        <div className="mb-10 flex items-start justify-between">
          <div>
            <div className="inline-block">
              <h2 className="text-4xl font-bold bg-gradient-to-r from-medical-pink via-medical-blue to-medical-pink bg-clip-text text-transparent mb-3 animate-float">
                All Patients
              </h2>
              <div className="h-1 w-32 bg-gradient-to-r from-medical-pink to-medical-blue rounded-full" />
            </div>
            <p className="text-muted-foreground mt-3 text-lg">
              Manage and monitor patient information and risk levels
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="group relative px-6 py-3 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add New Patient
            <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-medical-pink to-medical-blue opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-300" />
          </button>
        </div>

        {patients.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <p className="text-lg">No patients found. Add your first patient! </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pt-4">
            {patients.map((patient) => (
              <PatientCard
                key={patient. patient_identifier}
                id={patient.patient_identifier}
                name={patient.name}
                age={patient.age}
                contactNumber={patient.contact_number}
                riskLevel={patient. risk_level}
              />
            ))}
          </div>
        )}
      </main>

      <AddPatientModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAdd={handleAddPatient}
      />
    </div>
  );
};

export default PatientsPage;