import { useState } from "react";
import { Plus } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { PatientCard } from "@/components/PatientCard";
import { AddPatientModal } from "@/components/AddPatientModal";

interface Patient {
  id: string;
  name: string;
  age: string;
  contactNumber: string;
  riskLevel: 'high' | 'medium' | 'low';
}

const PatientsPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([
    {
      id: 'P001',
      name: 'Sarah Johnson',
      age: '28',
      contactNumber: '+1 (555) 123-4567',
      riskLevel: 'low',
    },
    {
      id: 'P002',
      name: 'Jennifer Wilson',
      age: '34',
      contactNumber: '+1 (555) 234-5678',
      riskLevel: 'high',
    },
    {
      id: 'P003',
      name: 'Emily Davis',
      age: '26',
      contactNumber: '+1 (555) 345-6789',
      riskLevel: 'low',
    },
    {
      id: 'P004',
      name: 'Amanda Brown',
      age: '31',
      contactNumber: '+1 (555) 456-7890',
      riskLevel: 'medium',
    },
    {
      id: 'P005',
      name: 'Maria Garcia',
      age: '29',
      contactNumber: '+1 (555) 567-8901',
      riskLevel: 'low',
    },
  ]);

  const handleAddPatient = (newPatient: { id: string; name: string; age: string; phone: string }) => {
    const patient: Patient = {
      id: newPatient.id,
      name: newPatient.name,
      age: newPatient. age,
      contactNumber: newPatient.phone,
      riskLevel: 'low', // Default to low risk
    };
    setPatients([...patients, patient]);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <Navbar />

      {/* Main Content */}
      <main className="container mx-auto px-6 py-10">
        {/* Header Section with Button */}
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

          {/* Add New Patient Button */}
          <button
            onClick={() => setIsModalOpen(true)}
            className="group relative px-6 py-3 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add New Patient
            
            {/* Button glow effect */}
            <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-medical-pink to-medical-blue opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-300" />
          </button>
        </div>

        {/* Patients Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pt-4">
          {patients.map((patient) => (
            <PatientCard
              key={patient. id}
              id={patient. id}
              name={patient. name}
              age={patient. age}
              contactNumber={patient.contactNumber}
              riskLevel={patient.riskLevel}
            />
          ))}
        </div>
      </main>

      {/* Add Patient Modal */}
      <AddPatientModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAdd={handleAddPatient}
      />
    </div>
  );
};

export default PatientsPage;