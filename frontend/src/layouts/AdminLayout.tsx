import React from 'react';
import { Outlet, NavLink, Link } from 'react-router-dom';
import {
  ShieldAlert,
  Activity,
  Building2,
  Building,
  Users,
  Sliders,
  Network,
  AlertOctagon,
  Headphones,
  FileText,
  ArrowLeft,
  CalendarCheck,
} from 'lucide-react';
import { ToastContainer } from '../components/common/ToastContainer';
import { DemoBanner } from '../components/common/DemoBanner';

export const AdminLayout: React.FC = () => {
  const adminNav = [
    { name: 'System Overview', to: '/admin', icon: Activity },
    { name: 'Tenants & Orgs', to: '/admin/organizations', icon: Building2 },
    { name: 'Agency Verification', to: '/admin/agencies', icon: Building },
    { name: 'Global Users', to: '/admin/users', icon: Users },
    { name: 'Plan Configurator', to: '/admin/plans', icon: Sliders },
    { name: 'Connector Health', to: '/admin/integrations', icon: Network },
    { name: 'Job Telemetry & DLQ', to: '/admin/jobs', icon: AlertOctagon },
    { name: 'Consultations & Services', to: '/admin/support', icon: CalendarCheck },
    { name: 'Audit Logs', to: '/admin/audit-logs', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <DemoBanner />
      {/* Operator Security Warning Banner */}
      <div className="bg-forest-deep border-b border-forest px-4 py-2.5 text-xs flex items-center justify-between text-emerald">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-softorange shrink-0" />
          <span className="font-mono text-[11px] font-bold tracking-wider uppercase text-slate-200">
            RESTRICTED PLATFORM OPERATOR CONSOLE — ROLE: PLATFORM_ADMIN
          </span>
        </div>
        <Link
          to="/app/dashboard"
          className="flex items-center gap-1.5 text-xs font-bold text-white bg-forest hover:bg-brand-600 px-3 py-1 rounded-xl border border-brand-700 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Return to Seller Workspace
        </Link>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Admin Dark Sidebar */}
        <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col">
          <div className="h-16 px-6 flex items-center border-b border-slate-800 gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-forest flex items-center justify-center text-emerald font-extrabold text-xs shadow-xs border border-brand-700">
              OP
            </div>
            <div>
              <span className="text-sm font-bold text-white tracking-tight">MarketPath Ops</span>
              <span className="block text-[9px] text-slate-400 uppercase tracking-widest font-mono">
                Superuser Console
              </span>
            </div>
          </div>

          <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {adminNav.map((item) => (
              <NavLink
                key={item.name}
                to={item.to}
                end={item.to === '/admin'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-forest text-emerald border border-brand-700 font-bold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            ))}
          </div>

          <div className="p-4 border-t border-slate-800 text-[11px] text-slate-500 font-mono space-y-0.5">
            <div>API Cluster: ap-south-1</div>
            <div>Build: v3.0.0-verified</div>
            <div>Status: Nominal</div>
          </div>
        </aside>

        {/* Admin Canvas */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 bg-slate-900/90 text-slate-100">
          <Outlet />
        </main>
      </div>

      <ToastContainer />
    </div>
  );
};
