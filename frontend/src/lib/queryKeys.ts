export type QueryKeyPart = string | number | boolean | null | undefined;

export const queryKeys = {
  dashboard: {
    stats: ["dashboard", "stats"] as const,
    riskTrends: (days: number) => ["dashboard", "risk-trends", days] as const,
    weeklyAssessments: ["dashboard", "weekly-assessments"] as const,
  },
  patients: {
    all: ["patients"] as const,
    detail: (patientId: string | number) => ["patients", "detail", patientId] as const,
    visits: (patientId: string | number) => ["patients", "visits", patientId] as const,
    ultrasounds: (patientId: string | number) => ["patients", "ultrasounds", patientId] as const,
    portalProfile: ["patients", "portal-profile"] as const,
    portalVisits: ["patients", "portal-visits"] as const,
  },
  appointments: {
    all: ["appointments"] as const,
    list: (scope: string) => ["appointments", "list", scope] as const,
    upcoming: ["appointments", "list", "upcoming"] as const,
    myDoctor: ["appointments", "my-doctor"] as const,
    doctors: ["appointments", "doctors"] as const,
    bookingConfig: ["appointments", "booking-config"] as const,
    availability: (doctorId: number | string) =>
      ["appointments", "availability", doctorId] as const,
    exceptions: (doctorId: number | string) =>
      ["appointments", "exceptions", doctorId] as const,
    slots: (doctorId: number | string, date: string, excludeId?: number) =>
      ["appointments", "slots", doctorId, date, excludeId ?? null] as const,
  },
  registration: {
    all: ["registration"] as const,
    doctorRequests: ["registration", "doctor-requests"] as const,
    patientRequests: ["registration", "patient-requests"] as const,
  },
  notifications: {
    all: ["notifications"] as const,
    reschedule: ["notifications", "reschedule"] as const,
    cancellation: ["notifications", "cancellation"] as const,
    newBookings: ["notifications", "new-bookings"] as const,
  },
  schedule: {
    all: ["schedule"] as const,
    mine: ["schedule", "mine"] as const,
    exceptions: ["schedule", "exceptions"] as const,
  },
  auth: {
    me: ["auth", "me"] as const,
    pendingDoctors: ["auth", "pending-doctors"] as const,
  },
} as const;
