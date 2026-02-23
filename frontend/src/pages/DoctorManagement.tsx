import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/api';
import { Search, UserPlus, X, Stethoscope, CheckCircle, XCircle, ToggleLeft, ToggleRight } from 'lucide-react';

interface Doctor {
    id: number;
    full_name: string;
    email: string;
    specialization?: string;
    is_active: boolean;
    created_at?: string;
}

const DoctorManagement: React.FC = () => {
    const { user } = useAuth();
    const [doctors, setDoctors] = useState<Doctor[]>([]);
    const [filtered, setFiltered] = useState<Doctor[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [formError, setFormError] = useState('');
    const [formSuccess, setFormSuccess] = useState('');
    const [doctorForm, setDoctorForm] = useState({ full_name: '', email: '', password: '', specialization: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const loadDoctors = useCallback(async () => {
        try {
            setIsLoading(true);
            const res = await adminAPI.getDoctors();
            setDoctors(res.data);
            setFiltered(res.data);
        } catch (err) {
            console.error('Failed to load doctors:', err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => { loadDoctors(); }, [loadDoctors]);

    useEffect(() => {
        const q = searchQuery.toLowerCase();
        setFiltered(
            doctors.filter(d =>
                d.full_name.toLowerCase().includes(q) ||
                d.email.toLowerCase().includes(q) ||
                (d.specialization || '').toLowerCase().includes(q)
            )
        );
    }, [searchQuery, doctors]);

    const handleAddDoctor = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormError('');
        setFormSuccess('');
        setIsSubmitting(true);
        try {
            await adminAPI.createDoctor({ ...doctorForm, role: 'doctor' });
            setFormSuccess(`Dr. ${doctorForm.full_name} added successfully!`);
            setDoctorForm({ full_name: '', email: '', password: '', specialization: '' });
            await loadDoctors(); // Refresh list immediately
        } catch (err: any) {
            setFormError(err?.response?.data?.detail || 'Failed to create doctor.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleToggleActive = async (doctor: Doctor) => {
        try {
            if (doctor.is_active) {
                await adminAPI.deactivateDoctor(doctor.id);
            } else {
                await adminAPI.activateDoctor(doctor.id);
            }
            await loadDoctors();
            if (selectedDoctor?.id === doctor.id) {
                setSelectedDoctor(prev => prev ? { ...prev, is_active: !prev.is_active } : null);
            }
        } catch (err) {
            console.error('Failed to toggle doctor status:', err);
        }
    };

    if (user?.role !== 'admin') {
        return <div className="p-8 text-center text-gray-500">Access denied. Admin only.</div>;
    }

    const activeCount = doctors.filter(d => d.is_active).length;
    const inactiveCount = doctors.length - activeCount;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Doctor Management</h2>
                    <p className="text-sm text-gray-500 mt-1">
                        {activeCount} active · {inactiveCount} inactive · {doctors.length} total
                    </p>
                </div>
                <button
                    onClick={() => { setIsAddOpen(true); setFormError(''); setFormSuccess(''); }}
                    className="btn-primary flex items-center space-x-2"
                >
                    <UserPlus className="h-5 w-5" />
                    <span>Add Doctor</span>
                </button>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                    type="text"
                    placeholder="Search by name, email, or specialization..."
                    className="input-field pl-10 w-full"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Doctor List */}
                <div className="lg:col-span-1 bg-white shadow rounded-lg overflow-hidden">
                    <div className="px-4 py-4 border-b border-gray-200">
                        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Doctors ({filtered.length})</h3>
                    </div>
                    <ul className="divide-y divide-gray-100 h-[600px] overflow-y-auto">
                        {isLoading ? (
                            <li className="p-8 text-center text-gray-400">Loading...</li>
                        ) : filtered.length === 0 ? (
                            <li className="p-8 text-center text-gray-400">No doctors found</li>
                        ) : (
                            filtered.map(doc => (
                                <li
                                    key={doc.id}
                                    onClick={() => setSelectedDoctor(doc)}
                                    className={`p-4 cursor-pointer transition-colors hover:bg-gray-50 ${selectedDoctor?.id === doc.id ? 'bg-primary-50 border-l-4 border-primary-500' : ''}`}
                                >
                                    <div className="flex items-center space-x-3">
                                        <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center font-bold text-primary-700 flex-shrink-0">
                                            {doc.full_name.charAt(0)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-semibold text-gray-900 truncate">{doc.full_name}</p>
                                            <p className="text-xs text-gray-500 truncate">{doc.specialization || 'General'}</p>
                                        </div>
                                        <span className={`h-2 w-2 rounded-full flex-shrink-0 ${doc.is_active ? 'bg-green-400' : 'bg-gray-300'}`} title={doc.is_active ? 'Active' : 'Inactive'} />
                                    </div>
                                </li>
                            ))
                        )}
                    </ul>
                </div>

                {/* Detail Panel */}
                <div className="lg:col-span-2">
                    {selectedDoctor ? (
                        <div className="bg-white shadow rounded-lg p-6 space-y-6">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center space-x-4">
                                    <div className="h-16 w-16 rounded-full bg-primary-100 flex items-center justify-center text-2xl font-bold text-primary-700">
                                        {selectedDoctor.full_name.charAt(0)}
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-gray-900">{selectedDoctor.full_name}</h3>
                                        <div className="flex items-center space-x-2 mt-1">
                                            <Stethoscope className="h-4 w-4 text-primary-500" />
                                            <span className="text-sm text-primary-600 font-medium">
                                                {selectedDoctor.specialization || 'General Physician'}
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">{selectedDoctor.email}</p>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    {selectedDoctor.is_active ? (
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                            <CheckCircle className="h-3 w-3 mr-1" /> Active
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                            <XCircle className="h-3 w-3 mr-1" /> Inactive
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <p className="text-xs text-gray-500 font-semibold uppercase mb-1">Doctor ID</p>
                                    <p className="font-mono text-sm font-bold text-gray-800">#{selectedDoctor.id}</p>
                                </div>
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <p className="text-xs text-gray-500 font-semibold uppercase mb-1">Specialization</p>
                                    <p className="text-sm font-bold text-gray-800">{selectedDoctor.specialization || '—'}</p>
                                </div>
                                <div className="bg-gray-50 p-4 rounded-lg col-span-2">
                                    <p className="text-xs text-gray-500 font-semibold uppercase mb-1">Email</p>
                                    <p className="text-sm font-bold text-gray-800">{selectedDoctor.email}</p>
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                                <p className="text-sm text-gray-500">
                                    Account status: <span className={`font-semibold ${selectedDoctor.is_active ? 'text-green-600' : 'text-gray-500'}`}>
                                        {selectedDoctor.is_active ? 'Active' : 'Deactivated'}
                                    </span>
                                </p>
                                <button
                                    onClick={() => handleToggleActive(selectedDoctor)}
                                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${selectedDoctor.is_active
                                            ? 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200'
                                            : 'bg-green-50 text-green-600 hover:bg-green-100 border border-green-200'
                                        }`}
                                >
                                    {selectedDoctor.is_active ? (
                                        <><ToggleLeft className="h-4 w-4" /><span>Deactivate</span></>
                                    ) : (
                                        <><ToggleRight className="h-4 w-4" /><span>Activate</span></>
                                    )}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white shadow rounded-lg p-12 flex flex-col items-center justify-center text-center text-gray-400">
                            <Stethoscope className="h-14 w-14 text-gray-200 mb-4" />
                            <p className="font-medium">Select a doctor to view details</p>
                            <p className="text-sm mt-1">or click "Add Doctor" to create a new account</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Add Doctor Modal */}
            {isAddOpen && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-gray-900">Create Doctor Account</h3>
                            <button onClick={() => setIsAddOpen(false)} className="text-gray-400 hover:text-gray-600">
                                <X className="h-6 w-6" />
                            </button>
                        </div>

                        {formError && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{formError}</div>}
                        {formSuccess && <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-lg text-sm">{formSuccess}</div>}

                        <form onSubmit={handleAddDoctor} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                <input required className="input-field" placeholder="Dr. John Smith"
                                    value={doctorForm.full_name}
                                    onChange={e => setDoctorForm({ ...doctorForm, full_name: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                <input required type="email" className="input-field" placeholder="doctor@hospital.com"
                                    value={doctorForm.email}
                                    onChange={e => setDoctorForm({ ...doctorForm, email: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Temporary Password</label>
                                <input required type="password" className="input-field" placeholder="Min 8 characters"
                                    value={doctorForm.password}
                                    onChange={e => setDoctorForm({ ...doctorForm, password: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Specialization</label>
                                <select required className="input-field" value={doctorForm.specialization}
                                    onChange={e => setDoctorForm({ ...doctorForm, specialization: e.target.value })}>
                                    <option value="">Select Specialization</option>
                                    <option>General Physician</option>
                                    <option>Cardiologist</option>
                                    <option>Neurologist</option>
                                    <option>Orthopedist</option>
                                    <option>Pediatrician</option>
                                    <option>Dermatologist</option>
                                    <option>Psychiatrist</option>
                                    <option>Endocrinologist</option>
                                    <option>Gynecologist</option>
                                    <option>Oncologist</option>
                                    <option>Radiologist</option>
                                    <option>Surgeon</option>
                                </select>
                            </div>
                            <div className="flex justify-end space-x-3 pt-2">
                                <button type="button" onClick={() => setIsAddOpen(false)} className="btn-secondary">Cancel</button>
                                <button type="submit" disabled={isSubmitting} className="btn-primary disabled:opacity-60">
                                    <UserPlus className="h-4 w-4 mr-2 inline" />
                                    {isSubmitting ? 'Creating...' : 'Create Doctor'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DoctorManagement;
