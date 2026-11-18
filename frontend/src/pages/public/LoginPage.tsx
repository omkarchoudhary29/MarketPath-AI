import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import {
  LogIn,
  Sparkles,
  ArrowRight,
  Lock,
  Mail,
  ShieldCheck,
  Building2,
  Users2,
  ShieldAlert,
  Eye,
  EyeOff,
  Briefcase,
  UserCheck,
  CheckCircle2,
  RotateCcw,
  Copy,
  Check,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { RecruiterDemoSection } from '../../components/common/RecruiterDemoSection';

const DEMO_CREDENTIALS: Record<
  'company' | 'agency' | 'consultant' | 'admin',
  { email: string; password: string; name: string; desc: string }
> = {
  company: {
    email: 'demo.company@marketpath.ai',
    password: 'MarketPath-Company-Demo-2026!',
    name: 'Aura Terra Living (Brand Owner)',
    desc: 'Pre-filled with 18 D2C products, 40 channel orders across 4 marketplaces, inventory alerts & analytics',
  },
  agency: {
    email: 'demo.agency@marketpath.ai',
    password: 'MarketPath-Agency-Demo-2026!',
    name: 'CraftVerve Media (Agency Partner)',
    desc: 'Pre-filled with Verified Partner profile, 3 service packages, active RFPs & client engagements',
  },
  consultant: {
    email: 'demo.consultant@marketpath.ai',
    password: 'MarketPath-Consultant-Demo-2026!',
    name: 'Dr. Rajesh Sharma (Lead D2C Advisor)',
    desc: 'Pre-filled with 4 strategic advisory sessions, diagnostics & private confidential notes',
  },
  admin: {
    email: 'demo.admin@marketpath.ai',
    password: 'MarketPath-DemoAdmin-2026!',
    name: 'Demo Platform Operator (Admin Console)',
    desc: 'Pre-filled with platform telemetry, tenant oversight, user vetting & audit logs',
  },
};

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { loginWithAccountType } = useAuth();
  const { addToast } = useApp();

  const getInitialAccountType = (): 'company' | 'agency' | 'consultant' | 'admin' => {
    const params = new URLSearchParams(location.search);
    const typeParam = params.get('type') || params.get('role');
    if (typeParam === 'agency' || location.pathname.includes('/agency')) return 'agency';
    if (typeParam === 'consultant' || location.pathname.includes('/consultant')) return 'consultant';
    if (typeParam === 'admin' || location.pathname.includes('/admin')) return 'admin';
    return 'company';
  };

  const initialType = getInitialAccountType();
  const [accountType, setAccountType] = useState<'company' | 'agency' | 'consultant' | 'admin'>(initialType);
  const [email, setEmail] = useState(DEMO_CREDENTIALS[initialType].email);
  const [password, setPassword] = useState(DEMO_CREDENTIALS[initialType].password);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = (text: string, field: string) => {
    try {
      navigator.clipboard.writeText(text);
    } catch {
      // Ignore
    }
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
    addToast({
      type: 'info',
      title: 'Copied to Clipboard',
      message: `${field === 'email' ? 'Email' : 'Password'} copied successfully.`,
    });
  };

  // Auto-sync credentials when URL query parameter changes
  useEffect(() => {
    const type = getInitialAccountType();
    setAccountType(type);
    setEmail(DEMO_CREDENTIALS[type].email);
    setPassword(DEMO_CREDENTIALS[type].password);
    setErrorMessage(null);
  }, [location.search, location.pathname]);

  const returnUrl = (location.state as any)?.from || (
    accountType === 'admin'
      ? '/admin'
      : accountType === 'agency'
      ? '/agency/portal'
      : accountType === 'consultant'
      ? '/consultant'
      : '/app/dashboard'
  );

  const handleAccountTypeChange = (type: 'company' | 'agency' | 'consultant' | 'admin') => {
    setAccountType(type);
    setEmail(DEMO_CREDENTIALS[type].email);
    setPassword(DEMO_CREDENTIALS[type].password);
    setErrorMessage(null);
  };

  const handleResetDemoCredentials = () => {
    setEmail(DEMO_CREDENTIALS[accountType].email);
    setPassword(DEMO_CREDENTIALS[accountType].password);
    setErrorMessage(null);
    addToast({
      type: 'info',
      title: 'Demo Credentials Loaded',
      message: `Pre-filled ${accountType.toUpperCase()} credentials.`,
    });
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    const res = await loginWithAccountType(email, password, accountType);
    setIsLoading(false);

    if (res.success) {
      addToast({
        type: 'success',
        title: 'Authentication Successful',
        message: `Signed in as ${accountType.toUpperCase()} account.`,
      });
      navigate(res.redirect_url || returnUrl);
    } else {
      setErrorMessage(res.error || 'Invalid credentials for this account type.');
      addToast({
        type: 'error',
        title: 'Sign In Failed',
        message: res.error || 'Authentication credentials rejected.',
      });
    }
  };

  return (
    <div className="min-h-[85vh] flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-warmwhite">
      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl border border-bordergrey shadow-option-c-lg">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center gap-2 mb-2">
            <div className="w-9 h-9 rounded-xl bg-forest bg-gradient-to-tr from-[#075443] via-[#08765B] to-[#15966F] border border-[#15966F]/40 flex items-center justify-center text-white font-extrabold text-sm shadow-sm">
              MP
            </div>
            <span className="text-xl font-bold text-charcoal tracking-tight">MarketPath AI</span>
          </Link>
          <h2 className="text-2xl font-extrabold text-charcoal tracking-tight">Sign in to MarketPath</h2>
          <p className="text-xs text-charcoal-muted">
            Select your account type to access the correct portal
          </p>
        </div>

        {/* 4 Account Types Selector */}
        <div className="grid grid-cols-4 p-1 rounded-2xl bg-softbeige border border-bordergrey text-[11px] font-bold">
          <button
            type="button"
            onClick={() => handleAccountTypeChange('company')}
            className={`py-2 px-1 rounded-xl flex flex-col items-center gap-1 transition-all cursor-pointer ${
              accountType === 'company'
                ? 'bg-white text-forest shadow-xs font-bold'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Company</span>
          </button>

          <button
            type="button"
            onClick={() => handleAccountTypeChange('agency')}
            className={`py-2 px-1 rounded-xl flex flex-col items-center gap-1 transition-all cursor-pointer ${
              accountType === 'agency'
                ? 'bg-white text-forest shadow-xs font-bold'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Agency</span>
          </button>

          <button
            type="button"
            onClick={() => handleAccountTypeChange('consultant')}
            className={`py-2 px-1 rounded-xl flex flex-col items-center gap-1 transition-all cursor-pointer ${
              accountType === 'consultant'
                ? 'bg-white text-forest shadow-xs font-bold'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Consultant</span>
          </button>

          <button
            type="button"
            onClick={() => handleAccountTypeChange('admin')}
            className={`py-2 px-1 rounded-xl flex flex-col items-center gap-1 transition-all cursor-pointer ${
              accountType === 'admin'
                ? 'bg-white text-forest shadow-xs font-bold'
                : 'text-charcoal-muted hover:text-charcoal'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Admin</span>
          </button>
        </div>

        {/* Account Scope Information Notice */}
        <div className="p-3 rounded-xl bg-softbeige/60 border border-bordergrey text-xs flex items-start gap-2 text-charcoal">
          {accountType === 'company' && (
            <>
              <Building2 className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
              <div>
                <strong>D2C Brand Seller Workspace:</strong> Manage your master catalogue, AI copy, connected channels, orders, and business calendar.
              </div>
            </>
          )}
          {accountType === 'agency' && (
            <>
              <Briefcase className="w-4 h-4 text-forest shrink-0 mt-0.5" />
              <div>
                <strong>Agency Partner Portal:</strong> Review inbound client RFPs, manage service packages, and submit verified case studies (with founder PII sanitized).
              </div>
            </>
          )}
          {accountType === 'consultant' && (
            <>
              <UserCheck className="w-4 h-4 text-softorange shrink-0 mt-0.5" />
              <div>
                <strong>Consultant Advisory Workspace:</strong> Platform-authorized category advisors conducting diagnostic audits and growth strategy sessions.
              </div>
            </>
          )}
          {accountType === 'admin' && (
            <>
              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <strong>Platform Operator Console:</strong> Server-side provisioned super-admin access only. Public self-registration is permanently disabled.
              </div>
            </>
          )}
        </div>

        {/* Demo Credentials Pre-fill Notice Banner with Quick Copy Actions */}
        <div className="p-3.5 rounded-2xl bg-forest/5 border border-forest/20 space-y-2 text-xs">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <CheckCircle2 className="w-4 h-4 text-emerald shrink-0" />
              <div className="truncate">
                <span className="font-bold text-forest">Demo Mode Active: </span>
                <span className="text-charcoal-muted font-medium truncate">{DEMO_CREDENTIALS[accountType].name}</span>
              </div>
            </div>
            <button
              type="button"
              onClick={handleResetDemoCredentials}
              title="Refill default demo credentials for this role"
              className="text-[11px] font-bold text-forest hover:text-emerald inline-flex items-center gap-1 cursor-pointer underline shrink-0"
            >
              <RotateCcw className="w-3 h-3" />
              Refill
            </button>
          </div>

          <div className="flex items-center justify-between gap-2 pt-1.5 border-t border-forest/10 text-[11px]">
            <span className="text-charcoal-muted shrink-0 font-medium">Quick Credentials:</span>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => handleCopy(DEMO_CREDENTIALS[accountType].email, 'email')}
                className="px-2 py-0.5 rounded-md bg-white border border-bordergrey hover:border-forest text-charcoal font-mono text-[10px] inline-flex items-center gap-1 cursor-pointer transition-colors"
                title="Copy demo email"
              >
                {copiedField === 'email' ? <Check className="w-3 h-3 text-emerald" /> : <Copy className="w-3 h-3 text-charcoal-muted" />}
                <span>Email</span>
              </button>
              <button
                type="button"
                onClick={() => handleCopy(DEMO_CREDENTIALS[accountType].password, 'password')}
                className="px-2 py-0.5 rounded-md bg-white border border-bordergrey hover:border-forest text-charcoal font-mono text-[10px] inline-flex items-center gap-1 cursor-pointer transition-colors"
                title="Copy demo password"
              >
                {copiedField === 'password' ? <Check className="w-3 h-3 text-emerald" /> : <Copy className="w-3 h-3 text-charcoal-muted" />}
                <span>Password</span>
              </button>
            </div>
          </div>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 leading-relaxed">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          {/* Email */}
          <div>
            <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
              {accountType === 'agency'
                ? 'Agency Email Address'
                : accountType === 'consultant'
                ? 'Consultant Email Address'
                : accountType === 'admin'
                ? 'Operator Email'
                : 'Work Email Address'}
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-charcoal-muted">
                <Mail className="w-4 h-4" />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={
                  accountType === 'agency'
                    ? 'partner@agency.com'
                    : accountType === 'consultant'
                    ? 'advisor@consulting.in'
                    : accountType === 'admin'
                    ? 'operator@marketpath.ai'
                    : 'founder@yourbrand.in'
                }
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-charcoal uppercase tracking-wider">
                Password
              </label>
              <Link
                to="/forgot-password"
                className="text-xs font-semibold text-brand-600 hover:text-forest hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-charcoal-muted">
                <Lock className="w-4 h-4" />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your account password"
                className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-charcoal-muted hover:text-charcoal cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {accountType === 'company' && (
            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center text-charcoal-muted cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-bordergrey text-brand-600 focus:ring-brand-500 mr-2"
                />
                Remember me on this browser
              </label>
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 text-sm font-bold shadow-sm"
          >
            {isLoading ? 'Authenticating...' : `Sign In to ${accountType === 'company' ? 'Workspace' : accountType === 'agency' ? 'Agency Portal' : accountType === 'consultant' ? 'Consultant Workspace' : 'Ops Console'}`}
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        </form>

        {/* Dynamic Contextual Registration Links */}
        <div className="text-center pt-3 border-t border-bordergrey">
          {accountType === 'company' && (
            <p className="text-xs text-charcoal-muted">
              Don't have a workspace yet?{' '}
              <Link to="/signup" className="font-bold text-forest hover:underline">
                Start Free Workspace
              </Link>
            </p>
          )}

          {accountType === 'agency' && (
            <p className="text-xs text-charcoal-muted">
              Looking to join our partner network?{' '}
              <Link to="/agency/signup" className="font-bold text-forest hover:underline">
                Apply as Agency Partner
              </Link>
            </p>
          )}

          {accountType === 'consultant' && (
            <p className="text-xs text-charcoal-muted">
              Interested in advising emerging Indian D2C brands?{' '}
              <Link to="/consultant/signup" className="font-bold text-forest hover:underline">
                Join Advisory Council
              </Link>
            </p>
          )}

          {accountType === 'admin' && (
            <p className="text-[11px] text-charcoal-muted">
              Platform administration is restricted to provisioned system operators. Public sign-up is disabled.
            </p>
          )}
        </div>
      </div>

      {/* SECTION: RECRUITER DEMO ACCESS */}
      <div className="w-full max-w-5xl mt-10">
        <RecruiterDemoSection onSelectRole={handleAccountTypeChange} />
      </div>
    </div>
  );
};
