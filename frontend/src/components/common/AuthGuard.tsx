import React from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldAlert, Loader2, ArrowRight } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
  requirePlatformAdmin?: boolean;
  allowedAccountTypes?: ('company' | 'agency' | 'consultant' | 'admin')[];
}

export const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requirePlatformAdmin = false,
  allowedAccountTypes,
}) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-warmwhite flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-forest animate-spin" />
        <p className="text-sm font-medium text-charcoal-muted">Authenticating session...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // Check platform administrator access (allows genuine superadmins or demo admin exploring demo console)
  const isDemoAdminUser = user.account_type === 'admin' && (user.email === 'demo.admin@marketpath.ai' || user.email.startsWith('demo.admin'));
  if (requirePlatformAdmin && !user.is_platform_admin && !isDemoAdminUser) {
    return (
      <div className="min-h-screen bg-warmwhite flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md bg-white p-8 rounded-3xl border border-rose-200 shadow-option-c-lg space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-charcoal">Platform Admin Access Required</h2>
          <p className="text-xs text-charcoal-muted leading-relaxed">
            Your current account (<strong>{user.email}</strong>) does not have internal platform administrator privileges. This area is reserved for MarketPath system operators.
          </p>
          <div className="pt-2">
            <Link
              to="/app/dashboard"
              className="inline-flex items-center justify-center px-4 py-2 rounded-xl bg-forest hover:bg-forest/90 text-white font-semibold text-xs shadow-xs transition-colors"
            >
              Return to Seller Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Account type restriction check
  if (
    allowedAccountTypes &&
    allowedAccountTypes.length > 0 &&
    !user.is_platform_admin
  ) {
    const userType = (user.account_type || 'company') as 'company' | 'agency' | 'consultant' | 'admin';
    if (!allowedAccountTypes.includes(userType)) {
      const targetPortal =
        userType === 'agency'
          ? '/agency/portal'
          : userType === 'consultant'
          ? '/consultant'
          : '/app/dashboard';
      const portalLabel =
        userType === 'agency'
          ? 'Agency Partner Portal'
          : userType === 'consultant'
          ? 'Consultant Advisory Workspace'
          : 'D2C Seller Dashboard';

      return (
        <div className="min-h-screen bg-warmwhite flex flex-col items-center justify-center p-6 text-center">
          <div className="max-w-md bg-white p-8 rounded-3xl border border-bordergrey shadow-option-c-lg space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-softbeige text-forest flex items-center justify-center mx-auto">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-bold text-charcoal">Portal Access Restriction</h2>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              Your account (<strong>{user.email}</strong>) is registered as a{' '}
              <strong className="text-charcoal uppercase">{userType}</strong> account and cannot access this specific workspace.
            </p>
            <div className="pt-2">
              <Link
                to={targetPortal}
                className="inline-flex items-center gap-1.5 justify-center px-4 py-2.5 rounded-xl bg-forest hover:bg-forest/90 text-white font-semibold text-xs shadow-xs transition-colors"
              >
                Go to {portalLabel}
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
};

