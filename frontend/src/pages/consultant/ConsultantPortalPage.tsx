import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Calendar,
  FileText,
  ArrowRight,
  Lock,
  CheckCircle2,
  AlertCircle,
  Clock,
  User,
  Building2,
  Phone,
  Mail,
  Send,
  Eye,
  Sliders,
  Settings,
  Bell,
  HelpCircle,
  RefreshCw,
  Video,
  XCircle,
  CalendarCheck,
  Check,
  X,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { DemoBanner } from '../../components/common/DemoBanner';

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

interface StatsData {
  total_consultations: number;
  submitted_count: number;
  confirmed_count: number;
  completed_count: number;
  cancelled_count: number;
  status_breakdown: Record<string, number>;
}

export const ConsultantPortalPage: React.FC = () => {
  const { user, session } = useAuth();
  const { addToast } = useApp();
  const token = session?.access_token;

  const [activeTab, setActiveTab] = useState<'dashboard' | 'assigned' | 'calendar' | 'notes' | 'settings'>('dashboard');
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Modal States
  const [confirmModalItem, setConfirmModalItem] = useState<Consultation | null>(null);
  const [confirmForm, setConfirmForm] = useState({ scheduledAt: '', meetingLink: '', duration: 30 });

  const [reportModalItem, setReportModalItem] = useState<Consultation | null>(null);
  const [reportForm, setReportForm] = useState({
    summary: '',
    recommendations: '',
    actionItems: '',
    internalNotes: '',
  });

  const [rescheduleModalItem, setRescheduleModalItem] = useState<Consultation | null>(null);
  const [rescheduleForm, setRescheduleForm] = useState({ date: '', slot: '10:00 AM – 10:30 AM IST', reason: '' });

  const [cancelModalItem, setCancelModalItem] = useState<Consultation | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const fetchConsultations = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const [listRes, statsRes] = await Promise.all([
        apiClient<Consultation[]>('/api/v1/consultations/assigned', { token }),
        apiClient<StatsData>('/api/v1/consultations/stats', { token }).catch(() => null),
      ]);
      setConsultations(listRes || []);
      if (statsRes) setStats(statsRes);
    } catch (err: any) {
      console.error('Failed to load assigned consultations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConsultations();
  }, [token]);

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
        title: 'Appointment Confirmed',
        message: `Consultation with ${confirmModalItem.brand_name} confirmed.`,
      });
      setConfirmModalItem(null);
      fetchConsultations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Confirmation Failed',
        message: err.message || 'Could not confirm appointment.',
      });
    }
  };

  // Handle Report Filing
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportModalItem || !token) return;
    try {
      const recList = reportForm.recommendations
        .split('\n')
        .map((r) => r.trim())
        .filter(Boolean);
      const actList = reportForm.actionItems
        .split('\n')
        .map((a) => a.trim())
        .filter(Boolean);

      await apiClient(`/api/v1/consultations/${reportModalItem.id}/report`, {
        method: 'POST',
        token,
        body: JSON.stringify({
          report_summary: reportForm.summary,
          recommendations: recList,
          action_items: actList,
          internal_notes: reportForm.internalNotes || null,
        }),
      });
      addToast({
        type: 'success',
        title: 'Report Filed',
        message: `Diagnostic roadmap filed for ${reportModalItem.brand_name}.`,
      });
      setReportModalItem(null);
      fetchConsultations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Report Filing Failed',
        message: err.message || 'Could not file diagnostic report.',
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
        title: 'Appointment Rescheduled',
        message: `New slot recorded for ${rescheduleModalItem.brand_name}.`,
      });
      setRescheduleModalItem(null);
      fetchConsultations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Reschedule Failed',
        message: err.message || 'Could not reschedule appointment.',
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
        title: 'Appointment Cancelled',
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">Confirmed</span>;
      case 'assigned':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-300">Assigned</span>;
      case 'completed':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-purple-100 text-purple-800 border border-purple-300">Completed</span>;
      case 'rescheduled':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300">Rescheduled</span>;
      case 'cancelled':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-300">Cancelled</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-softbeige text-forest border border-bordergrey">{status}</span>;
    }
  };

  const assignedActiveCount = consultations.filter((c) => ['assigned', 'confirmed', 'rescheduled'].includes(c.status)).length;
  const completedCount = consultations.filter((c) => c.status === 'completed').length;
  const reportsCount = consultations.filter((c) => Boolean(c.report_summary)).length;

  return (
    <div className="min-h-screen bg-warmwhite flex flex-col justify-between">
      <DemoBanner />
      {/* Top Header */}
      <header className="h-16 bg-white border-b border-bordergrey px-6 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-forest bg-gradient-to-tr from-[#075443] via-[#08765B] to-[#15966F] border border-[#15966F]/40 text-white font-extrabold flex items-center justify-center text-sm shadow-xs">
              MP
            </div>
            <span className="font-extrabold text-charcoal tracking-tight">MarketPath AI</span>
          </Link>
          <span className="text-bordergrey">|</span>
          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-softbeige text-forest border border-bordergrey">
            Consultant Advisory Workspace
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <button
            onClick={fetchConsultations}
            disabled={isLoading}
            className="p-1.5 rounded-lg border border-bordergrey text-charcoal-muted hover:text-charcoal hover:bg-slate-50 transition-colors"
            title="Refresh Consultations"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          {user ? (
            <span className="text-charcoal-muted">
              Signed in as <strong className="text-charcoal">{user.email}</strong>
            </span>
          ) : (
            <Link
              to="/login"
              className="px-3.5 py-1.5 rounded-xl bg-brand-600 text-white font-bold hover:bg-forest transition-colors shadow-xs"
            >
              Sign In
            </Link>
          )}
        </div>
      </header>

      {/* Main Workspace */}
      <main className="max-w-6xl mx-auto px-4 py-8 flex-1 w-full space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-bordergrey pb-3">
          <div className="flex items-center gap-2">
            {[
              { id: 'dashboard', label: 'Consultant Dashboard', icon: ShieldCheck },
              { id: 'assigned', label: `Assigned Consultations (${assignedActiveCount})`, icon: Calendar },
              { id: 'calendar', label: 'Advisory Calendar', icon: Clock },
              { id: 'notes', label: `Diagnostic Reports (${reportsCount})`, icon: FileText },
              { id: 'settings', label: 'Credentials & Security', icon: Settings },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    activeTab === tab.id
                      ? 'bg-softbeige text-forest border border-bordergrey shadow-xs'
                      : 'text-charcoal-muted hover:text-charcoal hover:bg-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          <Link to="/free-consultation">
            <Button size="sm" variant="outline">
              New Intake Slot +
            </Button>
          </Link>
        </div>

        {/* TAB 1: DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <Card className="p-8 space-y-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-softbeige border border-bordergrey text-forest flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h1 className="text-2xl font-extrabold text-charcoal tracking-tight">
                    Consultant Advisory Overview
                  </h1>
                  <p className="text-xs sm:text-sm text-charcoal-muted">
                    Restricted advisory environment for verified MarketPath category specialists and growth consultants.
                  </p>
                </div>
              </div>

              {/* Server-Provisioned Notice */}
              <div className="p-4 rounded-2xl bg-softorange-50 border border-softorange-200 text-xs text-softorange-800 space-y-1.5">
                <div className="font-bold flex items-center gap-1.5 text-softorange-900">
                  <Lock className="w-4 h-4" /> Server-Provisioned Accounts Only
                </div>
                <p className="leading-relaxed">
                  Consultant workspaces are authorized and provisioned server-side by MarketPath platform administrators.
                  Public self-registration for consultant roles is permanently disabled to maintain merchant diagnostic confidentiality.
                </p>
              </div>

              {/* KPI Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="p-5 rounded-2xl bg-warmwhite border border-bordergrey space-y-2">
                  <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-700 flex items-center justify-center font-bold text-xs">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <h3 className="text-xs font-bold text-charcoal">Active Assigned Sessions</h3>
                  <div className="text-2xl font-extrabold text-charcoal">{assignedActiveCount} Active</div>
                  <p className="text-[11px] text-charcoal-muted leading-relaxed">
                    Live merchant consultations assigned directly to your advisor account.
                  </p>
                </div>

                <div className="p-5 rounded-2xl bg-warmwhite border border-bordergrey space-y-2">
                  <div className="w-8 h-8 rounded-lg bg-softbeige text-forest flex items-center justify-center font-bold text-xs">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <h3 className="text-xs font-bold text-charcoal">Completed Sessions</h3>
                  <div className="text-2xl font-extrabold text-charcoal">{completedCount} Completed</div>
                  <p className="text-[11px] text-charcoal-muted leading-relaxed">
                    Fulfilled growth audits with full recommendations filed.
                  </p>
                </div>

                <div className="p-5 rounded-2xl bg-warmwhite border border-bordergrey space-y-2">
                  <div className="w-8 h-8 rounded-lg bg-softorange-50 text-softorange-700 flex items-center justify-center font-bold text-xs">
                    <FileText className="w-4 h-4" />
                  </div>
                  <h3 className="text-xs font-bold text-charcoal">Diagnostic Roadmaps</h3>
                  <div className="text-2xl font-extrabold text-charcoal">{reportsCount} Filed</div>
                  <p className="text-[11px] text-charcoal-muted leading-relaxed">
                    Structured recommendations with internal notes redacted for clients.
                  </p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* TAB 2: ASSIGNED CONSULTATIONS */}
        {activeTab === 'assigned' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-charcoal">Your Assigned Consultations</h2>
                <p className="text-xs text-charcoal-muted">Review merchant briefs, confirm schedule, or file diagnostic roadmaps</p>
              </div>
              <Badge variant="brand" size="sm">
                Isolated Tenant Scope
              </Badge>
            </div>

            {consultations.length === 0 ? (
              <Card className="p-12 text-center space-y-4">
                <Calendar className="w-12 h-12 text-forest mx-auto opacity-40" />
                <h3 className="text-base font-bold text-charcoal">No Assigned Consultations Currently</h3>
                <p className="text-xs text-charcoal-muted max-w-md mx-auto leading-relaxed">
                  When platform administrators assign inbound growth inquiries to your advisor profile, they will appear here with requested dates and challenge briefs.
                </p>
              </Card>
            ) : (
              <div className="space-y-4">
                {consultations.map((item) => (
                  <Card key={item.id} className="p-6 space-y-4 border-bordergrey hover:shadow-sm transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-bordergrey pb-3">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs font-extrabold px-2.5 py-1 rounded-lg bg-softbeige text-forest border border-bordergrey">
                          {item.reference_code}
                        </span>
                        <div>
                          <h3 className="text-base font-bold text-charcoal">{item.brand_name}</h3>
                          <span className="text-xs text-charcoal-muted">Category: {item.category} • Stage: {item.business_stage}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(item.status)}
                      </div>
                    </div>

                    {/* Details Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div>
                        <span className="text-charcoal-muted block">Contact Person:</span>
                        <span className="font-semibold text-charcoal">{item.full_name}</span>
                        <div className="text-[11px] text-charcoal-muted">{item.email}</div>
                        {item.phone && <div className="text-[11px] text-charcoal-muted">{item.phone}</div>}
                      </div>

                      <div>
                        <span className="text-charcoal-muted block">Requested Slot:</span>
                        <span className="font-semibold text-charcoal">{item.preferred_date || 'Flexible'}</span>
                        <div className="text-[11px] text-forest font-medium">{item.preferred_time_slot || 'Standard 30-min window'}</div>
                      </div>

                      <div>
                        <span className="text-charcoal-muted block">Monthly Scale:</span>
                        <span className="font-semibold text-charcoal">{item.monthly_revenue || 'Undisclosed'}</span>
                      </div>

                      <div>
                        <span className="text-charcoal-muted block">Meeting Link:</span>
                        {item.meeting_link ? (
                          <a
                            href={item.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-[11px] text-brand-600 hover:underline flex items-center gap-1"
                          >
                            <Video className="w-3.5 h-3.5" /> Join Room
                          </a>
                        ) : (
                          <span className="text-slate-400">Not set yet</span>
                        )}
                      </div>
                    </div>

                    {/* Challenges Brief */}
                    {item.challenges && (
                      <div className="p-3.5 rounded-xl bg-warmwhite border border-bordergrey text-xs space-y-1">
                        <span className="font-bold text-charcoal flex items-center gap-1.5">
                          Merchant Challenges & Objectives:
                        </span>
                        <p className="text-charcoal-muted leading-relaxed italic">
                          "{item.challenges}"
                        </p>
                      </div>
                    )}

                    {/* Action Bar */}
                    <div className="pt-2 flex flex-wrap items-center justify-end gap-2 border-t border-bordergrey">
                      {item.status !== 'confirmed' && item.status !== 'completed' && item.status !== 'cancelled' && (
                        <Button
                          size="sm"
                          onClick={() => {
                            setConfirmModalItem(item);
                            setConfirmForm({
                              scheduledAt: item.preferred_date ? `${item.preferred_date}T10:00` : '',
                              meetingLink: `https://meet.marketpath.ai/consult-${item.reference_code.toLowerCase()}`,
                              duration: 30,
                            });
                          }}
                        >
                          <Check className="w-3.5 h-3.5 mr-1" /> Confirm Slot
                        </Button>
                      )}

                      {item.status !== 'completed' && item.status !== 'cancelled' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setRescheduleModalItem(item);
                            setRescheduleForm({
                              date: item.preferred_date || '',
                              slot: item.preferred_time_slot || '10:00 AM – 10:30 AM IST',
                              reason: '',
                            });
                          }}
                        >
                          <Clock className="w-3.5 h-3.5 mr-1" /> Reschedule
                        </Button>
                      )}

                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => {
                          setReportModalItem(item);
                          setReportForm({
                            summary: item.report_summary || '',
                            recommendations: (item.recommendations || []).join('\n'),
                            actionItems: (item.action_items || []).join('\n'),
                            internalNotes: item.internal_notes || '',
                          });
                        }}
                      >
                        <FileText className="w-3.5 h-3.5 mr-1" /> {item.report_summary ? 'Update Report' : 'File Diagnostic Report'}
                      </Button>

                      {item.status !== 'cancelled' && item.status !== 'completed' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-rose-600 hover:bg-rose-50"
                          onClick={() => {
                            setCancelModalItem(item);
                            setCancelReason('');
                          }}
                        >
                          <XCircle className="w-3.5 h-3.5 mr-1" /> Cancel
                        </Button>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: CALENDAR */}
        {activeTab === 'calendar' && (
          <Card className="p-8 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-bordergrey">
              <div>
                <h3 className="text-base font-bold text-charcoal">Advisory Appointment Schedule</h3>
                <p className="text-xs text-charcoal-muted">Synchronized consultation slots in Asia/Kolkata timezone</p>
              </div>
              <Badge variant="brand" size="sm">
                Live Calendar Engine
              </Badge>
            </div>

            {consultations.filter((c) => ['confirmed', 'assigned'].includes(c.status)).length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <Clock className="w-12 h-12 text-forest mx-auto opacity-40" />
                <div className="font-bold text-charcoal text-sm">No Upcoming Advisory Sessions Scheduled</div>
                <p className="text-xs text-charcoal-muted max-w-sm mx-auto">
                  Confirmed consultations will automatically display here with date, time, and active video conference links.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {consultations
                  .filter((c) => ['confirmed', 'assigned'].includes(c.status))
                  .map((c) => (
                    <div key={c.id} className="p-4 rounded-2xl bg-warmwhite border border-bordergrey flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-forest text-white font-bold text-xs flex items-center justify-center">
                          <CalendarCheck className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="font-bold text-charcoal text-xs">{c.brand_name} ({c.reference_code})</div>
                          <div className="text-[11px] text-charcoal-muted">
                            {c.preferred_date || 'Date TBD'} • {c.preferred_time_slot || 'Standard Slot'} (IST)
                          </div>
                        </div>
                      </div>
                      <div>
                        {c.meeting_link && (
                          <a
                            href={c.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-forest text-white font-bold text-xs hover:bg-brand-600 transition-colors"
                          >
                            <Video className="w-3.5 h-3.5" /> Launch Video
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </Card>
        )}

        {/* TAB 4: DIAGNOSTIC REPORTS */}
        {activeTab === 'notes' && (
          <Card className="p-8 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-bordergrey">
              <div>
                <h3 className="text-base font-bold text-charcoal">Filed Diagnostic Reports & Roadmaps</h3>
                <p className="text-xs text-charcoal-muted">Verified client growth roadmaps with internal notes redaction guard active</p>
              </div>
              <Badge variant="brand" size="sm">
                Redaction Guard Active
              </Badge>
            </div>

            {consultations.filter((c) => Boolean(c.report_summary)).length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <FileText className="w-12 h-12 text-forest mx-auto opacity-40" />
                <div className="font-bold text-charcoal text-sm">No Diagnostic Reports Filed Yet</div>
                <p className="text-xs text-charcoal-muted max-w-sm mx-auto">
                  When you complete a merchant consultation, file your diagnosis from the Assigned Consultations tab.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {consultations
                  .filter((c) => Boolean(c.report_summary))
                  .map((rep) => (
                    <div key={rep.id} className="p-5 rounded-2xl bg-white border border-bordergrey space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-bold text-sm text-charcoal">{rep.brand_name}</h4>
                          <span className="font-mono text-xs text-forest">Ref: {rep.reference_code}</span>
                        </div>
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-purple-50 text-purple-800 border border-purple-200">
                          Report Filed
                        </span>
                      </div>

                      <div className="text-xs text-charcoal space-y-1">
                        <strong className="text-charcoal block">Executive Diagnostic Summary:</strong>
                        <p className="text-charcoal-muted leading-relaxed whitespace-pre-wrap">{rep.report_summary}</p>
                      </div>

                      {rep.recommendations && rep.recommendations.length > 0 && (
                        <div className="text-xs space-y-1">
                          <strong className="text-charcoal block">Key Recommendations:</strong>
                          <ul className="list-disc pl-5 text-charcoal-muted space-y-0.5">
                            {rep.recommendations.map((rec, i) => (
                              <li key={i}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {rep.action_items && rep.action_items.length > 0 && (
                        <div className="text-xs space-y-1">
                          <strong className="text-charcoal block">Action Plan:</strong>
                          <ul className="list-decimal pl-5 text-charcoal-muted space-y-0.5">
                            {rep.action_items.map((act, i) => (
                              <li key={i}>{act}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {rep.internal_notes && (
                        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
                          <div className="font-bold flex items-center gap-1.5 text-amber-950">
                            <Lock className="w-3.5 h-3.5" /> Confidential Internal Notes (Redacted from Client Endpoints)
                          </div>
                          <p className="whitespace-pre-wrap italic">{rep.internal_notes}</p>
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}
          </Card>
        )}

        {/* TAB 5: CREDENTIALS & SECURITY */}
        {activeTab === 'settings' && (
          <Card className="p-8 space-y-6">
            <h3 className="text-base font-bold text-charcoal">Advisor Credentials & RBAC Role</h3>
            <div className="space-y-3 text-xs text-charcoal-muted">
              <div className="p-4 bg-warmwhite rounded-2xl border border-bordergrey">
                <span className="font-bold text-charcoal">Account Email:</span> {user?.email || 'advisor@marketpath.ai'}
              </div>
              <div className="p-4 bg-warmwhite rounded-2xl border border-bordergrey">
                <span className="font-bold text-charcoal">Assigned Role:</span> Platform Authorized Growth Specialist
              </div>
              <div className="p-4 bg-warmwhite rounded-2xl border border-bordergrey">
                <span className="font-bold text-charcoal">Tenant Privacy Standard:</span> Zero founder personal phone/email exposure outside verified assignment.
              </div>
            </div>
          </Card>
        )}

        {/* Footer Actions */}
        <div className="pt-4 flex items-center justify-between">
          <Link
            to="/app/dashboard"
            className="inline-flex items-center gap-2 text-xs font-bold text-charcoal hover:text-forest"
          >
            Return to Seller Dashboard
          </Link>
          <Link to="/free-consultation">
            <Button size="sm">
              Schedule Merchant Consultation <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Button>
          </Link>
        </div>
      </main>

      {/* CONFIRM APPOINTMENT MODAL */}
      {confirmModalItem && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md p-6 space-y-4 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-bordergrey pb-3">
              <h3 className="font-bold text-charcoal text-base">Confirm Consultation Slot</h3>
              <button onClick={() => setConfirmModalItem(null)} className="text-slate-400 hover:text-charcoal cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleConfirmSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-charcoal mb-1">Appointment Schedule (Date & Time)</label>
                <input
                  type="datetime-local"
                  required
                  value={confirmForm.scheduledAt}
                  onChange={(e) => setConfirmForm({ ...confirmForm, scheduledAt: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal"
                />
              </div>

              <div>
                <label className="block font-bold text-charcoal mb-1">Meeting Room URL</label>
                <input
                  type="url"
                  value={confirmForm.meetingLink}
                  onChange={(e) => setConfirmForm({ ...confirmForm, meetingLink: e.target.value })}
                  placeholder="https://meet.marketpath.ai/..."
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal"
                />
              </div>

              <div>
                <label className="block font-bold text-charcoal mb-1">Duration (Minutes)</label>
                <select
                  value={confirmForm.duration}
                  onChange={(e) => setConfirmForm({ ...confirmForm, duration: Number(e.target.value) })}
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal cursor-pointer"
                >
                  <option value={30}>30 Minutes</option>
                  <option value={45}>45 Minutes</option>
                  <option value={60}>60 Minutes</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setConfirmModalItem(null)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Confirm & Send Calendar Invite
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* FILE DIAGNOSTIC REPORT MODAL */}
      {reportModalItem && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-lg p-6 space-y-4 bg-white shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-bordergrey pb-3">
              <div>
                <h3 className="font-bold text-charcoal text-base">File Diagnostic Growth Roadmap</h3>
                <span className="text-xs text-charcoal-muted">For {reportModalItem.brand_name} ({reportModalItem.reference_code})</span>
              </div>
              <button onClick={() => setReportModalItem(null)} className="text-slate-400 hover:text-charcoal cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleReportSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-charcoal mb-1">Executive Diagnostic Summary *</label>
                <textarea
                  required
                  rows={3}
                  value={reportForm.summary}
                  onChange={(e) => setReportForm({ ...reportForm, summary: e.target.value })}
                  placeholder="Summarize product packaging readiness, channel suitability, and primary expansion thesis..."
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal"
                />
              </div>

              <div>
                <label className="block font-bold text-charcoal mb-1">Strategic Recommendations (One per line)</label>
                <textarea
                  rows={3}
                  value={reportForm.recommendations}
                  onChange={(e) => setReportForm({ ...reportForm, recommendations: e.target.value })}
                  placeholder="E.g.,&#10;Shift primary packaging to 400g pouch to reduce Zepto shipping slab&#10;Enable Amazon Brand Registry and configure A+ Content"
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal"
                />
              </div>

              <div>
                <label className="block font-bold text-charcoal mb-1">Action Items & Deliverables (One per line)</label>
                <textarea
                  rows={2}
                  value={reportForm.actionItems}
                  onChange={(e) => setReportForm({ ...reportForm, actionItems: e.target.value })}
                  placeholder="E.g.,&#10;Merchant to provide master barcode list&#10;Advisor to share agency connection shortlist"
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal"
                />
              </div>

              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 space-y-1.5">
                <label className="block font-bold text-amber-950">
                  Confidential Internal Notes (Redacted from Client)
                </label>
                <textarea
                  rows={2}
                  value={reportForm.internalNotes}
                  onChange={(e) => setReportForm({ ...reportForm, internalNotes: e.target.value })}
                  placeholder="Operator observations, margin risks, or proprietary vendor recommendations..."
                  className="w-full p-2 rounded-lg border border-amber-300 text-xs bg-white text-charcoal"
                />
                <span className="text-[10px] text-amber-800 block">
                  ★ These notes are strictly redacted from client-facing endpoints.
                </span>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setReportModalItem(null)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Save & Publish Roadmap
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* RESCHEDULE MODAL */}
      {rescheduleModalItem && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md p-6 space-y-4 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-bordergrey pb-3">
              <h3 className="font-bold text-charcoal text-base">Reschedule Appointment</h3>
              <button onClick={() => setRescheduleModalItem(null)} className="text-slate-400 hover:text-charcoal cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRescheduleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-charcoal mb-1">New Date *</label>
                <input
                  type="date"
                  required
                  value={rescheduleForm.date}
                  onChange={(e) => setRescheduleForm({ ...rescheduleForm, date: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal cursor-pointer"
                />
              </div>

              <div>
                <label className="block font-bold text-charcoal mb-1">New Time Slot (IST) *</label>
                <select
                  value={rescheduleForm.slot}
                  onChange={(e) => setRescheduleForm({ ...rescheduleForm, slot: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal cursor-pointer"
                >
                  <option value="10:00 AM – 10:30 AM IST">10:00 AM – 10:30 AM IST</option>
                  <option value="11:30 AM – 12:00 PM IST">11:30 AM – 12:00 PM IST</option>
                  <option value="02:00 PM – 02:30 PM IST">02:00 PM – 02:30 PM IST</option>
                  <option value="03:30 PM – 04:00 PM IST">03:30 PM – 04:00 PM IST</option>
                  <option value="05:00 PM – 05:30 PM IST">05:00 PM – 05:30 PM IST</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-charcoal mb-1">Reason for Rescheduling</label>
                <input
                  type="text"
                  value={rescheduleForm.reason}
                  onChange={(e) => setRescheduleForm({ ...rescheduleForm, reason: e.target.value })}
                  placeholder="E.g., Merchant requested afternoon window due to catalogue audit"
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setRescheduleModalItem(null)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Save New Schedule
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* CANCEL MODAL */}
      {cancelModalItem && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md p-6 space-y-4 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-bordergrey pb-3">
              <h3 className="font-bold text-charcoal text-base text-rose-700">Cancel Consultation</h3>
              <button onClick={() => setCancelModalItem(null)} className="text-slate-400 hover:text-charcoal cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCancelSubmit} className="space-y-4 text-xs">
              <p className="text-charcoal-muted">
                Please provide a cancellation reason for <strong className="text-charcoal">{cancelModalItem.brand_name}</strong>.
              </p>

              <div>
                <label className="block font-bold text-charcoal mb-1">Cancellation Reason *</label>
                <textarea
                  required
                  rows={3}
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="E.g., Duplicate booking or merchant withdrew request..."
                  className="w-full p-2.5 rounded-xl border border-bordergrey text-xs bg-white text-charcoal"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setCancelModalItem(null)}>
                  Keep Booking
                </Button>
                <Button type="submit" size="sm" className="bg-rose-600 hover:bg-rose-700 text-white">
                  Confirm Cancellation
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Page Footer */}
      <footer className="h-14 bg-white border-t border-bordergrey px-6 flex items-center justify-between text-xs text-charcoal-muted">
        <span>© {new Date().getFullYear()} MarketPath AI. Consultant Advisory Network.</span>
        <span>Zero PII Sharing Across Roles • Verified Security</span>
      </footer>
    </div>
  );
};
