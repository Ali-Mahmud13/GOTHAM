import { useState } from "react";
import { X, Hash } from "lucide-react";
import { cn } from "@/lib/utils";

interface AddPatientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (patient: { id: string; name: string; age: string; phone: string }) => void;
}

export const AddPatientModal = ({ isOpen, onClose, onAdd }: AddPatientModalProps) => {
  const [patientId, setPatientId] = useState("");
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [phone, setPhone] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (patientId && name && age && phone) {
      onAdd({ id: patientId, name, age, phone });
      // Reset form
      setPatientId("");
      setName("");
      setAge("");
      setPhone("");
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-in fade-in duration-300">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md relative animate-in zoom-in-95 duration-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-medical-pink to-medical-blue p-6 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white">Add New Patient</h2>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <p className="text-white/80 text-sm mt-2">Enter patient information below</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Patient ID Field (Manual Entry) */}
          <div>
            <label htmlFor="patientId" className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Hash className="w-4 h-4 text-medical-blue" />
              Patient ID
            </label>
            <input
              id="patientId"
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e. target.value)}
              placeholder="e.g., P011, P012"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-medical-blue focus:border-transparent transition-all outline-none"
            />
          </div>

          {/* Name Field */}
          <div>
            <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2">
              Patient Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter full name"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-medical-blue focus:border-transparent transition-all outline-none"
            />
          </div>

          {/* Age Field */}
          <div>
            <label htmlFor="age" className="block text-sm font-semibold text-gray-700 mb-2">
              Age
            </label>
            <input
              id="age"
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              placeholder="Enter age"
              required
              min="0"
              max="150"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-medical-blue focus:border-transparent transition-all outline-none"
            />
          </div>

          {/* Phone Number Field */}
          <div>
            <label htmlFor="phone" className="block text-sm font-semibold text-gray-700 mb-2">
              Phone Number
            </label>
            <input
              id="phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+1 (555) 123-4567"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-medical-blue focus:border-transparent transition-all outline-none"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-gradient-to-r from-medical-pink to-medical-blue text-white font-semibold rounded-lg hover:shadow-lg hover:scale-105 transition-all"
            >
              Add Patient
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};