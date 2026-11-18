import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import type { Session, User as SupabaseUser } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../lib/supabase';
import { apiClient, ApiError, BACKEND_BASE_URL } from '../lib/api';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string | null;
  account_type?: string;
  is_platform_admin: boolean;
}

export interface OrganizationWithRole {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  settings: Record<string, any>;
  role: 'owner' | 'admin' | 'marketer' | 'viewer';
}

interface AuthContextType {
  session: Session | null;
  user: UserProfile | null;
  organizations: OrganizationWithRole[];
  activeOrg: OrganizationWithRole | null;
  role: 'owner' | 'admin' | 'marketer' | 'viewer' | null;
  isLoading: boolean;
  isDemoMode: boolean;
  isConfigured: boolean;
  loginWithEmail: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  loginWithAccountType: (
    email: string,
    password: string,
    accountType: 'company' | 'agency' | 'consultant' | 'admin'
  ) => Promise<{ success: boolean; error?: string; redirect_url?: string }>;
  registerCompany: (data: {
    brand_name: string;
    category: string;
    custom_category?: string;
    founder_name: string;
    email: string;
    password: string;
    website_url?: string;
  }) => Promise<{ success: boolean; error?: string; redirect_url?: string }>;
  signupWithEmail: (
    email: string,
    password: string,
    fullName: string,
    brandName: string,
    category?: string
  ) => Promise<{ success: boolean; error?: string; needsVerification?: boolean }>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string; reset_token?: string }>;
  confirmPasswordReset: (token: string, password: string) => Promise<{ success: boolean; error?: string }>;
  switchOrganization: (orgId: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<UserProfile | null>(() => {
    // Check if saved user exists in storage
    const saved = localStorage.getItem('marketpath_auth_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [organizations, setOrganizations] = useState<OrganizationWithRole[]>(() => {
    const saved = localStorage.getItem('marketpath_auth_orgs');
    return saved ? JSON.parse(saved) : [];
  });
  const [activeOrgId, setActiveOrgId] = useState<string | null>(() => {
    return localStorage.getItem('marketpath_active_org_id') || null;
  });
  const [isDemoMode, setIsDemoMode] = useState<boolean>(() => {
    return localStorage.getItem('marketpath_is_demo') === 'true';
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const activeOrg = useMemo(() => {
    if (!organizations.length) return null;
    return organizations.find((o) => o.id === activeOrgId) || organizations[0];
  }, [organizations, activeOrgId]);

  const role = activeOrg ? activeOrg.role : null;

  // Sync state to localStorage
  useEffect(() => {
    if (user) localStorage.setItem('marketpath_auth_user', JSON.stringify(user));
    else localStorage.removeItem('marketpath_auth_user');
  }, [user]);

  useEffect(() => {
    if (organizations.length) localStorage.setItem('marketpath_auth_orgs', JSON.stringify(organizations));
    else localStorage.removeItem('marketpath_auth_orgs');
  }, [organizations]);

  useEffect(() => {
    if (activeOrgId) localStorage.setItem('marketpath_active_org_id', activeOrgId);
    else localStorage.removeItem('marketpath_active_org_id');
  }, [activeOrgId]);

  useEffect(() => {
    localStorage.setItem('marketpath_is_demo', String(isDemoMode));
  }, [isDemoMode]);

  // Synchronize authenticated user profile and organizations from backend
  const syncWithBackend = async (accessToken: string) => {
    try {
      const data = await apiClient('/api/v1/auth/me', { token: accessToken });
      if (data && data.user) {
        setUser(data.user);
        setOrganizations(data.organizations || []);
        if (data.organizations?.length > 0) {
          const matched = data.organizations.find((o: OrganizationWithRole) => o.id === activeOrgId);
          setActiveOrgId(matched ? matched.id : data.organizations[0].id);
        }
        setIsDemoMode(false);
      }
    } catch (err: any) {
      if (err?.status === 401) {
        // Session has expired or been revoked on the server
        console.warn('Session expired or revoked. Logging out.');
        localStorage.removeItem('marketpath_auth_token');
        localStorage.removeItem('marketpath_auth_user');
        localStorage.removeItem('marketpath_auth_orgs');
        localStorage.removeItem('marketpath_active_org_id');
        localStorage.removeItem('marketpath_is_demo');
        setUser(null);
        setOrganizations([]);
        setActiveOrgId(null);
        setSession(null);
      } else {
        console.warn('Backend sync deferred or running offline:', err);
      }
    }
  };

  // Listen to Supabase Auth State changes or local session
  useEffect(() => {
    const savedToken = localStorage.getItem('marketpath_auth_token');

    if (!isSupabaseConfigured) {
      if (savedToken) {
        setSession({ access_token: savedToken, token_type: 'bearer' } as any);
        syncWithBackend(savedToken).finally(() => setIsLoading(false));
      } else {
        // Real unauthenticated visitor state - do not auto-login as demo
        setIsLoading(false);
      }
      return;
    }

    supabase.auth.getSession().then(({ data: { session: initialSession } }) => {
      setSession(initialSession);
      if (initialSession) {
        syncWithBackend(initialSession.access_token).finally(() => setIsLoading(false));
      } else if (savedToken) {
        syncWithBackend(savedToken).finally(() => setIsLoading(false));
      } else {
        setIsLoading(false);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, newSession) => {
      setSession(newSession);
      if (newSession) {
        await syncWithBackend(newSession.access_token);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const loginWithAccountType = async (
    email: string,
    password: string,
    accountType: 'company' | 'agency' | 'consultant' | 'admin'
  ) => {
    setIsLoading(true);
    let resp: Response;
    try {
      resp = await fetch(`${BACKEND_BASE_URL}/api/v1/auth/login-account`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password, account_type: accountType }),
      });
    } catch (netErr: any) {
      setIsLoading(false);
      const errorMsg =
        netErr?.message === 'Failed to fetch' || netErr?.name === 'TypeError'
          ? 'Cannot connect to MarketPath server. Please verify the backend service is running on port 8000.'
          : netErr?.message || 'Network request failed.';
      return { success: false, error: errorMsg };
    }

    try {
      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        setIsLoading(false);
        const errorMsg =
          errJson.detail ||
          errJson.error?.message ||
          'Sign in failed. Please check your credentials.';
        return { success: false, error: errorMsg };
      }

      const data = await resp.json();
      localStorage.setItem('marketpath_auth_token', data.access_token);
      localStorage.setItem('marketpath_auth_user', JSON.stringify(data.user));
      setUser(data.user);
      setSession({ access_token: data.access_token, token_type: 'bearer' } as any);

      if (data.organization) {
        localStorage.setItem('marketpath_auth_orgs', JSON.stringify([data.organization]));
        localStorage.setItem('marketpath_active_org_id', data.organization.id);
        setOrganizations([data.organization]);
        setActiveOrgId(data.organization.id);
      } else {
        localStorage.removeItem('marketpath_auth_orgs');
        localStorage.removeItem('marketpath_active_org_id');
        setOrganizations([]);
        setActiveOrgId(null);
      }

      setIsDemoMode(false);
      localStorage.setItem('marketpath_is_demo', 'false');
      setIsLoading(false);
      return { success: true, redirect_url: data.redirect_url };
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: err.message || 'Login failed' };
    }
  };

  const registerCompany = async (regData: {
    brand_name: string;
    category: string;
    custom_category?: string;
    founder_name: string;
    email: string;
    password: string;
    website_url?: string;
  }) => {
    setIsLoading(true);
    const payload = {
      brand_name: regData.brand_name,
      category: regData.category,
      custom_category: regData.custom_category,
      founder_name: regData.founder_name,
      full_name: regData.founder_name,
      email: regData.email,
      password: regData.password,
      website_url: regData.website_url,
      website: regData.website_url,
    };

    let resp: Response;
    try {
      resp = await fetch(`${BACKEND_BASE_URL}/api/v1/auth/register-company`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
    } catch (netErr: any) {
      setIsLoading(false);
      const errorMsg =
        netErr?.message === 'Failed to fetch' || netErr?.name === 'TypeError'
          ? 'Cannot connect to MarketPath server. Please verify the backend service is running on port 8000.'
          : netErr?.message || 'Network request failed.';
      return { success: false, error: errorMsg };
    }

    try {
      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        setIsLoading(false);
        const errorMsg =
          errJson.detail ||
          errJson.error?.message ||
          (errJson.error?.details && errJson.error.details.length > 0 ? errJson.error.details[0].issue : null) ||
          'Company registration failed.';
        return { success: false, error: errorMsg };
      }

      const data = await resp.json();
      localStorage.setItem('marketpath_auth_token', data.access_token);
      localStorage.setItem('marketpath_auth_user', JSON.stringify(data.user));
      setUser(data.user);
      setSession({ access_token: data.access_token, token_type: 'bearer' } as any);

      if (data.organization) {
        localStorage.setItem('marketpath_auth_orgs', JSON.stringify([data.organization]));
        localStorage.setItem('marketpath_active_org_id', data.organization.id);
        setOrganizations([data.organization]);
        setActiveOrgId(data.organization.id);
      }

      setIsDemoMode(false);
      localStorage.setItem('marketpath_is_demo', 'false');
      setIsLoading(false);
      return { success: true, redirect_url: data.redirect_url || '/app/dashboard' };
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: err.message || 'Failed to complete registration.' };
    }
  };

  const loginWithEmail = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      if (!isSupabaseConfigured) {
        const res = await loginWithAccountType(email, password, 'company');
        setIsLoading(false);
        return res;
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setIsLoading(false);
        return { success: false, error: error.message };
      }

      if (data.session) {
        setSession(data.session);
        await syncWithBackend(data.session.access_token);
      }

      setIsLoading(false);
      return { success: true };
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: err.message || 'Login failed' };
    }
  };

  const signupWithEmail = async (
    email: string,
    password: string,
    fullName: string,
    brandName: string,
    category: string = 'Home & Living'
  ) => {
    setIsLoading(true);
    try {
      if (!isSupabaseConfigured) {
        const res = await registerCompany({
          brand_name: brandName,
          founder_name: fullName,
          email,
          password,
          category,
        });
        setIsLoading(false);
        return { success: res.success, error: res.error };
      }

      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            brand_name: brandName,
            category,
          },
        },
      });

      if (error) {
        setIsLoading(false);
        return { success: false, error: error.message };
      }

      if (data.session) {
        setSession(data.session);
        try {
          const newOrg = await apiClient<OrganizationWithRole>('/api/v1/organizations', {
            method: 'POST',
            token: data.session.access_token,
            body: JSON.stringify({
              name: brandName,
              brand_name: brandName,
              category,
            }),
          });
          setOrganizations([newOrg]);
          setActiveOrgId(newOrg.id);
          setIsDemoMode(false);
        } catch (orgErr) {
          console.error('Failed to create organization during signup:', orgErr);
        }
      }

      setIsLoading(false);
      return {
        success: true,
        needsVerification: !data.session && !!data.user,
      };
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: err.message || 'Signup failed' };
    }
  };

  const logout = async () => {
    setIsLoading(true);
    const savedToken = localStorage.getItem('marketpath_auth_token');
    try {
      await fetch(`${BACKEND_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(savedToken ? { Authorization: `Bearer ${savedToken}` } : {}),
        },
        credentials: 'include',
      });
    } catch (err) {
      console.warn('Backend logout warning:', err);
    }

    if (isSupabaseConfigured) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.warn('Sign out warning:', err);
      }
    }
    setSession(null);
    setUser(null);
    setOrganizations([]);
    setActiveOrgId(null);
    setIsDemoMode(false);
    localStorage.removeItem('marketpath_auth_token');
    localStorage.removeItem('marketpath_auth_user');
    localStorage.removeItem('marketpath_auth_orgs');
    localStorage.removeItem('marketpath_active_org_id');
    localStorage.removeItem('marketpath_is_demo');
    setIsLoading(false);
  };

  const resetPassword = async (email: string) => {
    try {
      if (isSupabaseConfigured) {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/reset-password`,
        });
        if (error) return { success: false, error: error.message };
        return { success: true };
      }

      const res = await apiClient<{ success: boolean; message: string; reset_token?: string }>(
        '/api/v1/auth/forgot-password',
        {
          method: 'POST',
          body: JSON.stringify({ email }),
        }
      );
      return { success: true, error: undefined, reset_token: res.reset_token };
    } catch (err: any) {
      return { success: false, error: err.message || 'Password reset request failed.' };
    }
  };

  const confirmPasswordReset = async (token: string, password: string) => {
    try {
      if (isSupabaseConfigured) {
        const { error } = await supabase.auth.updateUser({ password });
        if (error) return { success: false, error: error.message };
        return { success: true };
      }

      await apiClient('/api/v1/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, password }),
      });
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to update password.' };
    }
  };

  const switchOrganization = (orgId: string) => {
    const matched = organizations.find((o) => o.id === orgId);
    if (matched) {
      setActiveOrgId(matched.id);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        session,
        user,
        organizations,
        activeOrg,
        role,
        isLoading,
        isDemoMode,
        isConfigured: isSupabaseConfigured,
        loginWithEmail,
        signupWithEmail,
        logout,
        resetPassword,
        confirmPasswordReset,
        switchOrganization,
        loginWithAccountType,
        registerCompany,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

