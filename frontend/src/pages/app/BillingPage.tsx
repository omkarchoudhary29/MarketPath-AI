import React, { useEffect, useState } from 'react';
import {
  CreditCard,
  CheckCircle2,
  Download,
  Sparkles,
  ShieldCheck,
  Building2,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  Clock,
  Layers,
  ChevronRight,
  Check,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import { Modal } from '../../components/ui/Modal';

interface Plan {
  id: string;
  name: string;
  monthly_price_inr: number;
  max_active_skus: number;
  max_connected_channels: number;
  ai_generation_monthly_quota: number;
  description: string;
  features?: Record<string, boolean>;
}

interface Subscription {
  id: string;
  organization_id: string;
  plan_id: string;
  status: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  gateway_subscription_id?: string;
  plan: Plan;
}

interface UsageMeterItem {
  metric: string;
  label: string;
  used: number;
  limit: number;
  percentage: number;
  unit: string;
}

interface UsageStats {
  plan_name: string;
  period_start: string;
  period_end: string;
  active_skus: UsageMeterItem;
  connected_channels: UsageMeterItem;
  ai_generations: UsageMeterItem;
  publishing_jobs: UsageMeterItem;
}

interface ServiceCatalogItem {
  id: string;
  service_type: string;
  name: string;
  short_description: string;
  scope_bullets: string[];
  starting_price_inr: number;
  deliverable_timeline: string;
  recommended_for: string;
}

interface ServiceOrder {
  id: string;
  service_type: string;
  scope_description: string;
  quoted_price_inr: number;
  status: string;
  deliverables_notes?: string;
  due_date?: string;
  created_at: string;
}

interface PaymentTransaction {
  id: string;
  amount_inr: number;
  currency: string;
  gateway: string;
  gateway_payment_id: string;
  status: string;
  receipt_url?: string;
  created_at: string;
}

export const BillingPage: React.FC = () => {
  const { session, activeOrg } = useAuth();
  const { addToast } = useApp();

  const token = session?.access_token;
  const orgId = activeOrg?.id;

  const [isLoading, setIsLoading] = useState(true);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [servicesCatalog, setServicesCatalog] = useState<ServiceCatalogItem[]>([]);
  const [serviceOrders, setServiceOrders] = useState<ServiceOrder[]>([]);
  const [payments, setPayments] = useState<PaymentTransaction[]>([]);

  // Upgrade Modal
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [isProcessingUpgrade, setIsProcessingUpgrade] = useState(false);

  // Managed Service Order Modal
  const [selectedService, setSelectedService] = useState<ServiceCatalogItem | null>(null);
  const [serviceScope, setServiceScope] = useState('');
  const [serviceBudget, setServiceBudget] = useState<number>(2999);
  const [isSubmittingService, setIsSubmittingService] = useState(false);

  const fetchBillingData = async () => {
    if (!token || !orgId) return;
    setIsLoading(true);
    try {
      const [pList, sub, uStats, sCatalog, sOrders, pmtList] = await Promise.all([
        apiClient<Plan[]>('/api/v1/billing/plans', { token, organizationId: orgId }),
        apiClient<Subscription>('/api/v1/billing/subscription', { token, organizationId: orgId }),
        apiClient<UsageStats>('/api/v1/billing/usage', { token, organizationId: orgId }),
        apiClient<ServiceCatalogItem[]>('/api/v1/services/catalog', { token, organizationId: orgId }),
        apiClient<ServiceOrder[]>('/api/v1/services/orders', { token, organizationId: orgId }),
        apiClient<PaymentTransaction[]>('/api/v1/billing/payments', { token, organizationId: orgId }),
      ]);

      setPlans(pList);
      setSubscription(sub);
      setUsage(uStats);
      setServicesCatalog(sCatalog);
      setServiceOrders(sOrders);
      setPayments(pmtList);
    } catch (err: any) {
      console.error('Failed to load billing data:', err);
      addToast({
        type: 'error',
        title: 'Billing Sync Error',
        message: err.message || 'Could not retrieve subscription details.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBillingData();
  }, [token, orgId]);

  const handleUpgradePlan = async (targetPlan: Plan) => {
    if (!token || !orgId) return;
    setIsProcessingUpgrade(true);
    try {
      // 1. Create checkout order on backend
      const checkoutRes = await apiClient<{
        order_id: string;
        amount_inr: number;
        currency: string;
        plan_name: string;
      }>('/api/v1/billing/checkout', {
        method: 'POST',
        token,
        organizationId: orgId,
        body: JSON.stringify({
          plan_id: targetPlan.id,
          gateway: 'razorpay',
        }),
      });

      // 2. In local test environment: verify signature with server
      const verifyRes = await apiClient<Subscription>('/api/v1/billing/verify', {
        method: 'POST',
        token,
        organizationId: orgId,
        body: JSON.stringify({
          gateway: 'razorpay',
          order_id: checkoutRes.order_id,
          payment_id: `pay_${Math.random().toString(36).substring(2, 10)}`,
          signature: 'sig_test_verified_12345',
          plan_id: targetPlan.id,
        }),
      });

      setSubscription(verifyRes);
      setShowUpgradeModal(false);
      addToast({
        type: 'success',
        title: 'Plan Activated',
        message: `Successfully upgraded to the ${targetPlan.name} tier (₹${targetPlan.monthly_price_inr}/month).`,
      });
      fetchBillingData();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Upgrade Failed',
        message: err.message || 'Payment verification failed.',
      });
    } finally {
      setIsProcessingUpgrade(false);
    }
  };

  const handleCreateServiceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedService || !token || !orgId) return;
    setIsSubmittingService(true);
    try {
      const res = await apiClient<ServiceOrder>('/api/v1/services/orders', {
        method: 'POST',
        token,
        organizationId: orgId,
        body: JSON.stringify({
          service_type: selectedService.service_type,
          scope_description: serviceScope,
          target_budget_inr: Number(serviceBudget),
        }),
      });

      setServiceOrders([res, ...serviceOrders]);
      setSelectedService(null);
      setServiceScope('');
      addToast({
        type: 'success',
        title: 'Service Request Submitted',
        message: 'A MarketPath operations specialist in Pune will review your deliverables and schedule execution.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Request Error',
        message: err.message || 'Failed to submit service order.',
      });
    } finally {
      setIsSubmittingService(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600">
            Subscription & Resource Entitlements
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-0.5">
            Billing & Usage Quotas
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Manage your SaaS tier, track active SKU quotas, and request optional managed growth services.
          </p>
        </div>

        <button
          onClick={() => setShowUpgradeModal(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-xs cursor-pointer self-start sm:self-auto transition-colors"
        >
          Change Plan / Upgrade
        </button>
      </div>

      {isLoading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-brand-600 animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-600">Retrieving active subscription and quota meters...</p>
        </div>
      ) : (
        <>
          {/* Active Plan & Meter Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            {/* Active Subscription Card */}
            <div className="p-6 rounded-3xl bg-white border-2 border-brand-500/80 shadow-xs relative space-y-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-700 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200">
                Active Subscription
              </span>
              <div>
                <h3 className="text-xl font-extrabold text-charcoal">
                  {subscription?.plan?.name || 'Growth'} Plan
                </h3>
                <div className="text-2xl font-bold text-charcoal mt-1">
                  ₹{(subscription?.plan?.monthly_price_inr || 2499).toLocaleString()}{' '}
                  <span className="text-xs text-slate-500 font-normal">/ month</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Renews {subscription?.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'Monthly'} via Razorpay.
                </p>
              </div>
              <div className="pt-2 text-xs text-emerald-700 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Good Standing
              </div>
            </div>

            {/* Quota Meter 1: Master SKUs */}
            <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-2xs space-y-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Master Active SKUs
              </span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-extrabold text-charcoal">
                  {usage?.active_skus?.used || 0} / {usage?.active_skus?.limit || 100}
                </span>
                <span className="text-xs font-bold text-brand-600">
                  {usage?.active_skus?.percentage || 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-600 rounded-full transition-all"
                  style={{ width: `${Math.min(100, usage?.active_skus?.percentage || 0)}%` }}
                />
              </div>
              <span className="text-[11px] text-slate-400 block pt-1">
                {(usage?.active_skus?.limit || 100) - (usage?.active_skus?.used || 0)} slots available.
              </span>
            </div>

            {/* Quota Meter 2: Connected Channels */}
            <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-2xs space-y-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Connected Channels
              </span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-extrabold text-charcoal">
                  {usage?.connected_channels?.used || 0} / {usage?.connected_channels?.limit || 3}
                </span>
                <span className="text-xs font-bold text-emerald-600">
                  {usage?.connected_channels?.percentage || 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-600 rounded-full transition-all"
                  style={{ width: `${Math.min(100, usage?.connected_channels?.percentage || 0)}%` }}
                />
              </div>
              <span className="text-[11px] text-slate-400 block pt-1">
                {(usage?.connected_channels?.limit || 3) - (usage?.connected_channels?.used || 0)} channels remaining.
              </span>
            </div>

            {/* Quota Meter 3: AI Studio Generations */}
            <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-2xs space-y-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                AI Studio Generations
              </span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-extrabold text-charcoal">
                  {usage?.ai_generations?.used || 0} / {usage?.ai_generations?.limit || 500}
                </span>
                <span className="text-xs font-bold text-amber-600">
                  {usage?.ai_generations?.percentage || 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full transition-all"
                  style={{ width: `${Math.min(100, usage?.ai_generations?.percentage || 0)}%` }}
                />
              </div>
              <span className="text-[11px] text-slate-400 block pt-1">
                Resets on billing period renewal.
              </span>
            </div>
          </div>

          {/* Managed Services Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-brand-600">
                  Hybrid Operational Services
                </span>
                <h2 className="text-lg font-bold text-charcoal mt-0.5">
                  Optional Managed Growth Services
                </h2>
                <p className="text-xs text-slate-500">
                  Fixed-fee professional execution from our dedicated D2C onboarding specialists in Pune. Service fees are completely separate from advertising media spend.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {servicesCatalog.map((service) => (
                <div
                  key={service.id}
                  className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-2xs flex flex-col justify-between space-y-4 hover:border-brand-300 transition-colors"
                >
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-2 py-0.5 rounded">
                      {service.deliverable_timeline}
                    </span>
                    <h3 className="text-sm font-bold text-charcoal">{service.name}</h3>
                    <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed">
                      {service.short_description}
                    </p>
                    <ul className="space-y-1 pt-2">
                      {service.scope_bullets.slice(0, 3).map((bullet, idx) => (
                        <li key={idx} className="text-[11px] text-slate-600 flex items-start gap-1.5">
                          <Check className="w-3.5 h-3.5 text-brand-600 shrink-0 mt-0.5" />
                          <span>{bullet}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 block">Starting from</span>
                      <span className="text-base font-extrabold text-charcoal">
                        ₹{service.starting_price_inr.toLocaleString()}
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedService(service);
                        setServiceBudget(service.starting_price_inr);
                      }}
                      className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-brand-600 text-white font-bold text-xs shadow-xs cursor-pointer transition-colors"
                    >
                      Request Service
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Service Requests & Invoices Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Active Service Requests */}
            <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-2xs space-y-4">
              <h3 className="text-sm font-bold text-charcoal">Your Managed Service Orders</h3>
              {serviceOrders.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs">
                  No managed service requests submitted yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {serviceOrders.map((ord) => (
                    <div
                      key={ord.id}
                      className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-bold text-charcoal block capitalize">
                          {ord.service_type.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[11px] text-slate-500 font-mono">
                          ₹{ord.quoted_price_inr.toLocaleString()} • Requested {new Date(ord.created_at).toLocaleDateString()}
                        </span>
                        {ord.deliverables_notes && (
                          <p className="text-[11px] text-brand-700 mt-1 italic">
                            Note: {ord.deliverables_notes}
                          </p>
                        )}
                      </div>
                      <span
                        className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          ord.status === 'completed'
                            ? 'bg-emerald-100 text-emerald-800'
                            : ord.status === 'in_progress'
                            ? 'bg-sky-100 text-sky-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {ord.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Payment & Invoice Receipts */}
            <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-2xs space-y-4">
              <h3 className="text-sm font-bold text-charcoal">Payment Transactions & Receipts</h3>
              {payments.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs">
                  No payment transactions recorded yet.
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {payments.map((pmt) => (
                    <div key={pmt.id} className="py-3 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-bold text-charcoal block">
                          ₹{pmt.amount_inr.toLocaleString()} {pmt.currency}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400">
                          {pmt.gateway.toUpperCase()} • ID: {pmt.gateway_payment_id.slice(-8)} • {new Date(pmt.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        {pmt.status.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Plan Upgrade Modal */}
      <Modal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        title="Choose a Subscription Plan"
        maxWidth="2xl"
      >
        <div className="space-y-6">
          <p className="text-xs text-slate-500">
            Select the growth tier that best fits your active SKU count and connected sales channel needs.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {plans.map((p) => {
              const isCurrent = subscription?.plan?.name === p.name;
              return (
                <div
                  key={p.id}
                  className={`p-5 rounded-2xl border-2 flex flex-col justify-between space-y-4 ${
                    isCurrent ? 'border-brand-500 bg-brand-50/20' : 'border-slate-200 bg-white'
                  }`}
                >
                  <div className="space-y-2">
                    {isCurrent && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-brand-700 bg-brand-100 px-2 py-0.5 rounded">
                        Current Plan
                      </span>
                    )}
                    <h4 className="text-base font-extrabold text-charcoal">{p.name}</h4>
                    <div className="text-2xl font-black text-charcoal">
                      ₹{p.monthly_price_inr.toLocaleString()}{' '}
                      <span className="text-xs font-normal text-slate-400">/ mo</span>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">{p.description}</p>
                    <ul className="space-y-1.5 pt-2 text-xs text-slate-600">
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600" />
                        <span>Up to <strong>{p.max_active_skus}</strong> Active SKUs</span>
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600" />
                        <span>Up to <strong>{p.max_connected_channels}</strong> Channels</span>
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600" />
                        <span><strong>{p.ai_generation_monthly_quota}</strong> AI Credits / mo</span>
                      </li>
                    </ul>
                  </div>

                  <button
                    onClick={() => handleUpgradePlan(p)}
                    disabled={isCurrent || isProcessingUpgrade}
                    className={`w-full py-2.5 rounded-xl font-bold text-xs shadow-xs cursor-pointer transition-colors ${
                      isCurrent
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        : 'bg-brand-600 hover:bg-brand-700 text-white'
                    }`}
                  >
                    {isProcessingUpgrade ? 'Processing...' : isCurrent ? 'Active Tier' : 'Select Plan'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </Modal>

      {/* Managed Service Request Modal */}
      <Modal
        isOpen={Boolean(selectedService)}
        onClose={() => setSelectedService(null)}
        title={`Request: ${selectedService?.name}`}
        maxWidth="lg"
      >
        {selectedService && (
          <form onSubmit={handleCreateServiceOrder} className="space-y-4">
            <p className="text-xs text-slate-500">
              Submit your project brief. A dedicated operator will contact you via email to review deliverables.
            </p>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Project Scope & Requirements
              </label>
              <textarea
                value={serviceScope}
                onChange={(e) => setServiceScope(e.target.value)}
                required
                rows={4}
                placeholder="Describe your current store setup, product catalogue size, and specific deliverables needed..."
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-brand-600"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Target Budget (INR)
              </label>
              <input
                type="number"
                value={serviceBudget}
                onChange={(e) => setServiceBudget(Number(e.target.value))}
                min={selectedService.starting_price_inr}
                required
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-semibold focus:outline-brand-600"
              />
              <span className="text-[10px] text-slate-400 block mt-1">
                Base price starting from ₹{selectedService.starting_price_inr.toLocaleString()}
              </span>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setSelectedService(null)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmittingService || !serviceScope.trim()}
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-xs cursor-pointer disabled:opacity-50"
              >
                {isSubmittingService ? 'Submitting...' : 'Confirm Request'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};
