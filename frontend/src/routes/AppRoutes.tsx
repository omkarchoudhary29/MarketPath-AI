import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import { PublicLayout } from '../layouts/PublicLayout';
import { AppLayout } from '../layouts/AppLayout';
import { AdminLayout } from '../layouts/AdminLayout';

import { AuthGuard } from '../components/common/AuthGuard';

// Public Pages
import { HomePage } from '../pages/public/HomePage';
import { AboutPage } from '../pages/public/AboutPage';
import { HowItWorksPage } from '../pages/public/HowItWorksPage';
import { TrustPage } from '../pages/public/TrustPage';
import { FreeConsultationPage } from '../pages/public/FreeConsultationPage';
import { LoginPage } from '../pages/public/LoginPage';
import { SignupPage } from '../pages/public/SignupPage';
import { AgencySignupPage } from '../pages/public/AgencySignupPage';
import { ConsultantSignupPage } from '../pages/public/ConsultantSignupPage';
import { InviteAcceptPage } from '../pages/public/InviteAcceptPage';
import { ForgotPasswordPage } from '../pages/public/ForgotPasswordPage';
import { ResetPasswordPage } from '../pages/public/ResetPasswordPage';

// App Pages
import { DashboardPage } from '../pages/app/DashboardPage';
import { BrandProfilePage } from '../pages/app/BrandProfilePage';
import { ProductsPage } from '../pages/app/ProductsPage';
import { AddProductPage } from '../pages/app/AddProductPage';
import { ProductDetailPage } from '../pages/app/ProductDetailPage';
import { AIStudioPage } from '../pages/app/AIStudioPage';
import { IntegrationsPage } from '../pages/app/IntegrationsPage';
import { PublishingPage } from '../pages/app/PublishingPage';
import { OrdersPage } from '../pages/app/OrdersPage';
import { CalendarPage } from '../pages/app/CalendarPage';
import { MarketingPage } from '../pages/app/MarketingPage';
import { CampaignDetailPage } from '../pages/app/CampaignDetailPage';
import { AnalyticsPage } from '../pages/app/AnalyticsPage';
import { BillingPage } from '../pages/app/BillingPage';
import { AgencyConnectPage } from '../pages/app/AgencyConnectPage';
import { AgencyPortalPage } from '../pages/agency/AgencyPortalPage';
import { ConsultantPortalPage } from '../pages/consultant/ConsultantPortalPage';
import { TeamPage } from '../pages/app/TeamPage';
import { SettingsPage } from '../pages/app/SettingsPage';
import { HelpPage } from '../pages/app/HelpPage';

// Admin Pages
import { AdminDashboardPage } from '../pages/admin/AdminDashboardPage';
import { AdminOrgsPage } from '../pages/admin/AdminOrgsPage';
import { AdminUsersPage } from '../pages/admin/AdminUsersPage';
import { AdminPlansPage } from '../pages/admin/AdminPlansPage';
import { AdminAgenciesPage } from '../pages/admin/AdminAgenciesPage';
import { AdminIntegrationsPage } from '../pages/admin/AdminIntegrationsPage';
import { AdminJobsPage } from '../pages/admin/AdminJobsPage';
import { AdminSupportPage } from '../pages/admin/AdminSupportPage';
import { AdminAuditLogsPage } from '../pages/admin/AdminAuditLogsPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Marketing Website */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/trust" element={<TrustPage />} />
        <Route path="/free-consultation" element={<FreeConsultationPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/agency/signup" element={<AgencySignupPage />} />
        <Route path="/agency/login" element={<LoginPage />} />
        <Route path="/agency/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/consultant/signup" element={<ConsultantSignupPage />} />
        <Route path="/consultant/login" element={<LoginPage />} />
        <Route path="/consultant/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/invite" element={<InviteAcceptPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Legacy route redirects to consolidated destinations */}
        <Route path="/features" element={<Navigate to="/#catalogue" replace />} />
        <Route path="/pricing" element={<Navigate to="/free-consultation" replace />} />
        <Route path="/contact" element={<Navigate to="/free-consultation" replace />} />
        <Route path="/book-demo" element={<Navigate to="/free-consultation" replace />} />
      </Route>

      {/* Authenticated Seller Workspace */}
      <Route
        path="/app"
        element={
          <AuthGuard allowedAccountTypes={['company', 'admin']}>
            <AppLayout />
          </AuthGuard>
        }
      >
        <Route index element={<Navigate to="/app/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="brand" element={<BrandProfilePage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="products/new" element={<AddProductPage />} />
        <Route path="products/:id" element={<ProductDetailPage />} />
        <Route path="ai-studio" element={<AIStudioPage />} />
        <Route path="integrations" element={<IntegrationsPage />} />
        <Route path="publishing" element={<PublishingPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="marketing" element={<MarketingPage />} />
        <Route path="campaigns" element={<MarketingPage />} />
        <Route path="campaigns/:id" element={<CampaignDetailPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="billing" element={<BillingPage />} />
        <Route path="agency-connect" element={<AgencyConnectPage />} />
        <Route path="agency-portal" element={<AgencyPortalPage />} />
        <Route path="team" element={<TeamPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="help" element={<HelpPage />} />
      </Route>

      {/* Isolated Agency Portal */}
      <Route
        path="/agency/portal"
        element={
          <AuthGuard allowedAccountTypes={['agency', 'admin']}>
            <AgencyPortalPage />
          </AuthGuard>
        }
      />

      {/* Restricted Consultant Advisory Workspace */}
      <Route
        path="/consultant"
        element={
          <AuthGuard allowedAccountTypes={['consultant', 'admin']}>
            <ConsultantPortalPage />
          </AuthGuard>
        }
      />
      <Route
        path="/consultant/*"
        element={
          <AuthGuard allowedAccountTypes={['consultant', 'admin']}>
            <ConsultantPortalPage />
          </AuthGuard>
        }
      />

      {/* Internal Operator Console */}
      <Route
        path="/admin"
        element={
          <AuthGuard requirePlatformAdmin={true} allowedAccountTypes={['admin']}>
            <AdminLayout />
          </AuthGuard>
        }
      >
        <Route index element={<AdminDashboardPage />} />
        <Route path="organizations" element={<AdminOrgsPage />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="plans" element={<AdminPlansPage />} />
        <Route path="agencies" element={<AdminAgenciesPage />} />
        <Route path="integrations" element={<AdminIntegrationsPage />} />
        <Route path="jobs" element={<AdminJobsPage />} />
        <Route path="support" element={<AdminSupportPage />} />
        <Route path="services" element={<AdminSupportPage />} />
        <Route path="audit-logs" element={<AdminAuditLogsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

