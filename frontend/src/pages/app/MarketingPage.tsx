import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { apiClient } from '../../lib/api';
import {
  Megaphone,
  Plus,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Download,
  ShieldCheck,
  Pause,
  Play,
  ArrowRight,
  Calendar,
  Layers,
  Target,
  DollarSign,
  TrendingUp,
  BarChart2,
  Copy,
  Check,
  Info,
} from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Campaign, CampaignCreative } from '../../types';

export const MarketingPage: React.FC = () => {
  const { campaigns, addCampaign, approveCampaignBudget, pauseCampaign, products, addToast } = useApp();
  const { session, activeOrg, role } = useAuth();
  const token = session?.access_token;

  const [campaignList, setCampaignList] = useState<Campaign[]>(campaigns);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterChannel, setFilterChannel] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3 | 4>(1);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [generatedProposal, setGeneratedProposal] = useState<any | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    objective: 'sales' as 'sales' | 'traffic' | 'awareness' | 'leads' | 'engagement',
    channel: 'meta_ads' as 'meta_ads' | 'google_ads',
    selectedProductId: products[0]?.id || '',
    targetGeography: 'Pan-India (Tier 1 Metros)',
    targetAudienceBrief: 'Design-conscious urban Indian consumers seeking sustainable artisanal home goods.',
    naturalLanguageBrief: '',
    totalBudget: 12000,
    dailyBudgetLimit: 800,
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0],
    landingPageUrl: 'https://auraterra.in/collections/artisanal',
    callToAction: 'Shop Now',
    creativeFormat: 'feed_image',
    headline: 'Handcrafted Stoneware for Mindful Mornings',
    primaryText: 'Slow down and savor your daily ritual with authentic artisan-made ceramic mugs crafted patiently in Pune.',
  });

  // Overview Statistics
  const totalCampaigns = campaignList.length;
  const activeCampaigns = campaignList.filter((c) => c.status === 'active').length;
  const readyCampaigns = campaignList.filter((c) => c.status === 'ready_for_manual_setup' || c.status === 'approved').length;
  const totalBudgetSum = campaignList.reduce((acc, c) => acc + (c.totalBudget || 0), 0);
  const totalSpendSum = campaignList.reduce((acc, c) => acc + (c.metrics?.spend || 0), 0);

  // Fetch campaigns from backend API if authenticated
  useEffect(() => {
    async function loadBackendCampaigns() {
      if (token && activeOrg?.id) {
        try {
          const remoteCampaigns = await apiClient<any[]>('/api/v1/campaigns', {
            token,
            organizationId: activeOrg.id,
          });
          if (Array.isArray(remoteCampaigns) && remoteCampaigns.length > 0) {
            const mapped: Campaign[] = remoteCampaigns.map((rc) => ({
              id: rc.id,
              name: rc.name,
              objective: rc.objective,
              totalBudget: rc.total_budget,
              dailyBudgetLimit: rc.daily_budget_limit,
              currency: rc.currency,
              startDate: rc.start_date,
              endDate: rc.end_date,
              status: rc.status === 'ready_for_manual_setup' ? 'ready_for_manual_setup' : (rc.status as any),
              channel: rc.channel,
              productId: rc.product_id,
              product: rc.product,
              targetGeography: rc.target_geography,
              creatives: (rc.creatives || []).map((cr: any) => ({
                id: cr.id,
                headline: cr.headline,
                primaryText: cr.primary_text,
                ctaText: cr.cta_text,
                mediaUrl: cr.media_url,
                destinationUrl: cr.destination_url,
              })),
              metrics: rc.performance_summary ? {
                spend: rc.performance_summary.total_spend,
                impressions: rc.performance_summary.total_impressions,
                clicks: rc.performance_summary.total_clicks,
                conversions: rc.performance_summary.total_conversions,
                roas: rc.performance_summary.blended_roas,
              } : undefined,
            }));
            setCampaignList(mapped);
          }
        } catch {
          // Keep local fallback
        }
      }
    }
    loadBackendCampaigns();
  }, [token, activeOrg]);

  // Handle AI Planning via Gemini
  const handleGenerateAIPlan = async () => {
    setIsGeneratingPlan(true);
    try {
      if (token && activeOrg?.id) {
        const plan = await apiClient<any>('/api/v1/campaigns/plan', {
          method: 'POST',
          token,
          organizationId: activeOrg.id,
          body: JSON.stringify({
            natural_language_brief: formData.naturalLanguageBrief || `Promote ${products.find((p) => p.id === formData.selectedProductId)?.title || 'Artisanal collection'} across ${formData.targetGeography}.`,
            product_id: formData.selectedProductId || undefined,
            objective: formData.objective,
            target_geography: formData.targetGeography,
            monthly_budget_inr: Number(formData.totalBudget),
            duration_days: 30,
            channel: formData.channel,
          }),
        });
        setGeneratedProposal(plan);
        if (plan.ad_headlines?.[0]) {
          setFormData((prev) => ({
            ...prev,
            headline: plan.ad_headlines[0],
            primaryText: plan.primary_texts?.[0] || prev.primaryText,
          }));
        }
      } else {
        // Local simulation fallback
        await new Promise((r) => setTimeout(r, 800));
        setGeneratedProposal({
          strategy_summary: `3-Stage Acquisition Sprint for ${formData.name || 'Artisanal Goods'} targeting urban conscious consumers in ${formData.targetGeography}.`,
          suggested_channel: 'Meta Ads (Instagram & Facebook Feeds + Stories)',
          target_audience_hypotheses: [
            'Mindful Urbanites (25-42) interested in interior styling and studio pottery.',
            'Festive and Corporate Gifters looking for authentic handcrafted Indian luxury.',
          ],
          ad_headlines: [
            'Handcrafted Stoneware for Mindful Mornings',
            'Authentic Craft Made Patiently in Pune',
            'Mindful Living for Modern Homes',
          ],
          primary_texts: [
            'Slow down and savor your daily ritual with authentic artisan-made ceramic mugs crafted patiently in Pune.',
            'Tired of mass-produced decor? Explore small-batch handcrafted pieces designed for conscious living.',
          ],
          suggested_budget_allocation: {
            testing_budget_inr: Math.round(Number(formData.totalBudget) * 0.3),
            scaling_budget_inr: Math.round(Number(formData.totalBudget) * 0.5),
            retargeting_budget_inr: Math.round(Number(formData.totalBudget) * 0.2),
            note: 'AI hypothesis based on input constraints. Media spend is billed directly by Meta.',
          },
          disclaimer: 'AI-generated hypothesis based on seller brief. Benchmarks and ROAS are not guaranteed.',
        });
      }
      addToast({
        type: 'success',
        title: 'Gemini Campaign Plan Generated',
        message: 'Review structured audience hypotheses, headlines, and budget pacing.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Plan Generation Failed',
        message: err.message || 'Could not contact Gemini planner.',
      });
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  // Submit Campaign Creation
  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.totalBudget < formData.dailyBudgetLimit) {
      addToast({
        type: 'error',
        title: 'Budget Validation Error',
        message: 'Total budget must be greater than or equal to daily spend limit.',
      });
      return;
    }

    const selectedProd = products.find((p) => p.id === formData.selectedProductId);
    const mediaUrl = selectedProd?.media?.[0]?.url || 'https://res.cloudinary.com/marketpath/image/upload/v1/samples/lifestyle.jpg';

    const newCampaignPayload = {
      name: formData.name,
      objective: formData.objective,
      channel: formData.channel,
      totalBudget: Number(formData.totalBudget),
      dailyBudgetLimit: Number(formData.dailyBudgetLimit),
      currency: 'INR',
      startDate: formData.startDate,
      endDate: formData.endDate,
      status: 'pending_approval' as const,
      productIds: formData.selectedProductId ? [formData.selectedProductId] : [],
      targetGeography: formData.targetGeography,
      creatives: [
        {
          id: `crt_${Date.now()}`,
          headline: formData.headline,
          primaryText: formData.primaryText,
          ctaText: formData.callToAction,
          mediaUrl,
          destinationUrl: formData.landingPageUrl,
        },
      ],
    };

    if (token && activeOrg?.id) {
      try {
        const created = await apiClient<any>('/api/v1/campaigns', {
          method: 'POST',
          token,
          organizationId: activeOrg.id,
          body: JSON.stringify({
            name: formData.name,
            product_id: formData.selectedProductId || undefined,
            objective: formData.objective,
            channel: formData.channel,
            target_geography: formData.targetGeography,
            target_audience_brief: formData.targetAudienceBrief,
            total_budget: Number(formData.totalBudget),
            daily_budget_limit: Number(formData.dailyBudgetLimit),
            currency: 'INR',
            start_date: formData.startDate,
            end_date: formData.endDate,
            landing_page_url: formData.landingPageUrl,
            call_to_action: formData.callToAction,
            creative_format: formData.creativeFormat,
            creatives: [
              {
                headline: formData.headline,
                primary_text: formData.primaryText,
                cta_text: formData.callToAction,
                media_url: mediaUrl,
                destination_url: formData.landingPageUrl,
                format: formData.creativeFormat,
              },
            ],
          }),
        });

        const mappedCreated: Campaign = {
          id: created.id,
          name: created.name,
          objective: created.objective,
          totalBudget: created.total_budget,
          dailyBudgetLimit: created.daily_budget_limit,
          currency: created.currency,
          startDate: created.start_date,
          endDate: created.end_date,
          status: 'pending_approval',
          channel: created.channel,
          productId: created.product_id,
          creatives: [
            {
              id: `crt_${Date.now()}`,
              headline: formData.headline,
              primaryText: formData.primaryText,
              ctaText: formData.callToAction,
              mediaUrl,
              destinationUrl: formData.landingPageUrl,
            },
          ],
        };
        setCampaignList((prev) => [mappedCreated, ...prev]);
      } catch {
        addCampaign(newCampaignPayload);
      }
    } else {
      addCampaign(newCampaignPayload);
    }

    setShowCreateModal(false);
    setWizardStep(1);
    setGeneratedProposal(null);
  };

  // Filter Logic
  const filteredCampaigns = campaignList.filter((camp) => {
    if (filterStatus !== 'all' && camp.status !== filterStatus) return false;
    if (filterChannel !== 'all' && camp.channel !== filterChannel) return false;
    if (searchQuery && !camp.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6 max-w-6xl pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600">
            Ad Operations & Strategy
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-0.5">
            Marketing & Advertising Studio
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Plan AI campaigns, generate copy variations, and enforce strict spending limits. Media spend is charged directly to your ad account.
          </p>
        </div>

        <button
          onClick={() => {
            setShowCreateModal(true);
            setWizardStep(1);
          }}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-xs transition-colors cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Create Campaign Brief
        </button>
      </div>

      {/* KPI Overview Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase">Total Campaigns</span>
            <Megaphone className="w-4 h-4 text-brand-500" />
          </div>
          <div className="text-2xl font-extrabold text-charcoal">{totalCampaigns}</div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">{activeCampaigns} active pacing</span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase">Ready For Setup</span>
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-extrabold text-charcoal">{readyCampaigns}</div>
          <span className="text-[11px] text-emerald-600 font-medium mt-0.5 block">Owner Approved</span>
        </div>

        <div className="p-4 rounded-2xl bg-purewhite border border-bordergrey shadow-option-c">
          <div className="flex items-center justify-between text-mutedgrey mb-1">
            <span className="text-xs font-semibold uppercase">Allocated Budget</span>
            <DollarSign className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-extrabold text-charcoal">₹{totalBudgetSum.toLocaleString('en-IN')}</div>
          <span className="text-[11px] text-mutedgrey mt-0.5 block">Strict lifetime ceilings</span>
        </div>

        <div className="p-4 rounded-2xl bg-purewhite border border-bordergrey shadow-option-c">
          <div className="flex items-center justify-between text-mutedgrey mb-1">
            <span className="text-xs font-semibold uppercase">Reported Spend</span>
            <TrendingUp className="w-4 h-4 text-softorange" />
          </div>
          <div className="text-2xl font-extrabold text-charcoal">₹{totalSpendSum.toLocaleString('en-IN')}</div>
          <span className="text-[11px] text-mutedgrey mt-0.5 block">Directly billed by Meta</span>
        </div>
      </div>

      {/* Ad Account Connector Banner */}
      <div className="p-5 rounded-2xl bg-forest border border-[#0A6B53] text-white shadow-option-c flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center shrink-0 mt-0.5">
            <Target className="w-5 h-5 text-softorange" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold">Meta Marketing API Integration</h4>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-softorange/20 text-softorange border border-softorange/30">
                Developer Approval Pending
              </span>
            </div>
            <p className="text-xs text-emerald-100 mt-1 max-w-2xl leading-relaxed">
              Standard Access approval for live Meta Ads API is currently under Meta Business Manager review. While approval is pending, MarketPath provides full Gemini AI strategy planning and <strong>one-click exportable Manual Ad Setup Packs</strong> with UTM tags and targeting checklists.
            </p>
          </div>
        </div>

        <Link
          to="/app/integrations"
          className="px-4 py-2 rounded-xl bg-white/15 hover:bg-white/25 text-xs font-semibold transition-colors shrink-0 text-center border border-white/20 cursor-pointer"
        >
          Check Integrations Hub
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {[
            { id: 'all', label: 'All Campaigns' },
            { id: 'active', label: 'Active' },
            { id: 'ready_for_manual_setup', label: 'Ready for Setup' },
            { id: 'approved', label: 'Approved' },
            { id: 'pending_approval', label: 'Draft / Review' },
            { id: 'paused', label: 'Paused' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterStatus(tab.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                filterStatus === tab.id
                  ? 'bg-charcoal text-white shadow-xs'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="w-full sm:w-64">
          <input
            type="text"
            placeholder="Search campaigns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
      </div>

      {/* Campaigns Grid */}
      {filteredCampaigns.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200/80">
          <Megaphone className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-charcoal">No campaigns found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchQuery || filterStatus !== 'all'
              ? 'Try adjusting your search or status filter criteria.'
              : 'Create your first marketing brief to plan ad copy, targeting, and budget pacing.'}
          </p>
          <button
            onClick={() => {
              setShowCreateModal(true);
              setWizardStep(1);
            }}
            className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 text-white font-semibold text-xs shadow-xs"
          >
            <Plus className="w-4 h-4" /> Create Campaign Brief
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredCampaigns.map((camp) => (
            <div
              key={camp.id}
              className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-xs flex flex-col justify-between space-y-5 hover:border-slate-300 transition-all"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-100">
                      {camp.channel === 'meta_ads' ? 'Meta Ads' : 'Google Ads'} • {camp.objective.toUpperCase()}
                    </span>
                    <h3 className="text-base font-bold text-charcoal mt-2.5 leading-snug">{camp.name}</h3>
                    {camp.targetGeography && (
                      <span className="text-[11px] text-slate-400 block mt-0.5">
                        Targeting: {camp.targetGeography}
                      </span>
                    )}
                  </div>

                  {camp.status === 'approved' ? (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                      Approved
                    </span>
                  ) : camp.status === 'ready_for_manual_setup' ? (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200 shrink-0">
                      Ready for Setup
                    </span>
                  ) : camp.status === 'active' ? (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 text-white shrink-0 animate-pulse">
                      Active Live
                    </span>
                  ) : camp.status === 'paused' ? (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200 shrink-0">
                      Paused
                    </span>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 shrink-0">
                      Pending Approval
                    </span>
                  )}
                </div>

                {/* Budget Pacing Box */}
                <div className="mt-4 p-4 rounded-2xl bg-slate-50 border border-slate-100 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-500 text-[11px] block">Total Budget Cap</span>
                    <span className="text-base font-extrabold text-charcoal">
                      ₹{camp.totalBudget.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">Daily Spend Limit</span>
                    <span className="text-base font-extrabold text-charcoal">
                      ₹{camp.dailyBudgetLimit.toLocaleString('en-IN')}/day
                    </span>
                  </div>
                </div>

                {/* Live Metrics if Synced */}
                {camp.metrics && (
                  <div className="mt-3 p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between text-xs text-emerald-900">
                    <span>Spend: <strong>₹{camp.metrics.spend.toLocaleString('en-IN')}</strong></span>
                    <span>Impressions: <strong>{camp.metrics.impressions.toLocaleString()}</strong></span>
                    <span className="font-bold text-emerald-700">{camp.metrics.roas ? `${camp.metrics.roas}x ROAS` : 'Clicks: ' + camp.metrics.clicks}</span>
                  </div>
                )}
              </div>

              {/* Card Footer Actions */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <Link
                  to={`/app/campaigns/${camp.id}`}
                  className="text-xs font-bold text-brand-600 hover:text-brand-700 inline-flex items-center gap-1"
                >
                  Inspect Strategy & Creatives <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <div className="flex items-center gap-2">
                  {camp.status === 'pending_approval' ? (
                    <button
                      onClick={() => approveCampaignBudget(camp.id)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs cursor-pointer shadow-2xs transition-colors"
                    >
                      Approve Budget
                    </button>
                  ) : camp.status === 'paused' ? (
                    <button
                      onClick={() => approveCampaignBudget(camp.id)}
                      className="px-2.5 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs cursor-pointer"
                    >
                      Resume
                    </button>
                  ) : (
                    <button
                      onClick={() => pauseCampaign(camp.id)}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold text-xs cursor-pointer"
                    >
                      Pause Spend
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Multi-Step Campaign Creation Wizard Modal */}
      {showCreateModal && (
        <Modal
          isOpen={showCreateModal}
          onClose={() => {
            setShowCreateModal(false);
            setWizardStep(1);
          }}
          title="Create New Campaign Brief"
          subtitle={`Step ${wizardStep} of 4: ${
            wizardStep === 1
              ? 'Campaign Basics & Product Focus'
              : wizardStep === 2
              ? 'AI Strategy Planning (Gemini)'
              : wizardStep === 3
              ? 'Budget Limits & Pacing Guardrails'
              : 'Creative Assembly & Mockup Preview'
          }`}
          maxWidth="2xl"
        >
          <div className="space-y-5">
            {/* Step Progress Indicators */}
            <div className="grid grid-cols-4 gap-2 pb-2 border-b border-slate-100">
              {[
                { step: 1, label: '1. Basics' },
                { step: 2, label: '2. AI Plan' },
                { step: 3, label: '3. Budget' },
                { step: 4, label: '4. Creative' },
              ].map((s) => (
                <div
                  key={s.step}
                  className={`text-center py-1.5 rounded-lg text-[11px] font-bold ${
                    wizardStep === s.step
                      ? 'bg-brand-50 text-brand-700 border border-brand-200'
                      : wizardStep > s.step
                      ? 'text-emerald-700 bg-emerald-50'
                      : 'text-slate-400 bg-slate-50'
                  }`}
                >
                  {s.label}
                </div>
              ))}
            </div>

            {/* STEP 1: Basics & Product */}
            {wizardStep === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Campaign Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Artisanal Ceramic Mugs Launch Sprint"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-bold focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Promoted Master Product</label>
                    <select
                      value={formData.selectedProductId}
                      onChange={(e) => setFormData({ ...formData, selectedProductId: e.target.value })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200 bg-white"
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>{p.title} (₹{p.basePrice})</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Advertising Platform</label>
                    <select
                      value={formData.channel}
                      onChange={(e) => setFormData({ ...formData, channel: e.target.value as any })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200 bg-white"
                    >
                      <option value="meta_ads">Meta Ads (Facebook & Instagram)</option>
                      <option value="google_ads">Google Ads (Search & Shopping)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Campaign Objective</label>
                    <select
                      value={formData.objective}
                      onChange={(e) => setFormData({ ...formData, objective: e.target.value as any })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200 bg-white"
                    >
                      <option value="sales">Sales & Purchases (Catalog & Store)</option>
                      <option value="traffic">Storefront Traffic</option>
                      <option value="awareness">Brand Reach & Impressions</option>
                      <option value="leads">Lead Generation & Enquiries</option>
                      <option value="engagement">Post & Product Engagement</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Target Geography</label>
                    <input
                      type="text"
                      placeholder="e.g. Maharashtra, Mumbai MMR & Pune"
                      value={formData.targetGeography}
                      onChange={(e) => setFormData({ ...formData, targetGeography: e.target.value })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-3">
                  <button
                    type="button"
                    disabled={!formData.name}
                    onClick={() => setWizardStep(2)}
                    className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-bold text-xs"
                  >
                    Next: AI Planning <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: Gemini AI Planning */}
            {wizardStep === 2 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">
                    Describe your marketing objective & brief (Natural Language)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="e.g. Promote our handmade ceramic mugs to urban coffee and interior lovers in Maharashtra. Total budget ₹12,000 for 30 days to drive store sales."
                    value={formData.naturalLanguageBrief}
                    onChange={(e) => setFormData({ ...formData, naturalLanguageBrief: e.target.value })}
                    className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                <button
                  type="button"
                  disabled={isGeneratingPlan}
                  onClick={handleGenerateAIPlan}
                  className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs shadow-xs flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  {isGeneratingPlan ? 'Gemini is Structuring Campaign Strategy...' : 'Generate AI Campaign Proposal'}
                </button>

                {generatedProposal && (
                  <div className="p-4 rounded-2xl bg-indigo-50/70 border border-indigo-100 text-xs space-y-3 max-h-64 overflow-y-auto">
                    <div>
                      <span className="font-bold text-indigo-900 block">AI Strategy Summary:</span>
                      <p className="text-slate-700 mt-0.5 leading-relaxed">{generatedProposal.strategy_summary}</p>
                    </div>

                    <div>
                      <span className="font-bold text-indigo-900 block">Audience Hypotheses:</span>
                      <ul className="list-disc pl-4 space-y-1 text-slate-700 mt-1">
                        {generatedProposal.target_audience_hypotheses?.map((h: string, idx: number) => (
                          <li key={idx}>{h}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <span className="font-bold text-indigo-900 block">Suggested Headlines:</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {generatedProposal.ad_headlines?.map((hl: string, idx: number) => (
                          <button
                            type="button"
                            key={idx}
                            onClick={() => setFormData({ ...formData, headline: hl })}
                            className="px-2.5 py-1 rounded-lg bg-white border border-indigo-200 text-indigo-800 text-[11px] hover:bg-indigo-100/70"
                          >
                            + Use: "{hl}"
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-900">
                      <strong>Guardrail:</strong> {generatedProposal.disclaimer}
                    </div>
                  </div>
                )}

                <div className="flex justify-between pt-3">
                  <button
                    type="button"
                    onClick={() => setWizardStep(1)}
                    className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setWizardStep(3)}
                    className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs"
                  >
                    Next: Budget Limits <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: Budget & Pacing */}
            {wizardStep === 3 && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Total Lifetime Budget Cap (₹) *</label>
                    <input
                      type="number"
                      required
                      min={1000}
                      value={formData.totalBudget}
                      onChange={(e) => setFormData({ ...formData, totalBudget: Number(e.target.value) })}
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-extrabold"
                    />
                    <span className="text-[10px] text-slate-400 mt-1 block">Hard ceiling. Cannot be exceeded without owner approval.</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Daily Spend Limit (₹) *</label>
                    <input
                      type="number"
                      required
                      min={100}
                      value={formData.dailyBudgetLimit}
                      onChange={(e) => setFormData({ ...formData, dailyBudgetLimit: Number(e.target.value) })}
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-extrabold"
                    />
                    <span className="text-[10px] text-slate-400 mt-1 block">Pacing guardrail against sudden auction surges.</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Start Date</label>
                    <input
                      type="date"
                      value={formData.startDate}
                      onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">End Date</label>
                    <input
                      type="date"
                      value={formData.endDate}
                      onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200"
                    />
                  </div>
                </div>

                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-slate-800">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    Strict Financial Separation
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Advertising media spend is charged directly to your own connected Meta/Google ad account. MarketPath never takes custody of seller ad money, ensuring 100% transparency.
                  </p>
                </div>

                <div className="flex justify-between pt-3">
                  <button
                    type="button"
                    onClick={() => setWizardStep(2)}
                    className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setWizardStep(4)}
                    className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs"
                  >
                    Next: Creative Assembly <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 4: Creative Assembly & Mockup Preview */}
            {wizardStep === 4 && (
              <form onSubmit={handleCreateCampaign} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Ad Headline *</label>
                  <input
                    type="text"
                    required
                    value={formData.headline}
                    onChange={(e) => setFormData({ ...formData, headline: e.target.value })}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-bold"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Primary Ad Copy *</label>
                  <textarea
                    rows={3}
                    required
                    value={formData.primaryText}
                    onChange={(e) => setFormData({ ...formData, primaryText: e.target.value })}
                    className="w-full text-xs p-3 rounded-xl border border-slate-200 leading-relaxed"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Destination URL</label>
                    <input
                      type="url"
                      value={formData.landingPageUrl}
                      onChange={(e) => setFormData({ ...formData, landingPageUrl: e.target.value })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Call to Action (CTA)</label>
                    <select
                      value={formData.callToAction}
                      onChange={(e) => setFormData({ ...formData, callToAction: e.target.value })}
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200 bg-white"
                    >
                      <option value="Shop Now">Shop Now</option>
                      <option value="Explore Collection">Explore Collection</option>
                      <option value="Order Today">Order Today</option>
                      <option value="Learn More">Learn More</option>
                      <option value="Sign Up">Sign Up</option>
                    </select>
                  </div>
                </div>

                {/* Live Responsive Ad Mockup Card */}
                <div>
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                    Responsive Meta Feed Preview
                  </label>
                  <div className="max-w-sm mx-auto border border-slate-200 rounded-2xl bg-white shadow-xs overflow-hidden">
                    <div className="p-3 flex items-center gap-2.5 border-b border-slate-100">
                      <div className="w-7 h-7 rounded-full bg-brand-600 text-white font-extrabold text-[10px] flex items-center justify-center">
                        AT
                      </div>
                      <div>
                        <span className="text-xs font-bold text-charcoal block leading-none">Aura Terra Living</span>
                        <span className="text-[10px] text-slate-400">Sponsored • Paid</span>
                      </div>
                    </div>
                    <div className="px-3.5 py-2 text-xs text-charcoal leading-relaxed">
                      {formData.primaryText}
                    </div>
                    <div className="w-full h-44 bg-slate-100 flex items-center justify-center overflow-hidden">
                      {products.find((p) => p.id === formData.selectedProductId)?.media?.[0]?.url ? (
                        <img
                          src={products.find((p) => p.id === formData.selectedProductId)!.media[0].url}
                          alt="Ad creative preview"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-xs text-slate-400">Product Image Preview</span>
                      )}
                    </div>
                    <div className="p-3 bg-slate-50 flex items-center justify-between border-t border-slate-100">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block">auraterra.in</span>
                        <span className="text-xs font-bold text-charcoal block truncate max-w-[200px]">{formData.headline}</span>
                      </div>
                      <span className="px-3 py-1.5 bg-slate-200 text-slate-800 font-bold text-[11px] rounded-lg">
                        {formData.callToAction}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex justify-between pt-3">
                  <button
                    type="button"
                    onClick={() => setWizardStep(3)}
                    className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-xs"
                  >
                    Save & Create Campaign Brief
                  </button>
                </div>
              </form>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
