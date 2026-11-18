import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { Building2, UserCheck, Lock, User, AlertCircle, CheckCircle2, ShieldCheck } from 'lucide-react';

interface InviteDetails {
  email: string;
  role: string;
  organization_name: string;
  expires_at: string;
}

export const InviteAcceptPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { addToast } = useApp();

  const [loadingVerify, setLoadingVerify] = useState(true);
  const [inviteDetails, setInviteDetails] = useState<InviteDetails | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setVerifyError('Invitation token is missing from the URL.');
      setLoadingVerify(false);
      return;
    }

    const verifyToken = async () => {
      try {
        const resp = await fetch(`/api/v1/team/invitations/${encodeURIComponent(token)}/verify`);
        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          setVerifyError(errData.detail || 'This invitation link is invalid or has expired.');
          setLoadingVerify(false);
          return;
        }

        const data: InviteDetails = await resp.json();
        setInviteDetails(data);
        setLoadingVerify(false);
      } catch (err: any) {
        setVerifyError('Failed to verify invitation link. Please check your network connection.');
        setLoadingVerify(false);
      }
    };

    verifyToken();
  }, [token]);

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    if (password !== confirmPassword) {
      setSubmitError('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setSubmitError('Password must be at least 8 characters long.');
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const resp = await fetch(`/api/v1/team/invitations/${encodeURIComponent(token)}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.trim(),
          password,
        }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        setSubmitError(errData.detail || 'Failed to accept invitation.');
        setSubmitting(false);
        return;
      }

      const authData = await resp.json();
      localStorage.setItem('marketpath_auth_token', authData.access_token);
      localStorage.setItem('marketpath_auth_user', JSON.stringify(authData.user));
      localStorage.setItem('marketpath_is_demo', 'false');

      if (authData.organization) {
        localStorage.setItem('marketpath_auth_orgs', JSON.stringify([authData.organization]));
        localStorage.setItem('marketpath_active_org_id', authData.organization.id);
      }

      addToast({
        type: 'success',
        title: 'Welcome to the Team!',
        message: `You have joined ${inviteDetails?.organization_name || 'the workspace'} as ${inviteDetails?.role || 'team member'}.`,
      });

      // Reload or navigate to trigger AuthContext state update
      window.location.href = authData.redirect_url || '/app/dashboard';
    } catch (err: any) {
      setSubmitError(err.message || 'An unexpected error occurred while accepting the invitation.');
      setSubmitting(false);
    }
  };

  if (loadingVerify) {
    return (
      <div className="min-h-[85vh] flex items-center justify-center p-4">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-600 font-medium">Verifying invitation security token...</p>
        </div>
      </div>
    );
  }

  if (verifyError || !inviteDetails) {
    return (
      <div className="min-h-[85vh] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 border border-slate-200 shadow-xl text-center space-y-5">
          <div className="w-14 h-14 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-charcoal">Invitation Link Invalid</h2>
            <p className="text-xs text-slate-500 mt-2">{verifyError || 'This link may have already been used, expired after 7 days, or was revoked.'}</p>
          </div>
          <div className="pt-2">
            <Link
              to="/login"
              className="inline-flex items-center justify-center w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs transition-colors"
            >
              Go to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[90vh] flex items-center justify-center p-4 bg-slate-50">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 sm:p-10 border border-slate-200 shadow-xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-brand-50 text-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-2">
            <Building2 className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-charcoal">Join {inviteDetails.organization_name}</h2>
          <p className="text-xs text-slate-500">
            You were invited as <span className="font-semibold text-brand-600 uppercase">{inviteDetails.role}</span> with email{' '}
            <span className="font-semibold text-slate-700">{inviteDetails.email}</span>.
          </p>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Set your private password below. Organization owners never see your password.</span>
        </div>

        {submitError && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{submitError}</span>
          </div>
        )}

        <form onSubmit={handleAccept} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-charcoal mb-1">Your Full Name *</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                required
                placeholder="e.g. Vikram Sharma"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal mb-1">Set Private Password *</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                minLength={8}
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal mb-1">Confirm Password *</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                minLength={8}
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-md transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {submitting ? (
              <span className="inline-block animate-spin">⌛</span>
            ) : (
              <>
                <UserCheck className="w-4 h-4" />
                <span>Accept Invitation & Launch Workspace</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

