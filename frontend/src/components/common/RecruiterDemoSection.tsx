import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Briefcase,
  UserCheck,
  ShieldAlert,
  Copy,
  Check,
  ArrowRight,
  Sparkles,
  Lock,
  Mail,
  ShieldCheck,
} from 'lucide-react';

export interface DemoAccountInfo {
  type: 'company' | 'agency' | 'consultant' | 'admin';
  title: string;
  role: string;
  email: string;
  password: string;
  badge: string;
  badgeColor: string;
  description: string;
  accentBorder: string;
  icon: React.ReactNode;
}

export const DEMO_ACCOUNTS: DemoAccountInfo[] = [
  {
    type: 'company',
    title: 'Explore Company Workspace',
    role: 'Company Demo (Brand Owner)',
    email: 'demo.company@marketpath.ai',
    password: 'MarketPath-Company-Demo-2026!',
    badge: 'Brand Owner',
    badgeColor: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20',
    description: '18 products, 40 channel orders across 4 marketplaces, inventory alerts & 4 live marketing campaigns (Aura Terra Living).',
    accentBorder: 'hover:border-emerald-500/50',
    icon: <Building2 className="w-5 h-5 text-emerald-600" />,
  },
  {
    type: 'agency',
    title: 'Explore Agency Portal',
    role: 'Agency Demo (Partner Agency)',
    email: 'demo.agency@marketpath.ai',
    password: 'MarketPath-Agency-Demo-2026!',
    badge: 'Verified Agency',
    badgeColor: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20',
    description: 'Verified Partner profile, 3 service packages, inbound RFPs, client engagements & privacy-vaulted proposals (CraftVerve Media).',
    accentBorder: 'hover:border-amber-500/50',
    icon: <Briefcase className="w-5 h-5 text-amber-600" />,
  },
  {
    type: 'consultant',
    title: 'Explore Consultant Portal',
    role: 'Consultant Demo (Category Advisor)',
    email: 'demo.consultant@marketpath.ai',
    password: 'MarketPath-Consultant-Demo-2026!',
    badge: 'Lead Advisor',
    badgeColor: 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20',
    description: 'Advisory desk with 4 strategic advisory sessions, private diagnostic notes, unit economics audits & checklists (Dr. Rajesh Sharma).',
    accentBorder: 'hover:border-blue-500/50',
    icon: <UserCheck className="w-5 h-5 text-blue-600" />,
  },
  {
    type: 'admin',
    title: 'Explore Demo Administration',
    role: 'Demo Admin (Operator Console)',
    email: 'demo.admin@marketpath.ai',
    password: 'MarketPath-DemoAdmin-2026!',
    badge: 'Demo Admin',
    badgeColor: 'bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20',
    description: 'Demonstration administration console with tenant oversight, connector health telemetry, and immutable audit logs.',
    accentBorder: 'hover:border-purple-500/50',
    icon: <ShieldAlert className="w-5 h-5 text-purple-600" />,
  },
];

interface RecruiterDemoSectionProps {
  onSelectRole?: (role: 'company' | 'agency' | 'consultant' | 'admin') => void;
  className?: string;
  isCompact?: boolean;
}

export const RecruiterDemoSection: React.FC<RecruiterDemoSectionProps> = ({
  onSelectRole,
  className = '',
  isCompact = false,
}) => {
  const navigate = useNavigate();
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = async (text: string, key: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
    } catch {
      // Fallback
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
    }
  };

  const handleOpenLogin = (account: DemoAccountInfo) => {
    if (onSelectRole) {
      onSelectRole(account.type);
    } else {
      navigate(`/login?type=${account.type}`);
    }
  };

  return (
    <section className={`w-full ${className}`}>
      <div className="rounded-3xl bg-forest-deep bg-[#053F32] p-6 sm:p-8 md:p-10 border border-[#075443] shadow-option-c-lg text-white">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#075443]">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#075443] text-emerald text-xs font-bold uppercase tracking-wider border border-[#15966F]/40">
              <Sparkles className="w-3.5 h-3.5 fill-emerald" />
              <span>Public Demonstration Access</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Explore MarketPath AI — Recruiter Demo Access
            </h2>
            <p className="text-xs sm:text-sm text-[#C1E0D4] max-w-2xl">
              Instant evaluation credentials for interviewers and reviewers. Each persona is fully isolated and pre-populated with realistic Indian D2C operational data.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#8CC5B0] bg-[#075443]/60 px-3.5 py-2 rounded-xl border border-[#15966F]/30 shrink-0">
            <ShieldCheck className="w-4 h-4 text-emerald shrink-0" />
            <span>Isolated Demo Tenant • Zero Real PII</span>
          </div>
        </div>

        {/* 4 Demo Options Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 pt-6">
          {DEMO_ACCOUNTS.map((account) => {
            const emailKey = `${account.type}-email`;
            const passKey = `${account.type}-pass`;

            return (
              <div
                key={account.type}
                className={`rounded-2xl bg-[#075443]/60 p-5 border border-[#15966F]/30 ${account.accentBorder} transition-all flex flex-col justify-between space-y-4`}
              >
                {/* Header & Badges */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="w-9 h-9 rounded-xl bg-forest flex items-center justify-center border border-brand-700 shrink-0">
                      {account.icon}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald bg-forest px-2.5 py-0.5 rounded-full border border-brand-700">
                      {account.badge}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white tracking-tight">{account.title}</h3>
                    <p className="text-[11px] font-semibold text-[#8CC5B0] mt-0.5">{account.role}</p>
                  </div>

                  {!isCompact && (
                    <p className="text-xs text-[#C1E0D4] leading-relaxed line-clamp-3">
                      {account.description}
                    </p>
                  )}

                  {/* Credentials Box */}
                  <div className="rounded-xl bg-[#042F25] p-3 space-y-2 border border-[#075443] text-xs">
                    {/* Email */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0 text-gray-300">
                        <Mail className="w-3.5 h-3.5 text-[#8CC5B0] shrink-0" />
                        <span className="truncate font-mono text-[11px] text-white select-all">{account.email}</span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => copyToClipboard(account.email, emailKey, e)}
                        title="Copy email address"
                        className="p-1 rounded-md bg-[#075443] hover:bg-forest text-emerald hover:text-white transition-colors cursor-pointer shrink-0"
                      >
                        {copiedKey === emailKey ? (
                          <Check className="w-3.5 h-3.5 text-emerald" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    {/* Password */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0 text-gray-300">
                        <Lock className="w-3.5 h-3.5 text-[#8CC5B0] shrink-0" />
                        <span className="truncate font-mono text-[11px] text-amber-200 select-all">{account.password}</span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => copyToClipboard(account.password, passKey, e)}
                        title="Copy demo password"
                        className="p-1 rounded-md bg-[#075443] hover:bg-forest text-emerald hover:text-white transition-colors cursor-pointer shrink-0"
                      >
                        {copiedKey === passKey ? (
                          <Check className="w-3.5 h-3.5 text-emerald" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Open Login Action */}
                <button
                  type="button"
                  onClick={() => handleOpenLogin(account)}
                  className="w-full text-center py-2.5 px-4 rounded-xl bg-emerald hover:bg-[#128260] text-forest-deep text-xs font-bold transition-all shadow-xs flex items-center justify-center gap-1.5 cursor-pointer mt-2"
                >
                  <span>Open & Pre-fill Login</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>

        {/* Footnote */}
        <div className="mt-6 pt-4 border-t border-[#075443] text-center text-xs text-[#8CC5B0]">
          <span>Notice: These are dedicated public demonstration credentials. Destructive external sync and real credit spending are strictly disabled in demo mode.</span>
        </div>
      </div>
    </section>
  );
};
