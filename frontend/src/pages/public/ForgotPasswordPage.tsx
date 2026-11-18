import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { KeyRound, ArrowLeft, Mail, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';

export const ForgotPasswordPage: React.FC = () => {
  const { resetPassword } = useAuth();
  const { addToast } = useApp();
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    const res = await resetPassword(email);
    setIsLoading(false);

    if (res.success) {
      setSent(true);
      if (res.reset_token) {
        setDevToken(res.reset_token);
      }
      addToast({
        type: 'info',
        title: 'Reset Link Dispatched',
        message: `If an account exists for ${email}, a password reset link was dispatched.`,
      });
    } else {
      setErrorMessage(res.error || 'Failed to dispatch reset email.');
      addToast({
        type: 'error',
        title: 'Reset Failed',
        message: res.error || 'Password reset request failed.',
      });
    }
  };

  return (
    <div className="min-h-[75vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl border border-slate-200/90 shadow-xl">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-2">
            <KeyRound className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-charcoal">Reset Your Password</h2>
          <p className="text-xs text-slate-500">
            Enter the work email associated with your brand account.
          </p>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {sent ? (
          <div className="p-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-center space-y-3">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
            <h4 className="text-sm font-bold text-emerald-900">Check Your Inbox</h4>
            <p className="text-xs text-emerald-800 leading-relaxed">
              We have sent a secure password reset link to <strong>{email}</strong>. The link expires in 60 minutes.
            </p>
            {devToken && (
              <div className="p-3 bg-white/90 rounded-xl border border-emerald-300 text-left text-xs space-y-1.5">
                <span className="font-bold text-emerald-900 block">Direct Reset Link:</span>
                <Link
                  to={`/reset-password?token=${devToken}`}
                  className="inline-block text-xs font-bold text-brand-600 hover:text-forest underline"
                >
                  Proceed to Reset Password &rarr;
                </Link>
              </div>
            )}
            <Link
              to="/login"
              className="inline-block text-xs font-semibold text-brand-700 hover:underline pt-2"
            >
              Back to Sign In
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Work Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  placeholder="ananya@brand.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-md transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <span className="inline-block animate-spin">⌛</span>
              ) : (
                'Send Secure Password Reset Link'
              )}
            </button>

            <div className="text-center pt-2">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-charcoal"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Sign In</span>
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
