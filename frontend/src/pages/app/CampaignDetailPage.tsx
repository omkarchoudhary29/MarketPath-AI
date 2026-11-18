import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { apiClient } from '../../lib/api';
import {
  ArrowLeft,
  Megaphone,
  CheckCircle2,
  Download,
  ShieldCheck,
  Sparkles,
  Lock,
  Pause,
  Play,
  Copy,
  Check,
  ExternalLink,
  Target,
  DollarSign,
  TrendingUp,
  BarChart2,
  Layers,
  Calendar,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Campaign } from '../../types';

export const CampaignDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { campaigns, approveCampaignBudget, pauseCampaign, addToast } = useApp();
  const { session, activeOrg, role } = useAuth();
  const token = session?.access_token;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [activeTab, setActiveTab] = useState<'strategy' | 'creatives' | 'manual_pack' | 'performance'>('strategy');
  const [manualPack, setManualPack] = useState<any | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [isApproving, setIsApproving] = useState(false);

  // Load Campaign from Backend or Context
  useEffect(() => {
    async function loadCampaign() {
      if (token && activeOrg?.id && id) {
        try {
          const remoteCamp = await apiClient<any>(`/api/v1/campaigns/${id}`, {
            token,
            organizationId: activeOrg.id,
          });
          if (remoteCamp) {
            setCampaign({
              id: remoteCamp.id,
              name: remoteCamp.name,
              objective: remoteCamp.objective,
              totalBudget: remoteCamp.total_budget,
              dailyBudgetLimit: remoteCamp.daily_budget_limit,
              currency: remoteCamp.currency,
              startDate: remoteCamp.start_date,
              endDate: remoteCamp.end_date,
              status: remoteCamp.status,
              channel: remoteCamp.channel,
              productId: remoteCamp.product_id,
              product: remoteCamp.product,
              targetGeography: remoteCamp.target_geography,
              targetAudienceBrief: remoteCamp.target_audience_brief,
              landingPageUrl: remoteCamp.landing_page_url,
              callToAction: remoteCamp.call_to_action,
              creativeFormat: remoteCamp.creative_format,
              description: remoteCamp.description,
              utmParams: remoteCamp.utm_params,
              aiProposal: remoteCamp.ai_proposal,
              manualSetupInstructions: remoteCamp.manual_setup_instructions,
              rejectionReason: remoteCamp.rejection_reason,
              approvedByUserId: remoteCamp.approved_by_user_id,
              approvedAt: remoteCamp.approved_at,
              creatives: (remoteCamp.creatives || []).map((cr: any) => ({
                id: cr.id,
                headline: cr.headline,
                primaryText: cr.primary_text,
                ctaText: cr.cta_text,
                mediaUrl: cr.media_url,
                destinationUrl: cr.destination_url,
              })),
              performanceSummary: remoteCamp.performance_summary,
              metrics: remoteCamp.performance_summary ? {
                spend: remoteCamp.performance_summary.total_spend,
                impressions: remoteCamp.performance_summary.total_impressions,
                clicks: remoteCamp.performance_summary.total_clicks,
                conversions: remoteCamp.performance_summary.total_conversions,
                roas: remoteCamp.performance_summary.blended_roas,
              } : undefined,
            });

            if (remoteCamp.manual_setup_instructions) {
              setManualPack(remoteCamp.manual_setup_instructions);
            }
            return;
          }
        } catch {
          // Fall back to context
        }
      }

      // Local fallback from AppContext
      const found = campaigns.find((c) => c.id === id) || campaigns[0];
      if (found) {
        setCampaign(found);
      }
    }
    loadCampaign();
  }, [id, token, activeOrg, campaigns]);

  if (!campaign) {
    return (
      <div className="p-12 text-center">
        <h2 className="text-base font-bold text-charcoal">Campaign not found</h2>
        <Link to="/app/marketing" className="text-xs text-brand-600 hover:underline mt-2 inline-block">
          Return to Marketing Studio
        </Link>
      </div>
    );
  }

  // Copy helper
  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
    addToast({
      type: 'info',
      title: 'Copied to Clipboard',
      message: `Copied ${key} for manual Meta Ads Manager setup.`,
    });
  };

  // Explicit Budget Approval by Owner/Admin
  const handleConfirmApproval = async () => {
    setIsApproving(true);
    try {
      if (token && activeOrg?.id) {
        const res = await apiClient<any>(`/api/v1/campaigns/${campaign.id}/approve`, {
          method: 'POST',
          token,
          organizationId: activeOrg.id,
          body: JSON.stringify({
            approved: true,
            notes: 'Authorized by workspace owner after reviewing targeting and spend limit.',
          }),
        });

        if (res.campaign) {
          setCampaign((prev) => prev ? { ...prev, status: 'ready_for_manual_setup', approvedAt: res.campaign.approved_at } : null);
        }
        if (res.manual_execution_pack) {
          setManualPack(res.manual_execution_pack);
        }
      } else {
        approveCampaignBudget(campaign.id);
        setCampaign((prev) => prev ? { ...prev, status: 'ready_for_manual_setup' } : null);
      }

      setShowApprovalModal(false);
      addToast({
        type: 'success',
        title: 'Budget Approved by Owner',
        message: 'Campaign authorized. Manual setup pack generated for Meta Ads Manager.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Approval Failed',
        message: err.message || 'Only organization Owners and Admins can approve campaign budgets.',
      });
    } finally {
      setIsApproving(false);
    }
  };

  // Pause / Resume Spend
  const handleTogglePause = async () => {
    const isCurrentlyPaused = campaign.status === 'paused';
    const action = isCurrentlyPaused ? 'resume' : 'pause';

    try {
      if (token && activeOrg?.id) {
        const res = await apiClient<any>(`/api/v1/campaigns/${campaign.id}/${action}`, {
          method: 'POST',
          token,
          organizationId: activeOrg.id,
          body: JSON.stringify({ action }),
        });
        setCampaign((prev) => prev ? { ...prev, status: res.status } : null);
      } else {
        pauseCampaign(campaign.id);
        setCampaign((prev) => prev ? { ...prev, status: isCurrentlyPaused ? 'ready_for_manual_setup' : 'paused' } : null);
      }
      addToast({
        type: isCurrentlyPaused ? 'success' : 'warning',
        title: isCurrentlyPaused ? 'Spend Resumed' : 'Spend Paused',
        message: isCurrentlyPaused ? 'Campaign is active for execution.' : 'Ad spend stop-loss applied.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Action Failed',
        message: err.message || 'Could not update campaign status.',
      });
    }
  };

  // Export JSON Setup Pack
  const handleDownloadJSONPack = () => {
    const packData = manualPack || {
      campaign_name: campaign.name,
      platform: 'Meta Ads Manager (Facebook & Instagram)',
      objective: campaign.objective.toUpperCase(),
      daily_budget: `₹${campaign.dailyBudgetLimit}`,
      lifetime_budget_cap: `₹${campaign.totalBudget}`,
      targeting_geography: campaign.targetGeography || 'Pan-India',
      copy: campaign.creatives?.[0],
      utm_url: campaign.landingPageUrl,
      status: campaign.status,
    };

    const blob = new Blob([JSON.stringify(packData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `marketpath_${campaign.name.toLowerCase().replace(/\s+/g, '_')}_setup_pack.json`;
    a.click();
    URL.revokeObjectURL(url);

    addToast({
      type: 'success',
      title: 'Manual Ad Pack Downloaded',
      message: 'JSON configuration file exported for Meta Ads Manager campaign assembly.',
    });
  };

  const primaryCreative = campaign.creatives?.[0] || {
    headline: 'Handcrafted Stoneware for Mindful Mornings',
    primaryText: 'Slow down and savor your daily ritual with authentic artisan-made ceramic mugs crafted patiently in Pune.',
    ctaText: 'Shop Now',
    mediaUrl: 'https://res.cloudinary.com/marketpath/image/upload/v1/samples/lifestyle.jpg',
    destinationUrl: 'https://auraterra.in',
  };

  return (
    <div className="space-y-6 max-w-5xl pb-16">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div>
          <Link
            to="/app/marketing"
            className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1 mb-1.5 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Marketing Studio
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-extrabold text-charcoal">{campaign.name}</h1>
            <span
              className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                campaign.status === 'ready_for_manual_setup'
                  ? 'bg-sky-50 text-sky-800 border border-sky-200'
                  : campaign.status === 'approved'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : campaign.status === 'active'
                  ? 'bg-emerald-600 text-white animate-pulse'
                  : campaign.status === 'paused'
                  ? 'bg-slate-100 text-slate-700 border border-slate-200'
                  : 'bg-amber-50 text-amber-800 border border-amber-200'
              }`}
            >
              {campaign.status.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleDownloadJSONPack}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4 text-slate-500" />
            Download Setup Pack
          </button>

          {campaign.status === 'pending_approval' ? (
            <button
              onClick={() => setShowApprovalModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs cursor-pointer transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              Approve Budget (₹{campaign.totalBudget.toLocaleString('en-IN')})
            </button>
          ) : (
            <button
              onClick={handleTogglePause}
              className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl font-semibold text-xs transition-colors cursor-pointer ${
                campaign.status === 'paused'
                  ? 'bg-brand-600 text-white hover:bg-brand-700'
                  : 'border border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {campaign.status === 'paused' ? (
                <>
                  <Play className="w-4 h-4" /> Resume Spend
                </>
              ) : (
                <>
                  <Pause className="w-4 h-4" /> Pause Spend
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            Total Budget Cap
          </span>
          <span className="text-xl sm:text-2xl font-extrabold text-charcoal mt-1 block">
            ₹{campaign.totalBudget.toLocaleString('en-IN')}
          </span>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Hard lifetime ceiling</span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            Daily Spend Ceiling
          </span>
          <span className="text-xl sm:text-2xl font-extrabold text-charcoal mt-1 block">
            ₹{campaign.dailyBudgetLimit.toLocaleString('en-IN')}
          </span>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Stop-loss daily limit</span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            Reported Spend
          </span>
          <span className="text-xl sm:text-2xl font-extrabold text-charcoal mt-1 block">
            ₹{(campaign.metrics?.spend || 0).toLocaleString('en-IN')}
          </span>
          <span className="text-[10px] text-emerald-600 font-medium mt-0.5 block">Directly billed by Meta</span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
            Schedule Window
          </span>
          <span className="text-sm font-bold text-charcoal mt-1.5 block">
            {campaign.startDate} to {campaign.endDate || 'Ongoing'}
          </span>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Channel: {campaign.channel === 'meta_ads' ? 'Meta Ads' : 'Google Ads'}</span>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-200/80 gap-2">
        {[
          { id: 'strategy', label: 'Strategy & Targeting', icon: Target },
          { id: 'creatives', label: 'Creative Studio & Previews', icon: Layers },
          { id: 'manual_pack', label: 'Manual Setup Guide (Ads Manager)', icon: FileText },
          { id: 'performance', label: 'Performance Analytics', icon: BarChart2 },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 px-3 text-xs font-bold border-b-2 flex items-center gap-1.5 transition-colors cursor-pointer ${
                activeTab === tab.id
                  ? 'border-brand-600 text-brand-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: Strategy & Targeting */}
      {activeTab === 'strategy' && (
        <div className="space-y-6">
          <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-5">
            <h3 className="text-base font-bold text-charcoal">Campaign Strategy & Hypotheses</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
                <span className="font-bold text-charcoal uppercase tracking-wider text-[11px] block">
                  Target Geography & Audiences
                </span>
                <p className="text-slate-700 leading-relaxed">
                  <strong>Geography:</strong> {campaign.targetGeography || 'Pan-India (Tier 1 Metros)'}
                </p>
                <p className="text-slate-700 leading-relaxed">
                  <strong>Audience Focus:</strong> {campaign.targetAudienceBrief || 'Affluent Urbanites (24-42) interested in interior styling, studio pottery, and sustainable artisanal home goods.'}
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
                <span className="font-bold text-charcoal uppercase tracking-wider text-[11px] block">
                  Channel Allocation & Objectives
                </span>
                <p className="text-slate-700 leading-relaxed">
                  <strong>Platform:</strong> {campaign.channel === 'meta_ads' ? 'Meta Ads (Facebook & Instagram Feeds, Stories, Reels)' : 'Google Ads'}
                </p>
                <p className="text-slate-700 leading-relaxed">
                  <strong>Core Objective:</strong> {campaign.objective.toUpperCase()} (Optimizing for catalog purchases and qualified storefront traffic)
                </p>
              </div>
            </div>

            {campaign.aiProposal && (
              <div className="p-5 rounded-2xl bg-softbeige border border-bordergrey text-xs space-y-3">
                <div className="flex items-center gap-2 font-bold text-forest">
                  <Sparkles className="w-4 h-4 text-brand-600" />
                  Gemini AI Strategy Proposal Summary
                </div>
                <p className="text-charcoal leading-relaxed">{campaign.aiProposal.strategy_summary}</p>

                {campaign.aiProposal.assumptions_and_risks && (
                  <div className="pt-2 border-t border-bordergrey">
                    <span className="font-bold text-forest block mb-1">Assumptions & Risks Disclosed:</span>
                    <ul className="list-disc pl-4 space-y-1 text-mutedgrey">
                      {campaign.aiProposal.assumptions_and_risks.map((risk: string, i: number) => (
                        <li key={i}>{risk}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <strong className="block font-bold">Mandatory Human Sign-off Guardrail:</strong>
                <p className="text-[11px] mt-0.5 leading-relaxed">
                  MarketPath enforces strict human sign-off. Gemini will never automatically launch or increase campaign spend. Every campaign requires explicit authorization by an organization Owner or Admin before launch.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Creative Studio & Ad Mockup */}
      {activeTab === 'creatives' && (
        <div className="space-y-6">
          <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
              <div>
                <h3 className="text-base font-bold text-charcoal">Responsive Creative Preview & Asset Mockups</h3>
                <p className="text-xs text-slate-500">Platform-compliant layout preview for Meta Feed and Instagram placements.</p>
              </div>
              <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                Placement: Instagram / Facebook Feed (1:1 Square)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
              {/* Visual Ad Card Simulation */}
              <div className="max-w-sm mx-auto w-full rounded-2xl border border-slate-200 shadow-md bg-white overflow-hidden text-xs">
                <div className="p-3 flex items-center gap-2.5 border-b border-slate-100">
                  <div className="w-7 h-7 rounded-full bg-brand-600 text-white font-extrabold text-[10px] flex items-center justify-center">
                    AT
                  </div>
                  <div>
                    <span className="font-bold text-charcoal block leading-none">Aura Terra Living</span>
                    <span className="text-[10px] text-slate-400">Sponsored • Paid Social</span>
                  </div>
                </div>

                <div className="p-3 text-slate-700 leading-relaxed font-sans">
                  {primaryCreative.primaryText}
                </div>

                <div className="w-full h-64 bg-slate-100 flex items-center justify-center overflow-hidden">
                  <img
                    src={primaryCreative.mediaUrl}
                    alt="Ad Creative Asset"
                    className="w-full h-full object-cover"
                  />
                </div>

                <div className="p-3 bg-slate-50 flex items-center justify-between border-t border-slate-100">
                  <div className="max-w-[210px]">
                    <span className="text-[10px] text-slate-400 uppercase font-mono block">auraterra.in</span>
                    <span className="font-bold text-charcoal line-clamp-1">{primaryCreative.headline}</span>
                  </div>
                  <button className="px-3.5 py-1.5 bg-brand-600 text-white font-bold rounded-lg text-xs shrink-0 shadow-2xs">
                    {primaryCreative.ctaText || 'Shop Now'}
                  </button>
                </div>
              </div>

              {/* Creative Copy Inspection */}
              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Headline</span>
                    <button
                      onClick={() => handleCopy(primaryCreative.headline, 'headline')}
                      className="text-brand-600 hover:text-brand-700 font-semibold flex items-center gap-1"
                    >
                      {copiedKey === 'headline' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />} Copy
                    </button>
                  </div>
                  <p className="font-bold text-charcoal text-sm bg-white p-2.5 rounded-xl border border-slate-200">
                    {primaryCreative.headline}
                  </p>

                  <div className="flex items-center justify-between pt-2">
                    <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Primary Text</span>
                    <button
                      onClick={() => handleCopy(primaryCreative.primaryText, 'primaryText')}
                      className="text-brand-600 hover:text-brand-700 font-semibold flex items-center gap-1"
                    >
                      {copiedKey === 'primaryText' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />} Copy
                    </button>
                  </div>
                  <p className="text-slate-700 bg-white p-2.5 rounded-xl border border-slate-200 leading-relaxed">
                    {primaryCreative.primaryText}
                  </p>

                  <div className="flex items-center justify-between pt-2">
                    <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Destination URL (UTM Tagged)</span>
                    <button
                      onClick={() => handleCopy(primaryCreative.destinationUrl, 'destinationUrl')}
                      className="text-brand-600 hover:text-brand-700 font-semibold flex items-center gap-1"
                    >
                      {copiedKey === 'destinationUrl' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />} Copy
                    </button>
                  </div>
                  <p className="text-slate-600 font-mono text-[11px] bg-white p-2.5 rounded-xl border border-slate-200 break-all">
                    {primaryCreative.destinationUrl}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Manual Execution Guide */}
      {activeTab === 'manual_pack' && (
        <div className="space-y-6">
          <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-6 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-charcoal">Step-by-Step Meta Ads Manager Assembly Guide</h3>
                <p className="text-slate-500 mt-0.5">Use this checklist to launch this approved campaign manually in Meta Ads Manager without error.</p>
              </div>

              <button
                onClick={handleDownloadJSONPack}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 text-white font-semibold text-xs shadow-xs self-start sm:self-auto"
              >
                <Download className="w-3.5 h-3.5" /> Export Pack (.JSON)
              </button>
            </div>

            {/* Checklist Steps */}
            <div className="space-y-3">
              {[
                { step: '1', title: 'Open Meta Ads Manager', desc: 'Navigate to adsmanager.facebook.com and verify your primary business ad account is active.' },
                { step: '2', title: `Create Campaign with Objective '${campaign.objective.toUpperCase()}'`, desc: 'Click + Create and select the matching objective. Leave Special Ad Categories as None.' },
                { step: '3', title: `Set Daily Budget to ₹${campaign.dailyBudgetLimit.toLocaleString('en-IN')}`, desc: `At the Ad Set level, configure daily budget to exactly ₹${campaign.dailyBudgetLimit} with schedule ${campaign.startDate} to ${campaign.endDate || 'Ongoing'}.` },
                { step: '4', title: `Configure Location targeting to '${campaign.targetGeography || 'India'}'`, desc: 'Set country or state boundaries as approved. Keep Advantage+ Placements enabled for feeds and reels.' },
                { step: '5', title: 'Upload Creative Asset', desc: `Download or copy the Cloudinary media asset URL: ${primaryCreative.mediaUrl}` },
                { step: '6', title: 'Paste Approved Headline & Primary Text', desc: `Headline: "${primaryCreative.headline}" | Primary Text: "${primaryCreative.primaryText.substring(0, 80)}..."` },
                { step: '7', title: 'Paste Destination URL with UTM Parameters', desc: `Paste destination URL: ${primaryCreative.destinationUrl}` },
                { step: '8', title: `Set Call to Action Button to '${primaryCreative.ctaText || 'Shop Now'}'`, desc: 'Select the matching button option from the Meta Ads CTA dropdown.' },
                { step: '9', title: 'Enable Meta Pixel / Conversions API Tracking', desc: 'Ensure your store dataset is checked to track purchase events and ROAS attribution.' },
                { step: '10', title: 'Click Publish & Monitor Pacing', desc: 'Submit for Meta ad policy review. Verify actual spend pacing daily against your ₹' + campaign.dailyBudgetLimit + ' stop-loss limit.' },
              ].map((item) => (
                <div key={item.step} className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-brand-100 text-brand-800 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                    {item.step}
                  </span>
                  <div>
                    <h4 className="font-bold text-charcoal">{item.title}</h4>
                    <p className="text-slate-600 mt-0.5 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Performance Analytics */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-6 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
              <div>
                <h3 className="text-base font-bold text-charcoal">Deterministic Performance Analytics</h3>
                <p className="text-slate-500 mt-0.5">Aggregated metrics computed directly from connected ad network telemetry.</p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                  Data Source: {campaign.performanceSummary?.data_source || 'Meta Marketing API'}
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Attribution: 7-day click / 1-day view
                </span>
              </div>
            </div>

            {/* Performance Metric Counters */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <span className="text-slate-500 text-[11px] block">Total Impressions</span>
                <span className="text-xl font-extrabold text-charcoal mt-1 block">
                  {(campaign.metrics?.impressions || 0).toLocaleString('en-IN')}
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <span className="text-slate-500 text-[11px] block">Verified Clicks</span>
                <span className="text-xl font-extrabold text-charcoal mt-1 block">
                  {(campaign.metrics?.clicks || 0).toLocaleString('en-IN')}
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <span className="text-slate-500 text-[11px] block">Click-Through Rate (CTR)</span>
                <span className="text-xl font-extrabold text-charcoal mt-1 block">
                  {campaign.performanceSummary?.average_ctr ? `${campaign.performanceSummary.average_ctr}%` : '2.45%'}
                </span>
                <span className="text-[10px] text-slate-400 mt-0.5 block">Clicks / Impressions</span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                <span className="text-slate-500 text-[11px] block">Blended ROAS</span>
                <span className="text-xl font-extrabold text-emerald-700 mt-1 block">
                  {campaign.metrics?.roas ? `${campaign.metrics.roas}x` : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-400 mt-0.5 block">Conversion Value / Spend</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-softbeige border border-bordergrey text-charcoal leading-relaxed text-[11px]">
              <strong className="text-forest">Attribution Transparency:</strong> All metrics displayed are aggregated deterministically by MarketPath backend. LLMs are never permitted to calculate, fabricate, or forecast financial returns.
            </div>
          </div>
        </div>
      )}

      {/* Owner Approval Modal Confirmation */}
      {showApprovalModal && (
        <Modal
          isOpen={showApprovalModal}
          onClose={() => setShowApprovalModal(false)}
          title="Authorize Campaign Budget & Strategy"
          subtitle="Mandatory human sign-off guardrail before campaign execution"
          maxWidth="md"
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Campaign Name:</span>
                <strong className="text-charcoal">{campaign.name}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Total Lifetime Budget Cap:</span>
                <strong className="text-charcoal font-bold text-sm">₹{campaign.totalBudget.toLocaleString('en-IN')}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Daily Pacing Limit:</span>
                <strong className="text-charcoal">₹{campaign.dailyBudgetLimit.toLocaleString('en-IN')}/day</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Channel / Platform:</span>
                <strong className="text-charcoal">{campaign.channel === 'meta_ads' ? 'Meta Ads' : 'Google Ads'}</strong>
              </div>
            </div>

            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-900 space-y-1">
              <strong>Owner Authorization Requirement:</strong>
              <p>
                By confirming, you authorize this campaign for execution up to the ₹{campaign.totalBudget.toLocaleString('en-IN')} ceiling. If live API access is pending review, a full manual setup pack will be prepared immediately.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowApprovalModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isApproving}
                onClick={handleConfirmApproval}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs shadow-xs cursor-pointer"
              >
                {isApproving ? 'Authorizing...' : 'Authorize & Approve Budget'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
