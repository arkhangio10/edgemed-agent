import { create } from 'zustand';

export interface Patient {
  id: string;
  name: string;
  age: number;
  sex: string;
  createdAt: string;
}

export interface PatientRecord {
  id: string;
  patientId: string;
  note: string;
  extractedData: any;
  safetyFlags: any;
  createdAt: string;
  status: 'draft' | 'saved';
}

interface PatientStore {
  patients: Patient[];
  records: PatientRecord[];
  selectedPatientId: string | null;
  addPatient: (patient: Omit<Patient, 'id' | 'createdAt'>) => string;
  deletePatient: (id: string) => void;
  selectPatient: (id: string | null) => void;
  addRecord: (record: Omit<PatientRecord, 'id' | 'createdAt'>) => void;
  getPatientRecords: (patientId: string) => PatientRecord[];
}

function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : fallback;
  } catch { return fallback; }
}

function saveToStorage(key: string, data: any) {
  localStorage.setItem(key, JSON.stringify(data));
}

const PATIENTS_KEY = 'edgemed_patients';
const RECORDS_KEY = 'edgemed_records';

const initialPatients: Patient[] = loadFromStorage(PATIENTS_KEY, [
  { id: 'p-001', name: 'Maria Gonzalez', age: 54, sex: 'Female', createdAt: '2025-02-22T10:00:00Z' },
  { id: 'p-002', name: 'James Rivera', age: 67, sex: 'Male', createdAt: '2025-02-21T09:00:00Z' },
  { id: 'p-003', name: 'Ana López', age: 32, sex: 'Female', createdAt: '2025-02-20T14:00:00Z' },
]);

const initialRecords: PatientRecord[] = loadFromStorage(RECORDS_KEY, []);

export const usePatientStore = create<PatientStore>((set, get) => ({
  patients: initialPatients,
  records: initialRecords,
  selectedPatientId: null,

  addPatient: (data) => {
    const id = `p-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    const patient: Patient = { ...data, id, createdAt: new Date().toISOString() };
    set((s) => {
      const patients = [...s.patients, patient];
      saveToStorage(PATIENTS_KEY, patients);
      return { patients };
    });
    return id;
  },

  deletePatient: (id) => {
    set((s) => {
      const patients = s.patients.filter((p) => p.id !== id);
      const records = s.records.filter((r) => r.patientId !== id);
      saveToStorage(PATIENTS_KEY, patients);
      saveToStorage(RECORDS_KEY, records);
      return { patients, records, selectedPatientId: s.selectedPatientId === id ? null : s.selectedPatientId };
    });
  },

  selectPatient: (id) => set({ selectedPatientId: id }),

  addRecord: (data) => {
    const id = `rec-${Date.now()}`;
    const record: PatientRecord = { ...data, id, createdAt: new Date().toISOString() };
    set((s) => {
      const records = [...s.records, record];
      saveToStorage(RECORDS_KEY, records);
      return { records };
    });
  },

  getPatientRecords: (patientId) => {
    return get().records.filter((r) => r.patientId === patientId);
  },
}));
