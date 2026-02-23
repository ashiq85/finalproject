import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { appointmentsAPI } from '../services/api';
import { format } from 'date-fns';
import { Calendar, Clock, Plus, X, Video, User } from 'lucide-react';
import type { Appointment } from '../types';
import { AppointmentStatus } from '../types';

const Appointments: React.FC = () => {
    const { user } = useAuth();
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [newAppointment, setNewAppointment] = useState({
        doctor_id: 1,
        appointment_date: '',
        reason: '',
        duration_minutes: 30
    });

    const [isRescheduleModalOpen, setIsRescheduleModalOpen] = useState(false);
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
    const [rescheduleDate, setRescheduleDate] = useState('');

    useEffect(() => {
        loadAppointments();
    }, []);

    const loadAppointments = async () => {
        try {
            setIsLoading(true);
            const response = await appointmentsAPI.getAll();
            setAppointments(response.data);
        } catch (error) {
            console.error('Error loading appointments:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await appointmentsAPI.create(newAppointment);
            setIsModalOpen(false);
            setNewAppointment({ ...newAppointment, appointment_date: '', reason: '' });
            loadAppointments();
        } catch (error) {
            console.error('Error booking appointment:', error);
        }
    };

    const handleCancel = async (id: number) => {
        try {
            await appointmentsAPI.cancel(id);
            loadAppointments();
        } catch (error) {
            console.error('Error cancelling appointment:', error);
        }
    };

    const handleRescheduleRequest = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedAppointment) return;
        try {
            await appointmentsAPI.requestReschedule(selectedAppointment.id, rescheduleDate);
            setIsRescheduleModalOpen(false);
            setSelectedAppointment(null);
            setRescheduleDate('');
            loadAppointments();
        } catch (error) {
            console.error('Error requesting reschedule:', error);
        }
    };

    const handleApprove = async (id: number) => {
        try {
            await appointmentsAPI.approveReschedule(id);
            loadAppointments();
        } catch (error) {
            console.error('Error approving reschedule:', error);
        }
    };

    const handleReject = async (id: number) => {
        try {
            await appointmentsAPI.rejectReschedule(id);
            loadAppointments();
        } catch (error) {
            console.error('Error rejecting reschedule:', error);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
                    <p className="text-gray-500">Manage your clinical sessions and scheduling</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="btn-primary flex items-center"
                >
                    <Plus className="h-5 w-5 mr-2" />
                    Book New Session
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Statistics Cards */}
                <div className="card bg-primary-50 border-primary-100 flex items-center p-4">
                    <Calendar className="h-10 w-10 text-primary-600 mr-4" />
                    <div>
                        <p className="text-xs font-semibold text-primary-700 uppercase">Upcoming</p>
                        <p className="text-2xl font-bold text-gray-900">{appointments.filter(a => a.status === AppointmentStatus.SCHEDULED || a.status === AppointmentStatus.RESCHEDULE_REQUESTED).length}</p>
                    </div>
                </div>
                <div className="card bg-green-50 border-green-100 flex items-center p-4">
                    <Video className="h-10 w-10 text-green-600 mr-4" />
                    <div>
                        <p className="text-xs font-semibold text-green-700 uppercase">Telehealth</p>
                        <p className="text-2xl font-bold text-gray-900">2</p>
                    </div>
                </div>
                <div className="card bg-amber-50 border-amber-100 flex items-center p-4">
                    <Clock className="h-10 w-10 text-amber-600 mr-4" />
                    <div>
                        <p className="text-xs font-semibold text-amber-700 uppercase">Wait Time</p>
                        <p className="text-2xl font-bold text-gray-900">12m</p>
                    </div>
                </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <div className="flex border-b border-gray-200">
                    <button className="px-6 py-4 text-sm font-medium border-b-2 border-primary-500 text-primary-600">Upcoming Sessions</button>
                    <button className="px-6 py-4 text-sm font-medium text-gray-500 hover:text-gray-700">Past History</button>
                </div>
                <div className="p-0">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider / Patient</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date & Time</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {isLoading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">Loading appointments...</td>
                                </tr>
                            ) : appointments.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">No scheduled appointments found</td>
                                </tr>
                            ) : (
                                appointments.map((apt) => (
                                    <tr key={apt.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center mr-3">
                                                    <User className="h-4 w-4 text-gray-500" />
                                                </div>
                                                <div className="text-sm font-medium text-gray-900">
                                                    {user?.role === 'doctor' ? apt.patient?.user?.full_name : apt.doctor?.full_name || 'Dr. Smith'}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {format(new Date(apt.appointment_date), 'MMM d, yyyy')} • {format(new Date(apt.appointment_date), 'h:mm a')}
                                            {apt.status === AppointmentStatus.RESCHEDULE_REQUESTED && apt.requested_new_date && (
                                                <div className="text-xs text-amber-600 font-semibold mt-1">
                                                    Requested: {format(new Date(apt.requested_new_date), 'MMM d, h:mm a')}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                            {apt.reason}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 text-xs font-bold rounded-full ${apt.status === AppointmentStatus.SCHEDULED ? 'bg-green-100 text-green-700' :
                                                apt.status === AppointmentStatus.CANCELLED ? 'bg-red-100 text-red-700' :
                                                    apt.status === AppointmentStatus.RESCHEDULE_REQUESTED ? 'bg-amber-100 text-amber-700' :
                                                        'bg-gray-100 text-gray-700'
                                                }`}>
                                                {apt.status.replace('_', ' ').toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex justify-end space-x-3">
                                                {apt.status === AppointmentStatus.SCHEDULED && user?.role === 'patient' && (
                                                    <button
                                                        onClick={() => {
                                                            setSelectedAppointment(apt);
                                                            setIsRescheduleModalOpen(true);
                                                        }}
                                                        className="text-primary-600 hover:text-primary-900"
                                                    >
                                                        Reschedule
                                                    </button>
                                                )}
                                                {apt.status === AppointmentStatus.RESCHEDULE_REQUESTED && (user?.role === 'doctor' || user?.role === 'admin') && (
                                                    <>
                                                        <button
                                                            onClick={() => handleApprove(apt.id)}
                                                            className="text-green-600 hover:text-green-900 font-bold"
                                                        >
                                                            Approve
                                                        </button>
                                                        <button
                                                            onClick={() => handleReject(apt.id)}
                                                            className="text-red-600 hover:text-red-900 font-bold"
                                                        >
                                                            Reject
                                                        </button>
                                                    </>
                                                )}
                                                {apt.status === AppointmentStatus.SCHEDULED && (
                                                    <button
                                                        onClick={() => handleCancel(apt.id)}
                                                        className="text-red-600 hover:text-red-900"
                                                    >
                                                        Cancel
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Book Appointment Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-gray-900">Schedule Session</h3>
                            <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-500">
                                <X className="h-6 w-6" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="label">Appointment Date & Time</label>
                                <input
                                    type="datetime-local"
                                    required
                                    className="input-field"
                                    value={newAppointment.appointment_date}
                                    onChange={(e) => setNewAppointment({ ...newAppointment, appointment_date: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="label">Reason for Visit</label>
                                <textarea
                                    required
                                    className="input-field"
                                    rows={3}
                                    value={newAppointment.reason}
                                    onChange={(e) => setNewAppointment({ ...newAppointment, reason: e.target.value })}
                                    placeholder="Briefly describe the purpose of this appointment..."
                                />
                            </div>

                            <div className="flex justify-end space-x-3 pt-6">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="btn-secondary"
                                >
                                    Go Back
                                </button>
                                <button
                                    type="submit"
                                    className="btn-primary"
                                >
                                    Confirm Scheduling
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Reschedule Request Modal */}
            {isRescheduleModalOpen && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-gray-900">Request New Slot</h3>
                            <button onClick={() => setIsRescheduleModalOpen(false)} className="text-gray-400 hover:text-gray-500">
                                <X className="h-6 w-6" />
                            </button>
                        </div>

                        <form onSubmit={handleRescheduleRequest} className="space-y-4">
                            <div className="bg-amber-50 p-3 rounded-md mb-4 text-xs text-amber-800">
                                Current scheduled date: {selectedAppointment && format(new Date(selectedAppointment.appointment_date), 'MMM d, yyyy h:mm a')}
                            </div>
                            <div>
                                <label className="label">Requested Date & Time</label>
                                <input
                                    type="datetime-local"
                                    required
                                    className="input-field"
                                    value={rescheduleDate}
                                    onChange={(e) => setRescheduleDate(e.target.value)}
                                />
                            </div>

                            <div className="flex justify-end space-x-3 pt-6">
                                <button
                                    type="button"
                                    onClick={() => setIsRescheduleModalOpen(false)}
                                    className="btn-secondary"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn-primary"
                                >
                                    Submit Request
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Appointments;
