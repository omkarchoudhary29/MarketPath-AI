import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { NotificationDrawer } from './NotificationDrawer';
import { siteConfig } from '../../config/site';
import {
  Bell,
  Plus,
  ChevronDown,
  Building2,
  LogOut,
  Shield,
  HelpCircle,
  Menu,
  Check,
} from 'lucide-react';

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { brand, addToast } = useApp();
  const { user, activeOrg, organizations, switchOrganization, role, logout } = useAuth();
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showOrgMenu, setShowOrgMenu] = useState(false);
  const [showNotificationDrawer, setShowNotificationDrawer] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(3);

  useEffect(() => {
    const fetchUnread = async () => {
      try {
        const token = localStorage.getItem('marketpath_auth_token');
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

        const resp = await fetch('/api/v1/notifications/unread-count', { headers });
        if (resp.ok) {
          const data = await resp.json();
          setUnreadCount(data.unread_count || 0);
        }
      } catch (err) {
        // fallback gracefully
      }
    };
    fetchUnread();
  }, [activeOrg?.id]);

  const handleLogout = async () => {
    setShowProfileMenu(false);
    await logout();
    addToast({ type: 'info', title: 'Signed Out', message: 'You have been signed out of your workspace.' });
    navigate('/login');
  };

  const displayName = user?.full_name || 'Founder';
  const displayEmail = user?.email || 'founder@brand.in';
  const orgName = activeOrg?.name || brand.name;
  const currentRole = role || 'owner';

  return (
    <header className="h-16 bg-white border-b border-bordergrey px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-2 text-charcoal-muted hover:text-charcoal rounded-xl hover:bg-softbeige/50 lg:hidden cursor-pointer"
            title="Toggle Menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        {/* Brand / Org Selector */}
        <div className="relative">
          <button
            onClick={() => setShowOrgMenu(!showOrgMenu)}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl border border-bordergrey hover:border-brand-300 hover:bg-softbeige/30 transition-all text-left cursor-pointer"
          >
            <div className="w-6 h-6 rounded-lg bg-forest text-white font-extrabold flex items-center justify-center text-xs">
              {orgName.substring(0, 1)}
            </div>
            <div>
              <div className="text-xs font-bold text-charcoal leading-tight flex items-center gap-1">
                {orgName}
                <ChevronDown className="w-3.5 h-3.5 text-charcoal-muted" />
              </div>
              <div className="text-[10px] text-charcoal-muted leading-none mt-0.5 capitalize">
                Role: {currentRole}
              </div>
            </div>
          </button>

          {showOrgMenu && (
            <div className="absolute left-0 mt-2 w-72 bg-white rounded-2xl shadow-option-c-lg border border-bordergrey p-2 z-40 animate-in fade-in duration-100">
              <div className="px-3 py-1.5 text-[10px] font-bold text-charcoal-muted uppercase tracking-wider">
                Organizations & Workspaces
              </div>
              <div className="space-y-1">
                {organizations.map((o) => (
                  <button
                    key={o.id}
                    onClick={() => {
                      switchOrganization(o.id);
                      setShowOrgMenu(false);
                      addToast({
                        type: 'info',
                        title: 'Workspace Switched',
                        message: `Switched active organization to ${o.name}`,
                      });
                    }}
                    className={`w-full text-left px-3 py-2 rounded-xl flex items-center justify-between transition-colors cursor-pointer ${
                      activeOrg?.id === o.id ? 'bg-brand-50 border border-brand-200' : 'hover:bg-softbeige/40'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-charcoal">{o.name}</div>
                      <div className="text-[10px] text-charcoal-muted capitalize">{o.role} Role</div>
                    </div>
                    {activeOrg?.id === o.id && <Check className="w-4 h-4 text-forest" />}
                  </button>
                ))}
              </div>
              <div className="mt-2 pt-2 border-t border-bordergrey space-y-0.5">
                <Link
                  to="/app/brand"
                  onClick={() => setShowOrgMenu(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-charcoal hover:bg-softbeige/40 rounded-xl font-medium"
                >
                  <Building2 className="w-3.5 h-3.5 text-charcoal-muted" />
                  Manage Brand Guidelines
                </Link>
                <Link
                  to="/app/settings"
                  onClick={() => setShowOrgMenu(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-charcoal hover:bg-softbeige/40 rounded-xl font-medium"
                >
                  <Shield className="w-3.5 h-3.5 text-charcoal-muted" />
                  Organization Settings
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        <a
          href={siteConfig.githubRepoUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="View MarketPath AI source code on GitHub"
          title="View source on GitHub"
          className="hidden md:inline-flex p-2 text-charcoal-muted hover:text-charcoal hover:bg-softbeige/50 rounded-xl transition-colors cursor-pointer border border-bordergrey"
        >
          <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
            <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
          </svg>
        </a>

        <Link
          to="/app/products?create=true"
          className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold transition-all shadow-xs"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Product</span>
        </Link>

        {/* Notifications */}
        <div>
          <button
            onClick={() => setShowNotificationDrawer(true)}
            className="p-2 text-charcoal-muted hover:text-charcoal rounded-xl hover:bg-softbeige/50 relative cursor-pointer"
            title="Notifications Centre"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 px-1 min-w-[16px] h-4 rounded-full bg-forest text-white text-[9px] font-bold flex items-center justify-center ring-2 ring-white">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
        </div>

        {/* User Profile */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2 p-1 rounded-xl hover:bg-softbeige/50 transition-colors cursor-pointer"
          >
            <div className="w-8 h-8 rounded-full bg-softbeige text-forest font-bold flex items-center justify-center text-xs ring-1 ring-bordergrey">
              {displayName.substring(0, 1)}
            </div>
            <div className="hidden xl:block text-left">
              <div className="text-xs font-bold text-charcoal leading-tight">
                {displayName}
              </div>
              <div className="text-[10px] text-charcoal-muted leading-none capitalize mt-0.5">
                {currentRole} Role
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-charcoal-muted hidden xl:block" />
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-60 bg-white rounded-2xl shadow-option-c-lg border border-bordergrey p-2 z-40 animate-in fade-in duration-100">
              <div className="px-3 py-2 border-b border-bordergrey">
                <div className="text-xs font-bold text-charcoal">{displayName}</div>
                <div className="text-[11px] text-charcoal-muted truncate">{displayEmail}</div>
                <span className="inline-block mt-1 text-[10px] font-bold uppercase tracking-wider text-forest bg-brand-50 px-2 py-0.5 rounded-full border border-brand-200">
                  {currentRole} Role
                </span>
              </div>
              <div className="py-1">
                <Link
                  to="/app/settings"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-charcoal hover:bg-softbeige/40 rounded-xl"
                >
                  Settings & Security
                </Link>
                <Link
                  to="/app/team"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-charcoal hover:bg-softbeige/40 rounded-xl"
                >
                  Team Members & Roles
                </Link>
                <Link
                  to="/app/billing"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-charcoal hover:bg-softbeige/40 rounded-xl"
                >
                  Billing & Quotas
                </Link>
                <Link
                  to="/app/help"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs text-charcoal hover:bg-softbeige/40 rounded-xl"
                >
                  <HelpCircle className="w-3.5 h-3.5 text-charcoal-muted" />
                  Documentation & Help
                </Link>
              </div>
              <div className="pt-1 border-t border-bordergrey">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-rose-600 hover:bg-rose-50 rounded-xl cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <NotificationDrawer
        isOpen={showNotificationDrawer}
        onClose={() => setShowNotificationDrawer(false)}
        onCountChange={setUnreadCount}
      />
    </header>
  );
};
