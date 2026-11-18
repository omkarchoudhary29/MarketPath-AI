import React, { useEffect, useState } from 'react';
import {
  CalendarCheck,
  Headphones,
  CheckCircle2,
  Clock,
  RefreshCw,
  Search,
  UserCheck,
  Video,
  XCircle,
  Plus,
  Trash2,
  Calendar,
  AlertCircle,
  ShieldAlert,
  X,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';

interface Consultation {
  id: string;
  reference_code: string;
  full_name: string;
  email: string;
  phone?: string | null;
  brand_name: string;
  category: string;
  business_stage: string;
  monthly_revenue?: string | null;
  challenges?: string | null;
  preferred_date?: string | null;
  preferred_time_slot?: string | null;
  timezone: string;
  status: string;
  assigned_consultant_id?: string | null;
  assigned_consultant_name?: string | null;
  scheduled_at?: string | null;
  duration_minutes: number;
  meeting_link?: string | null;
  notes?: string | null;
  internal_notes?: string | null;
  report_summary?: string | null;
  recommendations: string[];
  action_items: string[];
  cancellation_reason?: string | null;
  email_delivery_status: string;
  created_at: string;
  updated_at: string;
}

interface AdminConsultationData {
  stats: {
    total_consultations: number;
    submitted_count: number;
    assigned_count: number;
    confirmed_count: number;
    completed_count: number;
    cancelled_count: number;
    status_breakdown: Record<string, number>;
  };
  consultations: Consultation[];
}

interface AdminServiceOrder {
  id: string;
  organization_id: string;
  service_type: string;
  scope_description: string;
  quoted_price_inr: number;
  assigned_operator_id?: string;
  status: string;
  deliverables_notes?: string;
  created_at: string;
}

interface AvailabilityRule {
  id: string;
  rule_type: string;
  specific_date?: string | null;
  day_of_week?: number | null;
  start_time?: string | null;
  end_time?: string | null;
  slot_capacity: number;
  is_blocked: boolean;
  notes?: string | null;
  created_at: string;
}

interface PlatformUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export const AdminSupportPage: React.FC = () => {
  const { session } = useAuth();
  const { addToast } = useApp();
  const token = session?.access_token;

  const [activeTab, setActiveTab] = useState<'consultations' | 'rules' | 'orders'>('consultations');

  // Consultation State
  const [consultationsData, setConsultationsData] = useState<AdminConsultationData | null>(null);
  const [consultationSearch, setConsultationSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoadingConsultations, setIsLoadingConsultations] = useState(false);

  // Managed Service Orders State
  const [orders, setOrders] = useState<AdminServiceOrder[]>([]);
  const [isLoadingOrders, setIsLoadingOrders] = useState(false);

  // Availability Rules State
  const [rules, setRules] = useState<AvailabilityRule[]>([]);
  const [isLoadingRules, setIsLoadingRules] = useState(false);
  const [newRuleForm, setNewRuleForm] = useState({
    rule_type: 'blocked_date',
    specific_date: '',
    slot_capacity: 1,
    is_blocked: true,
    notes: '',
  });

  // Users for Consultant Assignment
  const [users, setUsers] = useState<PlatformUser[]>([]);

  // Modals
  const [assignModalItem, setAssignModalItem] = useState<Consultation | null>(null);
  const [assignForm, setAssignForm] = useState({ consultantId: '', consultantName: '' });

  const [confirmModalItem, setConfirmModalItem] = useState<Consultation | null>(null);
  const [confirmForm, setConfirmForm] = useState({ scheduledAt: '', meetingLink: '', duration: 30 });

  const [rescheduleModalItem, setRescheduleModalItem] = useState<Consultation | null>(null);
  const [rescheduleForm, setRescheduleForm] = useState({ date: '', slot: '10:00 AM – 10:30 AM IST', reason: '' });

  const [cancelModalItem, setCancelModalItem] = useState<Consultation | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  // Fetch Consultations
  const fetchConsultations = async () => {
    if (!token) return;
    setIsLoadingConsultations(true);
    try {
      const url = statusFilter === 'all'
        ? '/api/v1/admin/consultations'
        : `/api/v1/admin/consultations?status=${statusFilter}`;
      const data = await apiClient<AdminConsultationData>(url, { token });
      setConsultationsData(data);
    } catch (err: any) {
      console.error('Failed to load admin consultations:', err);
    } finally {
      setIsLoadingConsultations(false);
    }
  };

  // Fetch Service Orders
  const fetchOrders = async () => {
    if (!token) return;
    setIsLoadingOrders(true);
    try {
      const data = await apiClient<AdminServiceOrder[]>('/api/v1/admin/service-orders', { token });
      setOrders(data || []);
    } catch (err: any) {
      console.error('Failed to load admin service orders:', err);
    } finally {
      setIsLoadingOrders(false);
    }
  };

  // Fetch Rules
  const fetchRules = async () => {
    if (!token) return;
    setIsLoadingRules(true);
    try {
      const data = await apiClient<AvailabilityRule[]>('/api/v1/consultations/availability/rules', { token });
      setRules(data || []);
    } catch (err: any) {
      console.error('Failed to load availability rules:', err);
    } finally {
      setIsLoadingRules(false);
    }
  };

  // Fetch Users for Assignment
  const fetchUsers = async () => {
    if (!token) return;
    try {
      const data = await apiClient<any>('/api/v1/admin/users', { token });
      const userList = Array.isArray(data) ? data : data?.users || [];
      setUsers(userList);
    } catch (err) {
      console.error('Failed to fetch platform users:', err);
    }
  };

  useEffect(() => {
    if (token) {
      fetchConsultations();
      fetchOrders();
      fetchRules();
      fetchUsers();
    }
  }, [token, statusFilter]);

  // Handle Consultant Assignment
  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignModalItem || !token) return;
    try {
      await apiClient(`/api/v1/consultations/${assignModalItem.id}/assign`, {
        method: 'POST',
        token,
        body: JSON.stringify({
          consultant_id: assignForm.consultantId,
          consultant_name: assignForm.consultantName,
        }),
      });
      addToast({
        type: 'success',
        title: 'Consultant Assigned',
        message: `Assigned ${assignForm.consultantName} to ${assignModalItem.brand_name}.`,
      });
      setAssignModalItem(null);
      fetchConsultations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Assignment Failed',
        message: err.message || 'Could not assign consultant.',
      });
    }
  };

  // Handle Confirm
  const handleConfirmSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!confirmModalItem || !token) return;
    try {
      await apiClient(`/api/v1/consultations/${confirmModalItem.id}/confirm`, {
        method: 'POST',
        token,
        body: JSON.stringify({
          scheduled_at: new Date(confirmForm.scheduledAt).toISOString(),
          meeting_link: confirmForm.meetingLink || undefined,
          duration_minutes: Number(confirmForm.duration) || 30,
        }),
      });
      addToast({
        type: 'success',
        title: 'Consultation Confirmed',
        message: `Booking for ${confirmModalItem.brand_name} confirmed.`,
      });
      setConfirmModalItem(null);
      fetchConsultations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Confirmation Failed',
        message: err.message || 'Could not confirm booking.',
      });
    }
  };

  // Handle Reschedule
  const handleRescheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rescheduleModalItem || !token) return;
    try {
      await apiClient(`/api/v1/consultations/${rescheduleModalItem.id}/reschedule`, {
        method: 'POST',
        token,
        body: JSON.stringify({
          preferred_date: rescheduleForm.date,
          preferred_time_slot: rescheduleForm.slot,
          reason: rescheduleForm.reason || null,
        }),
      });
      addToast({
        type: 'success',
        title: 'Booking Rescheduled',
        message: `New slot recorded for ${rescheduleModalItem.brand_name}.`,
      });
      setRescheduleModalItem(null);
      fetchConsultations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Reschedule Failed',
        message: err.message || 'Could not reschedule booking.',
      });
    }
  };

  // Handle Cancel
  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancelModalItem || !token) return;
    try {
      await apiClient(`/api/v1/consultations/${cancelModalItem.id}/cancel`, {
        method: 'POST',
        token,
        body: JSON.stringify({ reason: cancelReason }),
      });
      addToast({
        type: 'info',
        title: 'Booking Cancelled',
        message: `Booking for ${cancelModalItem.brand_name} cancelled with reason recorded.`,
      });
      setCancelModalItem(null);
      setCancelReason('');
      fetchConsultations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Cancellation Failed',
        message: err.message || 'Could not cancel booking.',
      });
    }
  };

  // Handle Add Availability Rule
  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      await apiClient('/api/v1/consultations/availability/rules', {
        method: 'POST',
        token,
        body: JSON.stringify({
          rule_type: newRuleForm.rule_type,
          specific_date: newRuleForm.specific_date || null,
          slot_capacity: Number(newRuleForm.slot_capacity) || 1,
          is_blocked: newRuleForm.is_blocked,
          notes: newRuleForm.notes || null,
        }),
      });
      addToast({
        type: 'success',
        title: 'Rule Created',
        message: 'Consultation availability rule successfully activated.',
      });
      setNewRuleForm({
        rule_type: 'blocked_date',
        specific_date: '',
        slot_capacity: 1,
        is_blocked: true,
        notes: '',
      });
      fetchRules();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Failed to Create Rule',
        message: err.message || 'Could not create availability rule.',
      });
    }
  };

  // Handle Delete Rule
  const handleDeleteRule = async (ruleId: string) => {
    if (!token) return;
    try {
      await apiClient(`/api/v1/consultations/availability/rules/${ruleId}`, {
        method: 'DELETE',
        token,
      });
      addToast({
        type: 'info',
        title: 'Rule Removed',
        message: 'Availability rule deleted.',
      });
      fetchRules();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Failed to Delete Rule',
        message: err.message || 'Could not delete rule.',
      });
    }
  };

  // Filtered Consultations
  const filteredConsultations = (consultationsData?.consultations || []).filter((item) => {
    if (!consultationSearch) return true;
    const term = consultationSearch.toLowerCase();
    return (
      item.reference_code.toLowerCase().includes(term) ||
      item.brand_name.toLowerCase().includes(term) ||
      item.full_name.toLowerCase().includes(term) ||
      item.email.toLowerCase().includes(term)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">Confirmed</span>;
      case 'assigned':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-400 border border-blue-800">Assigned</span>;
      case 'completed':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950 text-purple-400 border border-purple-800">Completed</span>;
      case 'rescheduled':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-400 border border-amber-800">Rescheduled</span>;
      case 'cancelled':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800">Cancelled</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-300 border border-slate-700">{status}</span>;
    }
  };

  const getEmailStatusBadge = (status: string) => {
    switch (status) {
      case 'delivered':
        return <span className="text-[10px] font-mono text-emerald-400 font-bold">delivered</span>;
      case 'unconfigured_provider':
        return <span className="text-[10px] font-mono text-slate-400" title="Email credentials absent, logged locally">unconfigured (logged)</span>;
      case 'failed':
        return <span className="text-[10px] font-mono text-rose-400 font-bold">delivery failed</span>;
      default:
        return <span className="text-[10px] font-mono text-slate-500">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl font-mono text-xs text-slate-200">
      {/* Top Header */}
      <div className="pb-4 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-rose-400">Platform Operations Hub</span>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5 font-sans">
            Consultations, Advisory Triage & Service Pipeline
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage public consultation intake, assign advisors, regulate slot availability rules, and fulfill bespoke merchant services.
          </p>
        </div>

        {/* Global Refresh */}
        <button
          onClick={() => {
            fetchConsultations();
            fetchOrders();
            fetchRules();
          }}
          className="p-2 text-slate-400 hover:text-white rounded-lg border border-slate-800 bg-slate-900 self-start md:self-auto cursor-pointer"
          title="Refresh All Operations Data"
        >
          <RefreshCw className={`w-4 h-4 ${isLoadingConsultations || isLoadingOrders ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('consultations')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'consultations'
              ? 'bg-slate-900 text-emerald-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <CalendarCheck className="w-4 h-4" />
          <span>Inbound Consultations ({consultationsData?.stats?.total_consultations || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'rules'
              ? 'bg-slate-900 text-emerald-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Availability & Capacity Rules ({rules.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('orders')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'orders'
              ? 'bg-slate-900 text-emerald-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Headphones className="w-4 h-4" />
          <span>Managed Service Orders ({orders.length})</span>
        </button>
      </div>

      {/* TAB 1: INBOUND CONSULTATIONS */}
      {activeTab === 'consultations' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Total Inbound</span>
              <span className="text-xl font-extrabold text-white">{consultationsData?.stats?.total_consultations || 0}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Awaiting Triage</span>
              <span className="text-xl font-extrabold text-amber-400">{consultationsData?.stats?.submitted_count || 0}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Assigned</span>
              <span className="text-xl font-extrabold text-blue-400">{consultationsData?.stats?.assigned_count || 0}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Confirmed</span>
              <span className="text-xl font-extrabold text-emerald-400">{consultationsData?.stats?.confirmed_count || 0}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Completed</span>
              <span className="text-xl font-extrabold text-purple-400">{consultationsData?.stats?.completed_count || 0}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Cancelled</span>
              <span className="text-xl font-extrabold text-rose-400">{consultationsData?.stats?.cancelled_count || 0}</span>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-80">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                <Search className="w-3.5 h-3.5" />
              </div>
              <input
                type="text"
                value={consultationSearch}
                onChange={(e) => setConsultationSearch(e.target.value)}
                placeholder="Search ref, brand, name, email..."
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
              {['all', 'submitted', 'assigned', 'confirmed', 'completed', 'cancelled'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase transition-colors cursor-pointer ${
                    statusFilter === st
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Consultations Table */}
          <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden">
            {filteredConsultations.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                No consultation requests found matching your filter criteria.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="py-3 px-4">Ref Code</th>
                      <th className="py-3 px-4">Brand & Category</th>
                      <th className="py-3 px-4">Merchant Contact</th>
                      <th className="py-3 px-4">Requested Slot</th>
                      <th className="py-3 px-4">Assigned Advisor</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Email Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {filteredConsultations.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-900/50 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                          {item.reference_code}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-bold text-white">{item.brand_name}</div>
                          <div className="text-[10px] text-slate-400">{item.category} • {item.business_stage}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-white">{item.full_name}</div>
                          <div className="text-[10px] text-slate-400">{item.email}</div>
                          {item.phone && <div className="text-[10px] text-slate-500">{item.phone}</div>}
                        </td>
                        <td className="py-3 px-4">
                          <div>{item.preferred_date || 'Date TBD'}</div>
                          <div className="text-[10px] text-slate-400">{item.preferred_time_slot || 'Standard Slot'}</div>
                        </td>
                        <td className="py-3 px-4">
                          {item.assigned_consultant_name ? (
                            <span className="text-white font-medium flex items-center gap-1">
                              <UserCheck className="w-3.5 h-3.5 text-blue-400" />
                              {item.assigned_consultant_name}
                            </span>
                          ) : (
                            <span className="text-amber-400 italic">Unassigned</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {getStatusBadge(item.status)}
                        </td>
                        <td className="py-3 px-4">
                          {getEmailStatusBadge(item.email_delivery_status)}
                        </td>
                        <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                          {/* Assign Action */}
                          <button
                            onClick={() => {
                              setAssignModalItem(item);
                              setAssignForm({
                                consultantId: item.assigned_consultant_id || (users[0]?.id || ''),
                                consultantName: item.assigned_consultant_name || (users[0]?.full_name || ''),
                              });
                            }}
                            className="px-2 py-1 rounded bg-slate-900 text-blue-400 border border-slate-700 hover:bg-slate-800 cursor-pointer"
                            title="Assign Internal Specialist"
                          >
                            Assign
                          </button>

                          {/* Confirm Action */}
                          {item.status !== 'confirmed' && item.status !== 'completed' && item.status !== 'cancelled' && (
                            <button
                              onClick={() => {
                                setConfirmModalItem(item);
                                setConfirmForm({
                                  scheduledAt: item.preferred_date ? `${item.preferred_date}T10:00` : '',
                                  meetingLink: `https://meet.marketpath.ai/consult-${item.reference_code.toLowerCase()}`,
                                  duration: 30,
                                });
                              }}
                              className="px-2 py-1 rounded bg-slate-900 text-emerald-400 border border-slate-700 hover:bg-slate-800 cursor-pointer"
                              title="Confirm Slot & Send Calendar Invite"
                            >
                              Confirm
                            </button>
                          )}

                          {/* Reschedule Action */}
                          {item.status !== 'completed' && item.status !== 'cancelled' && (
                            <button
                              onClick={() => {
                                setRescheduleModalItem(item);
                                setRescheduleForm({
                                  date: item.preferred_date || '',
                                  slot: item.preferred_time_slot || '10:00 AM – 10:30 AM IST',
                                  reason: '',
                                });
                              }}
                              className="px-2 py-1 rounded bg-slate-900 text-amber-400 border border-slate-700 hover:bg-slate-800 cursor-pointer"
                              title="Reschedule Appointment"
                            >
                              Reschedule
                            </button>
                          )}

                          {/* Cancel Action */}
                          {item.status !== 'cancelled' && item.status !== 'completed' && (
                            <button
                              onClick={() => {
                                setCancelModalItem(item);
                                setCancelReason('');
                              }}
                              className="px-2 py-1 rounded bg-slate-900 text-rose-400 border border-slate-700 hover:bg-slate-800 cursor-pointer"
                              title="Cancel Booking"
                            >
                              Cancel
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: AVAILABILITY & CAPACITY RULES */}
      {activeTab === 'rules' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Add New Rule Form */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-6 rounded-3xl bg-slate-950 border border-slate-800 space-y-4">
              <h3 className="text-base font-bold text-white font-sans flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-400" />
                Configure Availability Rule
              </h3>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                Add date blackouts, company holidays, or slot capacity limits to prevent intake overflow.
              </p>

              <form onSubmit={handleCreateRule} className="space-y-3">
                <div>
                  <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Rule Type</label>
                  <select
                    value={newRuleForm.rule_type}
                    onChange={(e) => setNewRuleForm({ ...newRuleForm, rule_type: e.target.value })}
                    className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs cursor-pointer"
                  >
                    <option value="blocked_date">Block Specific Date (Holiday/Unavailable)</option>
                    <option value="custom_capacity">Slot Capacity Override</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Specific Date *</label>
                  <input
                    type="date"
                    required
                    value={newRuleForm.specific_date}
                    onChange={(e) => setNewRuleForm({ ...newRuleForm, specific_date: e.target.value })}
                    className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Slot Capacity</label>
                  <input
                    type="number"
                    min={0}
                    max={10}
                    value={newRuleForm.slot_capacity}
                    onChange={(e) => setNewRuleForm({ ...newRuleForm, slot_capacity: Number(e.target.value) })}
                    className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">0 = completely blocked, 1 = exclusive 1-on-1</span>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Reason / Notes</label>
                  <input
                    type="text"
                    value={newRuleForm.notes}
                    onChange={(e) => setNewRuleForm({ ...newRuleForm, notes: e.target.value })}
                    placeholder="E.g., Diwali Platform Holiday"
                    className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs"
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="w-full py-2.5 px-4 rounded-xl bg-forest text-emerald-300 border border-brand-700 font-bold hover:bg-brand-600 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Plus className="w-4 h-4" /> Save Availability Rule
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Rules List */}
          <div className="lg:col-span-7 space-y-4">
            <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <span className="font-bold text-white text-sm">Active Rules & Blocked Dates</span>
                <span className="text-slate-500 text-[11px]">{rules.length} Configured</span>
              </div>

              {rules.length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  No custom availability rules configured. Standard working hours (Mon–Sat 10:00 AM – 6:00 PM IST) apply.
                </div>
              ) : (
                <table className="w-full text-left">
                  <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="py-3 px-4">Date / Target</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Capacity</th>
                      <th className="py-3 px-4">Notes</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {rules.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-900/50">
                        <td className="py-3 px-4 font-bold text-white">
                          {r.specific_date || (r.day_of_week !== null ? `Day ${r.day_of_week}` : 'All')}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 border border-slate-700 text-slate-300">
                            {r.rule_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono">
                          {r.is_blocked ? (
                            <span className="text-rose-400 font-bold">Blocked (0)</span>
                          ) : (
                            <span className="text-emerald-400">{r.slot_capacity} per slot</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-slate-400 text-[11px]">
                          {r.notes || '—'}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleDeleteRule(r.id)}
                            className="p-1.5 text-rose-400 hover:text-white hover:bg-rose-950/50 rounded-lg cursor-pointer"
                            title="Delete Rule"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: MANAGED SERVICE ORDERS */}
      {activeTab === 'orders' && (
        <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden">
          {orders.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              No service orders currently requested across tenants.
            </div>
          ) : (
            <table className="w-full text-left">
              <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4">Service Type</th>
                  <th className="py-3 px-4">Quoted Fee</th>
                  <th className="py-3 px-4">Scope Summary</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {orders.map((o) => (
                  <tr key={o.id} className="hover:bg-slate-900/50">
                    <td className="py-3 px-4 text-slate-500 font-mono">{o.id.slice(0, 8)}</td>
                    <td className="py-3 px-4 font-bold text-white capitalize">{o.service_type.replace(/_/g, ' ')}</td>
                    <td className="py-3 px-4 text-rose-400 font-bold">₹{o.quoted_price_inr.toLocaleString()}</td>
                    <td className="py-3 px-4 text-slate-400 truncate max-w-xs">{o.scope_description}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          o.status === 'completed'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : o.status === 'in_progress'
                            ? 'bg-sky-950 text-sky-400 border border-sky-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}
                      >
                        {o.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ASSIGN CONSULTANT MODAL */}
      {assignModalItem && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md p-6 space-y-4 bg-slate-950 border border-slate-800 rounded-3xl text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base font-sans">Assign Growth Consultant</h3>
              <button onClick={() => setAssignModalItem(null)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAssignSubmit} className="space-y-4">
              <p className="text-slate-400 text-xs">
                Select an authorized growth consultant or platform specialist for <strong className="text-white">{assignModalItem.brand_name}</strong>.
              </p>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Advisor / Specialist *</label>
                <select
                  required
                  value={assignForm.consultantId}
                  onChange={(e) => {
                    const selId = e.target.value;
                    const matched = users.find((u) => u.id === selId);
                    setAssignForm({
                      consultantId: selId,
                      consultantName: matched?.full_name || matched?.email || 'Platform Specialist',
                    });
                  }}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs cursor-pointer"
                >
                  <option value="">Select Platform User</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name || u.email} ({u.role})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Display Name</label>
                <input
                  type="text"
                  required
                  value={assignForm.consultantName}
                  onChange={(e) => setAssignForm({ ...assignForm, consultantName: e.target.value })}
                  placeholder="Senior D2C Advisor"
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setAssignModalItem(null)}
                  className="px-3 py-1.5 rounded-xl border border-slate-700 text-slate-400 hover:text-white text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-forest text-emerald-300 border border-brand-700 font-bold hover:bg-brand-600 text-xs cursor-pointer"
                >
                  Confirm Assignment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONFIRM APPOINTMENT MODAL */}
      {confirmModalItem && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md p-6 space-y-4 bg-slate-950 border border-slate-800 rounded-3xl text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base font-sans">Confirm Appointment Slot</h3>
              <button onClick={() => setConfirmModalItem(null)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleConfirmSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Schedule (Date & Time) *</label>
                <input
                  type="datetime-local"
                  required
                  value={confirmForm.scheduledAt}
                  onChange={(e) => setConfirmForm({ ...confirmForm, scheduledAt: e.target.value })}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Meeting Link</label>
                <input
                  type="url"
                  value={confirmForm.meetingLink}
                  onChange={(e) => setConfirmForm({ ...confirmForm, meetingLink: e.target.value })}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Duration (Minutes)</label>
                <select
                  value={confirmForm.duration}
                  onChange={(e) => setConfirmForm({ ...confirmForm, duration: Number(e.target.value) })}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs cursor-pointer"
                >
                  <option value={30}>30 Minutes</option>
                  <option value={45}>45 Minutes</option>
                  <option value={60}>60 Minutes</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setConfirmModalItem(null)}
                  className="px-3 py-1.5 rounded-xl border border-slate-700 text-slate-400 hover:text-white text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-forest text-emerald-300 border border-brand-700 font-bold hover:bg-brand-600 text-xs cursor-pointer"
                >
                  Confirm Slot
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RESCHEDULE MODAL */}
      {rescheduleModalItem && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md p-6 space-y-4 bg-slate-950 border border-slate-800 rounded-3xl text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base font-sans">Reschedule Consultation</h3>
              <button onClick={() => setRescheduleModalItem(null)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRescheduleSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">New Date *</label>
                <input
                  type="date"
                  required
                  value={rescheduleForm.date}
                  onChange={(e) => setRescheduleForm({ ...rescheduleForm, date: e.target.value })}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">New Time Slot (IST) *</label>
                <select
                  value={rescheduleForm.slot}
                  onChange={(e) => setRescheduleForm({ ...rescheduleForm, slot: e.target.value })}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs cursor-pointer"
                >
                  <option value="10:00 AM – 10:30 AM IST">10:00 AM – 10:30 AM IST</option>
                  <option value="11:30 AM – 12:00 PM IST">11:30 AM – 12:00 PM IST</option>
                  <option value="02:00 PM – 02:30 PM IST">02:00 PM – 02:30 PM IST</option>
                  <option value="03:30 PM – 04:00 PM IST">03:30 PM – 04:00 PM IST</option>
                  <option value="05:00 PM – 05:30 PM IST">05:00 PM – 05:30 PM IST</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Reason for Rescheduling</label>
                <input
                  type="text"
                  value={rescheduleForm.reason}
                  onChange={(e) => setRescheduleForm({ ...rescheduleForm, reason: e.target.value })}
                  placeholder="E.g., Merchant requested afternoon window"
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setRescheduleModalItem(null)}
                  className="px-3 py-1.5 rounded-xl border border-slate-700 text-slate-400 hover:text-white text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-forest text-emerald-300 border border-brand-700 font-bold hover:bg-brand-600 text-xs cursor-pointer"
                >
                  Save Reschedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CANCEL MODAL */}
      {cancelModalItem && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md p-6 space-y-4 bg-slate-950 border border-slate-800 rounded-3xl text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-rose-400 text-base font-sans">Cancel Consultation Booking</h3>
              <button onClick={() => setCancelModalItem(null)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCancelSubmit} className="space-y-4">
              <p className="text-slate-400 text-xs">
                Provide a recorded cancellation rationale for <strong className="text-white">{cancelModalItem.brand_name}</strong> ({cancelModalItem.reference_code}).
              </p>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Cancellation Reason *</label>
                <textarea
                  required
                  rows={3}
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="E.g., Merchant duplicate booking or withdrew request..."
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setCancelModalItem(null)}
                  className="px-3 py-1.5 rounded-xl border border-slate-700 text-slate-400 hover:text-white text-xs cursor-pointer"
                >
                  Keep Booking
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-rose-600 text-white font-bold hover:bg-rose-700 text-xs cursor-pointer"
                >
                  Confirm Cancellation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
