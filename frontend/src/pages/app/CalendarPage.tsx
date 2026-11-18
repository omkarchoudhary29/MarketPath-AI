import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Plus,
  Download,
  Filter,
  Package,
  TrendingUp,
  CreditCard,
  Building2,
  Link2,
  CheckSquare,
  Clock,
  CheckCircle2,
  CalendarDays,
  List,
  Sparkles,
} from 'lucide-react';
import { Modal } from '../../components/ui/Modal';

interface CalendarEvent {
  id: string;
  event_type: string;
  title: string;
  description?: string;
  start_time: string;
  end_time?: string;
  is_all_day: boolean;
  color?: string;
  status: string;
}

const EVENT_TYPE_CONFIG: Record<
  string,
  { label: string; color: string; badgeClass: string; icon: any }
> = {
  product_launch: {
    label: 'Product Launch',
    color: '#9333EA',
    badgeClass: 'bg-purple-50 text-purple-700 border-purple-200',
    icon: Package,
  },
  campaign: {
    label: 'Ad Campaign',
    color: '#4F46E5',
    badgeClass: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    icon: TrendingUp,
  },
  subscription_renewal: {
    label: 'Subscription Renewal',
    color: '#059669',
    badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: CreditCard,
  },
  agency_meeting: {
    label: 'Agency Milestone',
    color: '#D97706',
    badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
    icon: Building2,
  },
  channel_sync: {
    label: 'Channel Sync',
    color: '#0D9488',
    badgeClass: 'bg-teal-50 text-teal-700 border-teal-200',
    icon: Link2,
  },
  task: {
    label: 'Operational Task',
    color: '#E11D48',
    badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
    icon: CheckSquare,
  },
};

export const CalendarPage: React.FC = () => {
  const { session, activeOrg } = useAuth();
  const { addToast } = useApp();

  const [viewMode, setViewMode] = useState<'month' | 'week' | 'day' | 'agenda'>('month');
  const [selectedEventType, setSelectedEventType] = useState<string>('all');
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  // New Event Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    event_type: 'product_launch',
    description: '',
    start_date: new Date().toISOString().split('T')[0],
    start_time: '10:00',
    is_all_day: false,
  });

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      let url = '/api/v1/calendar/events';
      if (selectedEventType !== 'all') url += `?event_type=${encodeURIComponent(selectedEventType)}`;

      const resp = await fetch(url, { headers });
      if (resp.ok) {
        const data = await resp.json();
        setEvents(data.items || []);
      }
    } catch (err) {
      console.warn('Failed to fetch calendar events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [selectedEventType, activeOrg?.id]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      const startDateTime = new Date(`${newEvent.start_date}T${newEvent.start_time}:00Z`);

      const resp = await fetch('/api/v1/calendar/events', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          title: newEvent.title.trim(),
          event_type: newEvent.event_type,
          description: newEvent.description.trim() || undefined,
          start_time: startDateTime.toISOString(),
          is_all_day: newEvent.is_all_day,
        }),
      });

      if (!resp.ok) throw new Error('Failed to create calendar event');

      addToast({
        type: 'success',
        title: 'Event Scheduled',
        message: `${newEvent.title} added to business calendar.`,
      });
      setShowAddModal(false);
      fetchEvents();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Creation Failed',
        message: err.message || 'Could not schedule event.',
      });
    }
  };

  const handleExportICS = async () => {
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      const resp = await fetch('/api/v1/calendar/export.ics', { headers });
      if (!resp.ok) throw new Error('Export failed');

      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `marketpath-calendar-${activeOrg?.slug || 'business'}.ics`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      addToast({
        type: 'success',
        title: 'Calendar Exported',
        message: '.ics calendar file downloaded. Sync to Google Calendar, Apple Calendar, or Outlook.',
      });
    } catch (err) {
      addToast({ type: 'error', title: 'Export Failed' });
    }
  };

  const handleSyncExternal = async (provider: 'google' | 'outlook') => {
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      const resp = await fetch(`/api/v1/calendar/connect/${provider}`, {
        method: 'POST',
        headers,
      });

      if (!resp.ok) throw new Error('External calendar sync failed');
      const data = await resp.json();

      addToast({
        type: 'success',
        title: `${provider === 'google' ? 'Google' : 'Outlook'} Calendar Synced`,
        message: data.message || `Synchronized ${data.events_synced} business events.`,
      });
      fetchEvents();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Sync Error',
        message: err.message || 'Could not synchronize with external calendar.',
      });
    }
  };

  // 30 days grid for Month view
  const days = Array.from({ length: 30 }, (_, i) => i + 1);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600">
            Unified Business Operations
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-0.5">
            Commercial Business Calendar
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Unifies product catalogue drops, marketing campaigns, subscription renewals, agency milestones, and channel syncs.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleExportICS}
            className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs inline-flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>.ics</span>
          </button>
          <button
            onClick={() => handleSyncExternal('google')}
            className="px-3 py-2 rounded-xl border border-bordergrey hover:bg-softbeige text-forest font-semibold text-xs inline-flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <CalendarIcon className="w-3.5 h-3.5 text-forest" />
            <span>Google Sync</span>
          </button>
          <button
            onClick={() => handleSyncExternal('outlook')}
            className="px-3 py-2 rounded-xl border border-bordergrey hover:bg-softbeige text-forest font-semibold text-xs inline-flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <CalendarIcon className="w-3.5 h-3.5 text-forest" />
            <span>Outlook Sync</span>
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 rounded-xl bg-forest hover:bg-deepforest text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Event</span>
          </button>
        </div>
      </div>

      {/* Control Bar: View Switcher & Domain Type Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        {/* Type Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1">
          <button
            onClick={() => setSelectedEventType('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
              selectedEventType === 'all'
                ? 'bg-charcoal text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            All Events ({events.length})
          </button>
          {Object.entries(EVENT_TYPE_CONFIG).map(([key, config]) => {
            const Icon = config.icon;
            const isSelected = selectedEventType === key;
            return (
              <button
                key={key}
                onClick={() => setSelectedEventType(key)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-brand-600 text-white shadow-2xs'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{config.label}</span>
              </button>
            );
          })}
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl self-start lg:self-auto">
          {(['month', 'week', 'day', 'agenda'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                viewMode === mode ? 'bg-white text-charcoal shadow-xs' : 'text-slate-600 hover:text-charcoal'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* AGENDA / LIST VIEW */}
      {viewMode === 'agenda' ? (
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-2xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-charcoal">Upcoming Business Events</h3>
            <span className="text-xs text-slate-400 font-mono">{events.length} Scheduled</span>
          </div>

          <div className="divide-y divide-slate-100">
            {events.map((ev) => {
              const config = EVENT_TYPE_CONFIG[ev.event_type] || EVENT_TYPE_CONFIG.task;
              const Icon = config.icon;
              return (
                <div
                  key={ev.id}
                  onClick={() => setSelectedEvent(ev)}
                  className="p-4 hover:bg-slate-50/60 transition-colors flex items-center justify-between gap-4 cursor-pointer text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-10 h-10 rounded-2xl flex items-center justify-center shrink-0"
                      style={{ backgroundColor: `${config.color}15`, color: config.color }}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-charcoal truncate">{ev.title}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {ev.description || 'No description provided.'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${config.badgeClass}`}>
                      {config.label}
                    </span>
                    <span className="text-slate-400 text-[11px] font-mono">
                      {new Date(ev.start_time).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* MONTH / WEEK / DAY CALENDAR GRID */
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-2xs overflow-hidden">
          <div className="grid grid-cols-7 text-center py-3 bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <div>Mon</div>
            <div>Tue</div>
            <div>Wed</div>
            <div>Thu</div>
            <div>Fri</div>
            <div>Sat</div>
            <div>Sun</div>
          </div>

          <div className="grid grid-cols-7 auto-rows-[120px] divide-x divide-y divide-slate-100">
            {days.map((day) => {
              // Map events to day numbers
              const dayEvents = events.filter((e) => {
                const evDate = new Date(e.start_time).getDate();
                return evDate === day;
              });

              return (
                <div
                  key={day}
                  className="p-2 flex flex-col justify-between hover:bg-slate-50/40 transition-colors"
                >
                  <span className="text-xs font-bold text-slate-400 self-end">{day}</span>
                  <div className="space-y-1 overflow-y-auto no-scrollbar max-h-20">
                    {dayEvents.map((ev) => {
                      const config = EVENT_TYPE_CONFIG[ev.event_type] || EVENT_TYPE_CONFIG.task;
                      return (
                        <button
                          key={ev.id}
                          onClick={() => setSelectedEvent(ev)}
                          className="w-full text-left p-1.5 rounded-lg text-[10px] font-semibold truncate border cursor-pointer block"
                          style={{
                            backgroundColor: `${config.color}15`,
                            borderColor: `${config.color}40`,
                            color: config.color,
                          }}
                        >
                          {ev.title}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Event Details Inspection Modal */}
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onClose={() => setSelectedEvent(null)}
          title={selectedEvent.title}
          subtitle={`Scheduled: ${new Date(selectedEvent.start_time).toLocaleString()}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div>
                <span className="text-slate-500">Event Domain: </span>
                <span className="font-bold text-charcoal uppercase">
                  {EVENT_TYPE_CONFIG[selectedEvent.event_type]?.label || selectedEvent.event_type}
                </span>
              </div>
              <div>
                <span className="text-slate-500">Description: </span>
                <span className="text-slate-700 font-medium">{selectedEvent.description || 'None'}</span>
              </div>
              <div>
                <span className="text-slate-500">Status: </span>
                <span className="text-emerald-700 font-bold uppercase">{selectedEvent.status}</span>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Add Event Modal */}
      {showAddModal && (
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Schedule Business Event"
          subtitle="Add commercial milestone, campaign flight, or renewal"
        >
          <form onSubmit={handleCreateEvent} className="space-y-4 text-xs">
            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Event Title *</label>
              <input
                type="text"
                required
                placeholder="e.g. Diwali Collection Catalogue Drop"
                value={newEvent.title}
                onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Commercial Event Type *</label>
              <select
                value={newEvent.event_type}
                onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white"
              >
                {Object.entries(EVENT_TYPE_CONFIG).map(([k, cfg]) => (
                  <option key={k} value={k}>
                    {cfg.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Date *</label>
                <input
                  type="date"
                  required
                  value={newEvent.start_date}
                  onChange={(e) => setNewEvent({ ...newEvent, start_date: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Time</label>
                <input
                  type="time"
                  value={newEvent.start_time}
                  onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Description / Notes</label>
              <textarea
                rows={3}
                placeholder="Key objectives, channel links, budget notes..."
                value={newEvent.description}
                onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold"
              >
                Save Event
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
