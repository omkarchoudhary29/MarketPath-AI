import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import {
  X,
  Bell,
  CheckCheck,
  Package,
  Link2,
  Briefcase,
  TrendingUp,
  Building2,
  Users,
  CheckCircle2,
  AlertTriangle,
  Info,
  ExternalLink,
} from 'lucide-react';

interface NotificationItem {
  id: string;
  organization_id: string;
  domain: string;
  title: string;
  message: string;
  notification_type: string;
  severity: string;
  is_read: boolean;
  link?: string;
  created_at: string;
}

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onCountChange?: (count: number) => void;
}

const DOMAIN_TABS = [
  { id: 'all', label: 'All', icon: Bell },
  { id: 'products', label: 'Products', icon: Package },
  { id: 'channels', label: 'Channels', icon: Link2 },
  { id: 'business', label: 'Business', icon: Briefcase },
  { id: 'marketing', label: 'Marketing', icon: TrendingUp },
  { id: 'agency', label: 'Agency', icon: Building2 },
  { id: 'team', label: 'Team', icon: Users },
];

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  onCountChange,
}) => {
  const { activeOrg } = useAuth();
  const { addToast } = useApp();

  const [activeDomain, setActiveDomain] = useState<string>('all');
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      let url = `/api/v1/notifications?limit=50`;
      if (activeDomain !== 'all') url += `&domain=${encodeURIComponent(activeDomain)}`;
      if (unreadOnly) url += `&unread_only=true`;

      const resp = await fetch(url, { headers });
      if (resp.ok) {
        const data = await resp.json();
        setNotifications(data.items || []);
        setUnreadCount(data.unread_count || 0);
        if (onCountChange) onCountChange(data.unread_count || 0);
      }
    } catch (err) {
      console.warn('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, activeDomain, unreadOnly, activeOrg?.id]);

  const handleMarkRead = async (id: string) => {
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      const resp = await fetch(`/api/v1/notifications/${id}/read`, {
        method: 'PATCH',
        headers,
      });

      if (resp.ok) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
        );
        const nextCount = Math.max(0, unreadCount - 1);
        setUnreadCount(nextCount);
        if (onCountChange) onCountChange(nextCount);
      }
    } catch (err) {
      console.warn('Failed to mark read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      let url = `/api/v1/notifications/mark-all-read`;
      if (activeDomain !== 'all') url += `?domain=${encodeURIComponent(activeDomain)}`;

      const resp = await fetch(url, {
        method: 'POST',
        headers,
      });

      if (resp.ok) {
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
        setUnreadCount(0);
        if (onCountChange) onCountChange(0);
        addToast({
          type: 'success',
          title: 'Notifications Cleared',
          message: 'All notifications in current view marked as read.',
        });
      }
    } catch (err) {
      addToast({ type: 'error', title: 'Error', message: 'Could not mark all as read.' });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-slate-200">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-charcoal">Notification Centre</h2>
                {unreadCount > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-brand-600 text-white text-[10px] font-bold">
                    {unreadCount} new
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500">6 business domain updates & alerts</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-charcoal hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Domain Filter Pills */}
        <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {DOMAIN_TABS.map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeDomain === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveDomain(tab.id)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-brand-600 text-white shadow-2xs'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Subheader: Unread Toggle & Mark All */}
        <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between text-xs">
          <label className="flex items-center gap-2 cursor-pointer text-slate-600 font-medium">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
              className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 h-3.5 w-3.5"
            />
            <span>Unread only</span>
          </label>
          <button
            onClick={handleMarkAllRead}
            className="text-brand-600 hover:text-brand-700 font-semibold inline-flex items-center gap-1 cursor-pointer"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            <span>Mark all read</span>
          </button>
        </div>

        {/* List of Notifications */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400 space-y-2">
              <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Loading updates...</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400 space-y-2">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="font-medium text-slate-600">No notifications in this view</p>
              <p className="text-[11px] text-slate-400">You're all caught up on {activeDomain} updates!</p>
            </div>
          ) : (
            notifications.map((item) => (
              <div
                key={item.id}
                className={`p-3.5 rounded-2xl border transition-all text-xs space-y-1.5 ${
                  item.is_read
                    ? 'bg-white border-slate-200/80'
                    : 'bg-brand-50/40 border-brand-200 shadow-xs'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-mono">
                      {item.domain}
                    </span>
                    {!item.is_read && (
                      <span className="w-2 h-2 rounded-full bg-brand-600 inline-block" />
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <div className="font-bold text-charcoal text-xs">{item.title}</div>
                <div className="text-slate-600 text-[11px] leading-relaxed">{item.message}</div>

                <div className="pt-1 flex items-center justify-between text-[11px] border-t border-slate-100">
                  {item.link ? (
                    <Link
                      to={item.link}
                      onClick={onClose}
                      className="text-brand-600 hover:text-brand-700 font-semibold inline-flex items-center gap-1"
                    >
                      <span>View Details</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  ) : (
                    <span />
                  )}

                  {!item.is_read && (
                    <button
                      onClick={() => handleMarkRead(item.id)}
                      className="text-slate-400 hover:text-brand-600 text-[10px] font-medium cursor-pointer"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer info */}
        <div className="p-3 bg-slate-50 border-t border-slate-100 text-center text-[11px] text-slate-500">
          Showing real-time events across Products, Channels, Business, Marketing, Agency, and Team.
        </div>
      </div>
    </div>
  );
};

