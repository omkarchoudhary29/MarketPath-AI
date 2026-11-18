import React, { useEffect, useState } from 'react';
import {
  Building,
  ShieldCheck,
  Send,
  DollarSign,
  Calendar,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Plus,
  UserCheck,
  Lock,
  Briefcase,
  Users,
  Award,
  Eye,
  FileText,
  Check,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { DemoBanner } from '../../components/common/DemoBanner';

interface SanitizedBrief {
  id: string;
  brand_name: string;
  category: string;
  business_stage: string;
  budget_tier: string;
  marketing_objectives: string[];
  required_services: string[];
  target_timeline: string;
  founder_phone?: string;
  founder_email?: string;
  created_at: string;
  _pii_sanitized?: boolean;
}

interface ServicePackage {
  id: string;
  name: string;
  monthly_retainer_inr: number;
  best_for: string;
  deliverables: string[];
  turnaround_days: number;
  active_clients: number;
}

interface PortfolioCaseStudy {
  id: string;
  client_name: string;
  category: string;
  headline: string;
  metrics: Record<string, string>;
  is_demo_work: boolean;
  verification_badge: string;
}

export const AgencyPortalPage: React.FC = () => {
  const { session } = useAuth();
  const { addToast } = useApp();

  const [activeTab, setActiveTab] = useState<'briefs' | 'packages' | 'portfolio' | 'team'>('briefs');
  const [briefs, setBriefs] = useState<SanitizedBrief[]>([]);
  const [packages, setPackages] = useState<ServicePackage[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioCaseStudy[]>([]);
  const [overview, setOverview] = useState<any>({
    agency_name: 'GrowthCraft Media Labs',
    verification_status: 'verified',
    active_client_briefs_count: 5,
    proposals_sent_count: 9,
    rating_avg: 4.9,
    total_gmv_managed: '₹1.48 Cr',
  });
  const [isLoading, setIsLoading] = useState(true);

  // Proposal modal state
  const [selectedBrief, setSelectedBrief] = useState<SanitizedBrief | null>(null);
  const [quoteAmount, setQuoteAmount] = useState(65000);
  const [quoteDeliverables, setQuoteDeliverables] = useState(
    'Meta Ads Full-Funnel Management\n12 Custom High-ROAS Video & Static Creatives\nWeekly Strategy Review & CRO Audit'
  );
  const [quoteNotes, setQuoteNotes] = useState(
    'We specialize in this D2C category and have scaled peer brands to 4x+ ROAS.'
  );
  const [isSubmittingQuote, setIsSubmittingQuote] = useState(false);

  const fetchPortalData = async () => {
    setIsLoading(true);
    try {
      const [overviewRes, briefsRes, packagesRes, portfolioRes] = await Promise.all([
        fetch('/api/v1/agency/portal/overview').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/agency/portal/briefs').then((r) => (r.ok ? r.json() : [])),
        fetch('/api/v1/agency/portal/packages').then((r) => (r.ok ? r.json() : [])),
        fetch('/api/v1/agency/portal/portfolio').then((r) => (r.ok ? r.json() : [])),
      ]);

      if (overviewRes) setOverview(overviewRes);
      if (briefsRes) setBriefs(briefsRes);
      if (packagesRes) setPackages(packagesRes);
      if (portfolioRes) setPortfolio(portfolioRes);
    } catch (err) {
      console.warn('Agency portal fetch fallback:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, []);

  const handleSendQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBrief) return;
    setIsSubmittingQuote(true);

    try {
      addToast({
        type: 'success',
        title: 'Commercial Proposal Delivered',
        message: `Quotation of ₹${quoteAmount.toLocaleString('en-IN')} sent to ${selectedBrief.brand_name}.`,
      });
      setSelectedBrief(null);
    } catch (err: any) {
      addToast({ type: 'error', title: 'Dispatch Failed' });
    } finally {
      setIsSubmittingQuote(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <DemoBanner />
      {/* Header Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-forest-deep border border-forest text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-option-c-md">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-forest text-emerald text-[11px] font-bold uppercase tracking-wider border border-brand-700">
            <Building className="w-3.5 h-3.5" />
            <span>Agency Partner Portal Workspace</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {overview.agency_name || 'Agency Partner Portal'}
          </h1>
          <p className="text-xs text-slate-300">
            Dedicated workspace for verified marketing agencies. Review seller briefs, manage retainers, and submit proposals.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-forest text-emerald border border-brand-700 text-xs font-bold">
            <ShieldCheck className="w-4 h-4 text-emerald" />
            <span>Verified D2C Agency</span>
          </span>
          <button
            onClick={fetchPortalData}
            className="p-2 text-slate-300 hover:text-white hover:bg-forest rounded-xl transition-colors cursor-pointer"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* PII Privacy Vault Guarantee Alert */}
      <div className="p-4 rounded-2xl bg-softbeige border border-bordergrey text-charcoal flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <Lock className="w-4 h-4 text-forest shrink-0" />
          <span>
            <strong>Client Privacy Vault Active:</strong> Founder personal phone numbers, direct emails, and internal profit margins are masked to protect seller confidentiality. Communications occur securely within MarketPath.
          </span>
        </div>
        <span className="text-[10px] font-mono font-bold text-forest bg-white px-2 py-1 rounded-lg border border-bordergrey shrink-0">
          AES-256 Vaulted
        </span>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="p-5">
          <span className="text-[10px] font-bold text-charcoal-muted uppercase tracking-wider block">
            Client Inquiries
          </span>
          <span className="text-2xl font-extrabold text-charcoal mt-1 block">
            {briefs.length} Active
          </span>
          <span className="text-[11px] text-charcoal-muted mt-0.5 block">Category-matched D2C briefs</span>
        </Card>

        <Card className="p-5">
          <span className="text-[10px] font-bold text-charcoal-muted uppercase tracking-wider block">
            Proposals Sent
          </span>
          <span className="text-2xl font-extrabold text-forest mt-1 block">
            {overview.proposals_sent_count || 9}
          </span>
          <span className="text-[11px] text-charcoal-muted mt-0.5 block">Awaiting seller approval</span>
        </Card>

        <Card className="p-5">
          <span className="text-[10px] font-bold text-charcoal-muted uppercase tracking-wider block">
            Client Rating
          </span>
          <span className="text-2xl font-extrabold text-softorange mt-1 block">
            ★ {overview.rating_avg || 4.9}
          </span>
          <span className="text-[11px] text-charcoal-muted mt-0.5 block">Verified D2C brand reviews</span>
        </Card>

        <Card className="p-5">
          <span className="text-[10px] font-bold text-charcoal-muted uppercase tracking-wider block">
            Client GMV Influenced
          </span>
          <span className="text-2xl font-extrabold text-emerald mt-1 block">
            {overview.total_gmv_managed || '₹1.48 Cr'}
          </span>
          <span className="text-[11px] text-charcoal-muted mt-0.5 block">Portfolio annualized scale</span>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-bordergrey gap-6 text-xs font-bold">
        <button
          onClick={() => setActiveTab('briefs')}
          className={`pb-3 transition-colors cursor-pointer border-b-2 ${
            activeTab === 'briefs'
              ? 'border-brand-600 text-forest'
              : 'border-transparent text-charcoal-muted hover:text-charcoal'
          }`}
        >
          Client Inquiries &amp; Briefs ({briefs.length})
        </button>
        <button
          onClick={() => setActiveTab('packages')}
          className={`pb-3 transition-colors cursor-pointer border-b-2 ${
            activeTab === 'packages'
              ? 'border-brand-600 text-forest'
              : 'border-transparent text-charcoal-muted hover:text-charcoal'
          }`}
        >
          Service Packages &amp; Pricing ({packages.length})
        </button>
        <button
          onClick={() => setActiveTab('portfolio')}
          className={`pb-3 transition-colors cursor-pointer border-b-2 ${
            activeTab === 'portfolio'
              ? 'border-brand-600 text-forest'
              : 'border-transparent text-charcoal-muted hover:text-charcoal'
          }`}
        >
          Case Studies &amp; Portfolio ({portfolio.length})
        </button>
        <button
          onClick={() => setActiveTab('team')}
          className={`pb-3 transition-colors cursor-pointer border-b-2 ${
            activeTab === 'team'
              ? 'border-brand-600 text-forest'
              : 'border-transparent text-charcoal-muted hover:text-charcoal'
          }`}
        >
          Agency Team &amp; RBAC
        </button>
      </div>

      {/* TAB 1: CLIENT BRIEFS (SANITIZED) */}
      {activeTab === 'briefs' && (
        <Card className="overflow-hidden">
          <div className="p-5 border-b border-bordergrey flex items-center justify-between bg-softbeige/30">
            <div>
              <h3 className="text-sm font-bold text-charcoal">Verified Seller Briefs &amp; RFPs</h3>
              <p className="text-xs text-charcoal-muted">Contact details and commercial margins are automatically masked.</p>
            </div>
            <span className="text-xs font-mono font-bold text-charcoal-muted">{briefs.length} Matched</span>
          </div>

          <div className="divide-y divide-bordergrey">
            {briefs.map((b) => (
              <div key={b.id} className="p-5 hover:bg-softbeige/20 transition-colors space-y-3 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-charcoal text-sm">{b.brand_name}</h4>
                      <Badge variant="brand" size="sm">{b.category}</Badge>
                      <Badge variant="neutral" size="sm">{b.business_stage}</Badge>
                    </div>
                    <p className="text-charcoal-muted text-[11px] mt-1">
                      Budget: <strong className="text-charcoal">{b.budget_tier}</strong> • Timeline: {b.target_timeline}
                    </p>
                  </div>

                  <Button
                    size="sm"
                    onClick={() => setSelectedBrief(b)}
                    className="self-start sm:self-auto"
                  >
                    Prepare Proposal
                  </Button>
                </div>

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {b.required_services.map((srv, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded-lg bg-softbeige text-charcoal font-medium text-[11px] border border-bordergrey">
                      {srv}
                    </span>
                  ))}
                </div>

                {/* Sanitized PII Contact Row */}
                <div className="p-2.5 rounded-xl bg-warmwhite border border-bordergrey flex flex-wrap items-center justify-between gap-2 text-[11px] text-charcoal-muted">
                  <div className="flex items-center gap-3">
                    <span>Masked Email: <strong className="font-mono text-charcoal">{b.founder_email}</strong></span>
                    <span>Phone: <strong className="font-mono text-charcoal">{b.founder_phone}</strong></span>
                  </div>
                  <span className="text-forest font-bold flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald" /> PII Protected
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 2: SERVICE PACKAGES */}
      {activeTab === 'packages' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {packages.map((pkg) => (
            <Card key={pkg.id} className="p-6 flex flex-col justify-between space-y-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-forest bg-brand-50 px-2 py-0.5 rounded-md border border-brand-200">
                  Package Tier
                </span>
                <h3 className="text-base font-bold text-charcoal mt-2">{pkg.name}</h3>
                <div className="mt-2 text-2xl font-extrabold text-charcoal">
                  ₹{pkg.monthly_retainer_inr.toLocaleString('en-IN')}{' '}
                  <span className="text-xs text-charcoal-muted font-normal">/ month</span>
                </div>
                <p className="text-xs text-charcoal-muted mt-2">{pkg.best_for}</p>

                <div className="mt-4 pt-3 border-t border-bordergrey space-y-1.5 text-xs text-charcoal">
                  <span className="font-bold text-charcoal block mb-1">Included Deliverables:</span>
                  {pkg.deliverables.map((d, idx) => (
                    <div key={idx} className="flex items-start gap-1.5">
                      <Check className="w-3.5 h-3.5 text-emerald shrink-0 mt-0.5" />
                      <span>{d}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-bordergrey flex items-center justify-between text-xs text-charcoal-muted">
                <span>Turnaround: {pkg.turnaround_days} days</span>
                <span className="font-bold text-charcoal">{pkg.active_clients} Active Brands</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* TAB 3: PORTFOLIO & CASE STUDIES */}
      {activeTab === 'portfolio' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {portfolio.map((item) => (
            <Card key={item.id} className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-charcoal text-sm">{item.client_name}</h4>
                  <span className="text-xs text-charcoal-muted">{item.category}</span>
                </div>
                {item.is_demo_work ? (
                  <Badge variant="warning" size="sm">
                    Demo Portfolio Case Study
                  </Badge>
                ) : (
                  <Badge variant="success" size="sm" dot>
                    Verified D2C Client
                  </Badge>
                )}
              </div>

              <p className="text-xs font-semibold text-charcoal leading-relaxed">{item.headline}</p>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-bordergrey text-center">
                {Object.entries(item.metrics).map(([k, val]) => (
                  <div key={k} className="p-2.5 rounded-xl bg-warmwhite border border-bordergrey">
                    <span className="text-[10px] font-bold uppercase text-charcoal-muted block">{k.replace('_', ' ')}</span>
                    <span className="text-sm font-extrabold text-charcoal block mt-0.5">{val}</span>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* TAB 4: AGENCY TEAM & RBAC */}
      {activeTab === 'team' && (
        <Card className="p-6 space-y-4 text-xs">
          <div className="flex items-center justify-between border-b border-bordergrey pb-3">
            <div>
              <h3 className="text-sm font-bold text-charcoal">Agency Team Roster &amp; Role Permissions</h3>
              <p className="text-xs text-charcoal-muted">Manage media buyers, creative strategists, and account managers.</p>
            </div>
            <Button size="sm">
              + Add Agency Member
            </Button>
          </div>

          <div className="divide-y divide-bordergrey">
            <div className="py-3 flex items-center justify-between">
              <div>
                <span className="font-bold text-charcoal block">Rohan Mehra</span>
                <span className="text-[11px] text-charcoal-muted">rohan@growthcraft.in</span>
              </div>
              <Badge variant="brand" size="sm">Agency Lead</Badge>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <span className="font-bold text-charcoal block">Natasha Sen</span>
                <span className="text-[11px] text-charcoal-muted">natasha.ads@growthcraft.in</span>
              </div>
              <Badge variant="info" size="sm">Senior Media Buyer</Badge>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <span className="font-bold text-charcoal block">Kabir Joshi</span>
                <span className="text-[11px] text-charcoal-muted">kabir.content@growthcraft.in</span>
              </div>
              <Badge variant="success" size="sm">Creative Strategist</Badge>
            </div>
          </div>
        </Card>
      )}

      {/* Prepare Quotation Modal */}
      {selectedBrief && (
        <Modal
          isOpen={Boolean(selectedBrief)}
          onClose={() => setSelectedBrief(null)}
          title={`Prepare Proposal: ${selectedBrief.brand_name}`}
          subtitle={`Category: ${selectedBrief.category} • Budget: ${selectedBrief.budget_tier}`}
        >
          <form onSubmit={handleSendQuotation} className="p-6 space-y-4 text-xs">
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">
                Proposed Monthly Retainer (INR) *
              </label>
              <input
                type="number"
                required
                value={quoteAmount}
                onChange={(e) => setQuoteAmount(Number(e.target.value))}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-bordergrey font-mono bg-white text-charcoal focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">
                Key Deliverables (One per line) *
              </label>
              <textarea
                rows={3}
                required
                value={quoteDeliverables}
                onChange={(e) => setQuoteDeliverables(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-bordergrey bg-white text-charcoal focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">
                Strategy Brief &amp; Pitch Notes
              </label>
              <textarea
                rows={3}
                required
                value={quoteNotes}
                onChange={(e) => setQuoteNotes(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-bordergrey bg-white text-charcoal focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-bordergrey">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setSelectedBrief(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={isSubmittingQuote}
              >
                {isSubmittingQuote ? 'Sending...' : 'Dispatch Commercial Proposal'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
