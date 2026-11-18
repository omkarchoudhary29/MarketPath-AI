import React from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { Sparkles, Database, ShieldCheck } from 'lucide-react';

export const DemoBanner: React.FC = () => {
  const { isDemoMode } = useApp();
  const auth = useAuth();

  const isDemoAccount =
    isDemoMode ||
    auth?.isDemoMode ||
    auth?.user?.email?.startsWith('demo.') ||
    auth?.activeOrg?.settings?.is_demo === true ||
    auth?.activeOrg?.name?.includes('(Demo)');

  if (!isDemoAccount) {
    return null;
  }

  return (
    <div className="px-4 py-2 border-b text-xs flex flex-wrap items-center justify-between gap-2 transition-colors bg-softorange/10 border-softorange/25 text-charcoal">
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1 font-bold px-2 py-0.5 rounded text-[10px] uppercase tracking-wider bg-softorange/20 text-softorange">
          <Database className="w-3 h-3" />
          Demo Environment
        </span>
        <span className="text-mutedgrey text-[11px] hidden sm:inline">
          Sample data for interview evaluation (Aura Terra Living — Pune). External marketplace mutations are safely simulated.
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-[11px] text-mutedgrey hidden md:inline">
          Signed in as: <strong className="text-charcoal">{auth?.user?.email || 'Demo Visitor'}</strong>
        </span>
        <Link
          to="/login"
          className="font-medium text-forest hover:text-brand-600 flex items-center gap-1 cursor-pointer text-[11px] hover:underline"
        >
          <Sparkles className="w-3.5 h-3.5 text-softorange" />
          Switch Demo Persona
        </Link>
      </div>
    </div>
  );
};
