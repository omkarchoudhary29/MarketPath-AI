import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Compass,
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  MapPin,
  Building,
  DollarSign,
  ArrowRight,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  Send,
  Sliders,
  ShieldCheck,
  Layers,
  Award,
  AlertTriangle,
  RefreshCw,
  Plus,
  Scale,
  X,
  FileText,
  UserCheck,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import { Modal } from '../../components/ui/Modal';

const STANDARD_SERVICES = [
  'Digital marketing',
  'Social media management',
  'Meta Ads management',
  'Google Ads management',
  'SEO',
  'Shopify store development',
  'E-commerce website development',
  'Product photography',
  'Product videography',
  'Graphic design',
  'Branding',
  'Packaging design',
  'Influencer marketing',
  'Content creation',
  'Email marketing',
  'Marketing strategy and consultation',
];

const STANDARD_OBJECTIVES = [
  'Increase online sales',
  'Improve social media presence',
  'Improve product photography',
  'Improve advertising performance',
  'Increase brand awareness',
  'Generate leads',
  'Build an online store',
  'Expand into new marketing channels',
];

interface AgencyItem {
  id: string;
  name: string;
  slug: string;
  tagline: string;
  description: string;
  logo_url?: string;
  website?: string;
  email: string;
  city: string;
  state: string;
  country: string;
  remote_or_local: string;
  team_size: string;
  founded_year: number;
  category_specialties: string[];
  service_offerings: string[];
  min_budget_inr: number;
  max_budget_inr?: number;
  verification_status: string;
  is_available: boolean;
  is_featured: boolean;
  is_demo: boolean;
  rating_avg: number;
  reviews_count: number;
  packages?: any[];
}

interface MatchCard {
  agency: AgencyItem;
  packages: any[];
  match_score: number;
  is_eligible: boolean;
  explanation: {
    why_matched: string;
    services_covered: string[];
    portfolio_highlights: string[];
    budget_compatibility_note: string;
    location_compatibility_note: string;
    verification_standing: string;
    missing_or_uncertain_info?: string;
    score_breakdown: Record<string, number>;
  };
  is_featured: boolean;
}

interface QuoteRequestItem {
  id: string;
  project_title: string;
  project_description: string;
  budget_inr: number;
  budget_type: string;
  timeframe: string;
  status: string;
  agency_name?: string;
  quotation_amount_inr?: number;
  quotation_deliverables?: string[];
  agency_response_notes?: string;
  created_at: string;
}

export const AgencyConnectPage: React.FC = () => {
  const { session } = useAuth();
  const { org, addToast } = useApp();
  const navigate = useNavigate();
  const token = session?.access_token;
  const orgId = org?.id;

  const [activeTab, setActiveTab] = useState<'discover' | 'recommendations' | 'saved' | 'requests'>('discover');
  const [isLoading, setIsLoading] = useState(false);

  // Discovery state
  const [agencies, setAgencies] = useState<AgencyItem[]>([]);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedService, setSelectedService] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [maxBudget, setMaxBudget] = useState<number | ''>('');
  const [remoteOnly, setRemoteOnly] = useState(false);

  // Recommendations state
  const [recommendations, setRecommendations] = useState<MatchCard[]>([]);
  const [isMatchingLoading, setIsMatchingLoading] = useState(false);
  const [activeRequirement, setActiveRequirement] = useState<any>(null);

  // Saved agencies state
  const [savedAgencies, setSavedAgencies] = useState<AgencyItem[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  // Comparison state (2-4 agencies)
  const [compareList, setCompareList] = useState<AgencyItem[]>([]);
  const [showCompareModal, setShowCompareModal] = useState(false);

  // Quote Requests state
  const [quoteRequests, setQuoteRequests] = useState<QuoteRequestItem[]>([]);
  const [selectedAgencyForQuote, setSelectedAgencyForQuote] = useState<AgencyItem | null>(null);
  const [rfpTitle, setRfpTitle] = useState('');
  const [rfpDesc, setRfpDesc] = useState('');
  const [rfpBudget, setRfpBudget] = useState(15000);
  const [rfpType, setRfpType] = useState('monthly');
  const [rfpTimeframe, setRfpTimeframe] = useState('1-3 Months');
  const [rfpEmail, setRfpEmail] = useState('');
  const [rfpConsent, setRfpConsent] = useState(true);
  const [isSubmittingRfp, setIsSubmittingRfp] = useState(false);

  // Requirement Wizard Modal state
  const [showWizardModal, setShowWizardModal] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);
  const [wizardBrand, setWizardBrand] = useState(org?.name || '');
  const [wizardCategory, setWizardCategory] = useState('Home & Living');
  const [wizardStage, setWizardStage] = useState('Early Stage (<₹5L/mo)');
  const [wizardLocation, setWizardLocation] = useState('Pune');
  const [wizardMonthlyBudget, setWizardMonthlyBudget] = useState(15000);
  const [wizardObjectives, setWizardObjectives] = useState<string[]>(['Increase online sales', 'Improve product photography']);
  const [wizardServices, setWizardServices] = useState<string[]>(['Product photography', 'Meta Ads management']);
  const [wizardNotes, setWizardNotes] = useState('');
  const [isAiExtracting, setIsAiExtracting] = useState(false);
  const [aiExtractionResult, setAiExtractionResult] = useState<any>(null);

  // Load Initial Discovery Data
  const loadAgencies = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedService) params.append('service', selectedService);
      if (selectedLocation) params.append('location', selectedLocation);
      if (maxBudget) params.append('max_budget', maxBudget.toString());
      if (remoteOnly) params.append('remote_only', 'true');

      const data = await apiClient<AgencyItem[]>(`/api/v1/agency/discover?${params.toString()}`);
      setAgencies(data);
    } catch (err: any) {
      console.error('Failed to load agencies:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Load Active Requirement & Recommendations
  const loadRecommendations = async () => {
    if (!token || !orgId) return;
    setIsMatchingLoading(true);
    try {
      const reqData = await apiClient<any>('/api/v1/agency/requirements/active', { token, organizationId: orgId });
      setActiveRequirement(reqData);

      const recData = await apiClient<{ matches: MatchCard[] }>('/api/v1/agency/recommendations', { token, organizationId: orgId });
      setRecommendations(recData.matches || []);
    } catch (err: any) {
      console.error('Failed to fetch recommendations:', err);
    } finally {
      setIsMatchingLoading(false);
    }
  };

  // Load Saved Shortlist
  const loadSaved = async () => {
    if (!token || !orgId) return;
    try {
      const data = await apiClient<AgencyItem[]>('/api/v1/agency/shortlists', { token, organizationId: orgId });
      setSavedAgencies(data);
      setSavedIds(new Set(data.map((a) => a.id)));
    } catch (err: any) {
      console.error('Failed to load saved shortlist:', err);
    }
  };

  // Load Quote Requests
  const loadQuoteRequests = async () => {
    if (!token || !orgId) return;
    try {
      const data = await apiClient<QuoteRequestItem[]>('/api/v1/agency/quote-requests', { token, organizationId: orgId });
      setQuoteRequests(data);
    } catch (err: any) {
      console.error('Failed to load quote requests:', err);
    }
  };

  useEffect(() => {
    loadAgencies();
    loadSaved();
  }, [search, selectedCategory, selectedService, selectedLocation, maxBudget, remoteOnly]);

  useEffect(() => {
    if (activeTab === 'recommendations') {
      loadRecommendations();
    } else if (activeTab === 'saved') {
      loadSaved();
    } else if (activeTab === 'requests') {
      loadQuoteRequests();
    }
  }, [activeTab, token, orgId]);

  // Toggle Save Agency Bookmark
  const handleToggleSave = async (agency: AgencyItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!token || !orgId) {
      addToast({ type: 'warning', title: 'Sign In Required', message: 'Please sign in to save agencies.' });
      return;
    }
    try {
      const res = await apiClient<{ saved: boolean }>(`/api/v1/agency/shortlists/${agency.id}`, {
        method: 'POST',
        token,
        organizationId: orgId,
      });
      if (res.saved) {
        setSavedIds((prev) => new Set([...prev, agency.id]));
        setSavedAgencies((prev) => [...prev, agency]);
        addToast({ type: 'success', title: 'Agency Shortlisted', message: `Saved "${agency.name}" to your shortlist.` });
      } else {
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(agency.id);
          return next;
        });
        setSavedAgencies((prev) => prev.filter((a) => a.id !== agency.id));
        addToast({ type: 'info', title: 'Bookmark Removed', message: `Removed "${agency.name}" from your shortlist.` });
      }
    } catch (err: any) {
      addToast({ type: 'error', title: 'Error', message: err.message || 'Failed to update shortlist.' });
    }
  };

  // Toggle Comparison List
  const handleToggleCompare = (agency: AgencyItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (compareList.some((a) => a.id === agency.id)) {
      setCompareList((prev) => prev.filter((a) => a.id !== agency.id));
    } else {
      if (compareList.length >= 4) {
        addToast({ type: 'warning', title: 'Maximum 4 Agencies', message: 'You can compare up to 4 agencies at a time.' });
        return;
      }
      setCompareList((prev) => [...prev, agency]);
      addToast({ type: 'info', title: 'Added to Comparison', message: `Added "${agency.name}".` });
    }
  };

  // AI Wizard Extraction
  const handleRunAiWizard = async () => {
    setIsAiExtracting(true);
    try {
      const data = await apiClient<any>('/api/v1/agency/requirements/ai-extract', {
        method: 'POST',
        token,
        body: JSON.stringify({
          brand_name: wizardBrand,
          product_category: wizardCategory,
          business_stage: wizardStage,
          location: wizardLocation,
          selected_objectives: wizardObjectives,
          selected_services: wizardServices,
          monthly_budget_inr: wizardMonthlyBudget,
          raw_brief_text: wizardNotes,
        }),
      });
      setAiExtractionResult(data);
      setWizardStep(3);
    } catch (err: any) {
      addToast({ type: 'error', title: 'AI Extraction Error', message: err.message || 'Failed to analyze brief.' });
    } finally {
      setIsAiExtracting(false);
    }
  };

  // Save Wizard Requirement
  const handleSaveWizardRequirement = async () => {
    if (!token || !orgId) return;
    try {
      await apiClient('/api/v1/agency/requirements', {
        method: 'POST',
        token,
        organizationId: orgId,
        body: JSON.stringify({
          brand_name: wizardBrand,
          product_category: wizardCategory,
          business_stage: wizardStage,
          location: wizardLocation,
          selected_objectives: wizardObjectives,
          selected_services: wizardServices,
          monthly_budget_inr: wizardMonthlyBudget,
          ai_search_brief: aiExtractionResult?.search_brief || wizardNotes,
          ai_suggested_services: aiExtractionResult?.suggested_additional_services || [],
          special_requirements: wizardNotes,
        }),
      });
      addToast({
        type: 'success',
        title: 'Requirement Saved',
        message: 'Your D2C marketing brief has been saved. Generating updated agency matches...',
      });
      setShowWizardModal(false);
      setActiveTab('recommendations');
      loadRecommendations();
    } catch (err: any) {
      addToast({ type: 'error', title: 'Save Failed', message: err.message || 'Could not save requirement.' });
    }
  };

  // Submit Quote Request
  const handleSubmitQuoteRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !orgId || !selectedAgencyForQuote) return;
    if (!rfpConsent) {
      addToast({ type: 'warning', title: 'Consent Required', message: 'Please consent to sharing your project details.' });
      return;
    }
    setIsSubmittingRfp(true);
    try {
      await apiClient('/api/v1/agency/quote-requests', {
        method: 'POST',
        token,
        organizationId: orgId,
        body: JSON.stringify({
          agency_profile_id: selectedAgencyForQuote.id,
          project_title: rfpTitle,
          project_description: rfpDesc,
          budget_inr: rfpBudget,
          budget_type: rfpType,
          timeframe: rfpTimeframe,
          contact_email: rfpEmail || session?.user?.email || '',
          share_contact_consent: rfpConsent,
        }),
      });
      addToast({
        type: 'success',
        title: 'Quote Request Submitted',
        message: `Your RFP has been sent to ${selectedAgencyForQuote.name}. They will review and submit a quotation.`,
      });
      setSelectedAgencyForQuote(null);
      setRfpTitle('');
      setRfpDesc('');
      setActiveTab('requests');
      loadQuoteRequests();
    } catch (err: any) {
      addToast({ type: 'error', title: 'Submission Failed', message: err.message || 'Could not send quote request.' });
    } finally {
      setIsSubmittingRfp(false);
    }
  };

  // Accept Quotation
  const handleAcceptQuotation = async (reqId: string) => {
    if (!token || !orgId) return;
    try {
      await apiClient(`/api/v1/agency/quote-requests/${reqId}/accept`, {
        method: 'POST',
        token,
        organizationId: orgId,
      });
      addToast({
        type: 'success',
        title: 'Quotation Accepted!',
        message: 'Commercial engagement established. You can now coordinate deliverables directly with the agency.',
      });
      loadQuoteRequests();
    } catch (err: any) {
      addToast({ type: 'error', title: 'Acceptance Failed', message: err.message || 'Could not accept quotation.' });
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Marketplace Header */}
      <div className="relative overflow-hidden rounded-3xl bg-forest border border-[#0A6B53] p-6 md:p-8 text-white shadow-option-c">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-emerald/30 text-emerald text-xs font-semibold uppercase tracking-wider">
            <Compass className="w-3.5 h-3.5 text-softorange" />
            MarketPath Agency Connect
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Discover & Connect with Verified D2C Growth Agencies
          </h1>
          <p className="text-xs md:text-sm text-emerald-100 leading-relaxed">
            Describe your product catalogue, business stage, and marketing objectives once. MarketPath’s AI matching engine evaluates real agency portfolios, starting package rates, and verified service credentials to find the right partner for your brand.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={() => {
                setWizardStep(1);
                setShowWizardModal(true);
              }}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors shadow-option-c cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-softorange" />
              Configure AI Requirement Brief
            </button>
            {compareList.length > 0 && (
              <button
                onClick={() => setShowCompareModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-colors cursor-pointer"
              >
                <Scale className="w-4 h-4 text-amber-400" />
                Compare ({compareList.length}) Selected
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Primary Tabs Navigation */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-px">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('discover')}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-xl transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'discover'
                ? 'border-b-2 border-brand-600 text-brand-600 bg-brand-50/40'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Compass className="w-4 h-4" />
            Discover Agencies
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-xl transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'recommendations'
                ? 'border-b-2 border-brand-600 text-brand-600 bg-brand-50/40'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Sparkles className="w-4 h-4 text-brand-500" />
            AI Recommendations
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-xl transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'saved'
                ? 'border-b-2 border-brand-600 text-brand-600 bg-brand-50/40'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Bookmark className="w-4 h-4 text-emerald-600" />
            Saved Shortlist ({savedAgencies.length})
          </button>
          <button
            onClick={() => setActiveTab('requests')}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-xl transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'requests'
                ? 'border-b-2 border-brand-600 text-brand-600 bg-brand-50/40'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Send className="w-4 h-4 text-sky-600" />
            Quote Requests & RFPs ({quoteRequests.length})
          </button>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* TAB 1: DISCOVER AGENCIES                                      */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'discover' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              <div className="relative col-span-1 sm:col-span-2">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search agencies by name, specialty, or services..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full text-xs pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div>
                <select
                  value={selectedService}
                  onChange={(e) => setSelectedService(e.target.value)}
                  className="w-full text-xs px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="">All Services</option>
                  {STANDARD_SERVICES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="w-full text-xs px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="">All Locations</option>
                  <option value="Pune">Pune, MH</option>
                  <option value="Mumbai">Mumbai, MH</option>
                  <option value="Bengaluru">Bengaluru, KA</option>
                  <option value="Delhi">Delhi NCR</option>
                </select>
              </div>

              <div>
                <select
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value ? Number(e.target.value) : '')}
                  className="w-full text-xs px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="">Max Starting Budget</option>
                  <option value="10000">Up to ₹10,000 / mo</option>
                  <option value="15000">Up to ₹15,000 / mo</option>
                  <option value="25000">Up to ₹25,000 / mo</option>
                  <option value="50000">Up to ₹50,000 / mo</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
              <label className="flex items-center gap-2 text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={remoteOnly}
                  onChange={(e) => setRemoteOnly(e.target.checked)}
                  className="rounded text-brand-600 focus:ring-brand-500"
                />
                Remote-capable agencies only
              </label>
              <span className="text-slate-400 font-mono text-[11px]">
                Showing {agencies.length} registered providers
              </span>
            </div>
          </div>

          {/* Agencies Grid */}
          {isLoading ? (
            <div className="py-16 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-brand-500" />
              Searching verified agency database...
            </div>
          ) : agencies.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-white border border-slate-200 text-slate-500 space-y-3">
              <AlertTriangle className="w-8 h-8 mx-auto text-amber-500" />
              <p className="font-semibold text-slate-800">No Agencies Found Matching Filter Criteria</p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Try widening your location, budget, or service filters to find matching service providers.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {agencies.map((agency) => {
                const isSaved = savedIds.has(agency.id);
                const isCompared = compareList.some((a) => a.id === agency.id);

                return (
                  <div
                    key={agency.id}
                    className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all flex flex-col justify-between space-y-4"
                  >
                    <div className="space-y-3">
                      {/* Card Header */}
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <h3 className="font-bold text-slate-900 text-base">{agency.name}</h3>
                            {agency.is_demo && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                                DEMO PROFILE
                              </span>
                            )}
                            {agency.verification_status === 'verified' && (
                              <span title="Verified Partner Agency">
                                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3 h-3 text-slate-400" />
                              {agency.city}, {agency.state}
                            </span>
                            <span>•</span>
                            <span className="text-[11px] font-medium text-slate-600">
                              {agency.remote_or_local === 'both' ? 'Remote + Local' : agency.remote_or_local}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => handleToggleSave(agency, e)}
                            title={isSaved ? 'Remove from Shortlist' : 'Save Agency'}
                            className={`p-1.5 rounded-lg border transition-colors cursor-pointer ${
                              isSaved
                                ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                                : 'bg-slate-50 text-slate-400 border-slate-200 hover:text-slate-600'
                            }`}
                          >
                            <Bookmark className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Tagline & Description */}
                      <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                        {agency.description}
                      </p>

                      {/* Category Specialties */}
                      <div className="flex flex-wrap gap-1.5">
                        {agency.category_specialties.slice(0, 3).map((cat) => (
                          <span
                            key={cat}
                            className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-700"
                          >
                            {cat}
                          </span>
                        ))}
                      </div>

                      {/* Service Capabilities */}
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                          Key Capabilities
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {agency.service_offerings.slice(0, 3).map((srv) => (
                            <span
                              key={srv}
                              className="px-2 py-0.5 rounded text-[10px] bg-brand-50 text-forest border border-brand-200 font-medium"
                            >
                              {srv}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Bottom Pricing & Actions */}
                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Starting Retainer</span>
                        <span className="font-extrabold text-sm text-slate-900">
                          ₹{agency.min_budget_inr.toLocaleString('en-IN')}{' '}
                          <span className="text-xs font-normal text-slate-500">/mo</span>
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={(e) => handleToggleCompare(agency, e)}
                          title="Compare Agency"
                          className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border cursor-pointer ${
                            isCompared
                              ? 'bg-amber-50 text-amber-700 border-amber-300'
                              : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          <Scale className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedAgencyForQuote(agency);
                            setRfpTitle(`Growth Engagement with ${org?.name || 'My Brand'}`);
                          }}
                          className="px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold cursor-pointer shadow-xs"
                        >
                          Request Quote
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 2: AI RECOMMENDATIONS                                     */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'recommendations' && (
        <div className="space-y-6">
          {/* Active Brief Summary Card */}
          <div className="p-5 rounded-2xl bg-softbeige border border-bordergrey shadow-option-c flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-600 text-white uppercase tracking-wider">
                  Active Brand Brief
                </span>
                <span className="text-xs font-bold text-charcoal">
                  {activeRequirement?.brand_name || org?.name} • {activeRequirement?.product_category || 'Home Decor'}
                </span>
              </div>
              <p className="text-xs text-mutedgrey max-w-2xl">
                {activeRequirement?.ai_search_brief ||
                  'Currently evaluating verified agencies with capability in photography, Instagram management, and Meta Ads.'}
              </p>
              <div className="flex flex-wrap gap-2 pt-1 text-[11px] text-mutedgrey font-medium">
                <span>Budget: ₹{(activeRequirement?.monthly_budget_inr || 15000).toLocaleString('en-IN')}/mo</span>
                <span>•</span>
                <span>Location: {activeRequirement?.location || 'Pune, India'}</span>
                <span>•</span>
                <span>Requested Services: {(activeRequirement?.required_services || ['Photography', 'Meta Ads']).join(', ')}</span>
              </div>
            </div>

            <button
              onClick={() => {
                setWizardStep(1);
                setShowWizardModal(true);
              }}
              className="px-3.5 py-2 rounded-xl bg-purewhite border border-bordergrey text-forest hover:bg-warmwhite text-xs font-bold shrink-0 transition-colors cursor-pointer shadow-2xs"
            >
              Modify Marketing Brief
            </button>
          </div>

          {/* Recommendations List */}
          {isMatchingLoading ? (
            <div className="py-16 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-brand-500" />
              Running weighted matching algorithm against active agencies...
            </div>
          ) : recommendations.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-white border border-slate-200 text-slate-500 space-y-3">
              <AlertTriangle className="w-8 h-8 mx-auto text-amber-500" />
              <p className="font-semibold text-slate-800">No Eligible Recommendations Found</p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                No agencies currently meet the strict eligibility threshold for your budget and location. Click above to adjust your brief parameters.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendations.map((match) => {
                const ag = match.agency;
                return (
                  <div
                    key={ag.id}
                    className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 shadow-xs transition-all space-y-4"
                  >
                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-bold text-slate-900 text-base">{ag.name}</h3>
                          {ag.is_demo && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                              DEMO PROFILE
                            </span>
                          )}
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-200">
                            {match.match_score}% Match Score
                          </span>
                          {ag.verification_status === 'verified' && (
                            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                              <ShieldCheck className="w-3 h-3" />
                              Verified Partner
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-600">{ag.tagline}</p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => {
                            setSelectedAgencyForQuote(ag);
                            setRfpTitle(`Growth Engagement with ${org?.name || 'My Brand'}`);
                          }}
                          className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold cursor-pointer shadow-xs"
                        >
                          Request Quotation
                        </button>
                      </div>
                    </div>

                    {/* Transparent Match Reason Pill Box */}
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs">
                      <div className="flex items-start gap-2">
                        <Sparkles className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold text-slate-900">{match.explanation.why_matched}</p>
                          <p className="text-[11px] text-slate-600 mt-0.5">
                            {match.explanation.budget_compatibility_note} • {match.explanation.location_compatibility_note}
                          </p>
                        </div>
                      </div>

                      {match.explanation.portfolio_highlights.length > 0 && (
                        <div className="pt-2 border-t border-slate-200/60 flex items-center gap-2 text-[11px] text-slate-500">
                          <span className="font-bold text-slate-700">Verified Experience:</span>
                          <span>{match.explanation.portfolio_highlights.join(' | ')}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 3: SAVED SHORTLIST                                        */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'saved' && (
        <div className="space-y-4">
          {savedAgencies.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-white border border-slate-200 text-slate-500">
              <Bookmark className="w-8 h-8 mx-auto text-slate-300 mb-2" />
              <p className="font-semibold text-slate-800">Your Shortlist is Empty</p>
              <p className="text-xs text-slate-500 mt-1">
                Bookmark agencies while browsing the directory to compare and request quotes in bulk.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {savedAgencies.map((agency) => (
                <div
                  key={agency.id}
                  className="p-5 rounded-2xl bg-white border border-slate-200 flex flex-col justify-between space-y-3"
                >
                  <div>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <h3 className="font-bold text-slate-900">{agency.name}</h3>
                      {agency.is_demo && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                          DEMO PROFILE
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">{agency.city}, {agency.state}</p>
                    <p className="text-xs text-slate-600 mt-2 line-clamp-2">{agency.description}</p>
                  </div>
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">
                      ₹{agency.min_budget_inr.toLocaleString('en-IN')}/mo
                    </span>
                    <button
                      onClick={() => {
                        setSelectedAgencyForQuote(agency);
                        setRfpTitle(`Growth Engagement with ${org?.name || 'My Brand'}`);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold"
                    >
                      Request Quote
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 4: QUOTE REQUESTS & RFPS                                  */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'requests' && (
        <div className="space-y-4">
          {quoteRequests.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-white border border-slate-200 text-slate-500">
              <Send className="w-8 h-8 mx-auto text-slate-300 mb-2" />
              <p className="font-semibold text-slate-800">No Quote Requests Submitted Yet</p>
              <p className="text-xs text-slate-500 mt-1">
                Discover agencies and submit an RFP brief to receive custom deliverables and pricing proposals.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {quoteRequests.map((req) => (
                <div
                  key={req.id}
                  className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 shadow-xs space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-slate-900 text-sm">{req.project_title}</h4>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                          {req.status.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Target Agency: <span className="font-semibold text-slate-700">{req.agency_name || 'Partner Agency'}</span> • Budget: ₹{req.budget_inr.toLocaleString('en-IN')} ({req.budget_type})
                      </p>
                    </div>

                    {req.status === 'quotation_sent' && (
                      <button
                        onClick={() => handleAcceptQuotation(req.id)}
                        className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors shadow-xs cursor-pointer"
                      >
                        Accept Quotation
                      </button>
                    )}
                  </div>

                  <p className="text-xs text-slate-600">{req.project_description}</p>

                  {/* Agency Response Box */}
                  {req.agency_response_notes && (
                    <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-200/80 text-xs space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-emerald-950">Agency Formal Quotation</span>
                        <span className="font-extrabold text-emerald-800">
                          ₹{req.quotation_amount_inr?.toLocaleString('en-IN')}
                        </span>
                      </div>
                      <p className="text-emerald-900">{req.agency_response_notes}</p>
                      {req.quotation_deliverables && req.quotation_deliverables.length > 0 && (
                        <div className="pt-1">
                          <span className="font-semibold text-emerald-950 block text-[11px]">Proposed Deliverables:</span>
                          <ul className="list-disc list-inside text-[11px] text-emerald-800">
                            {req.quotation_deliverables.map((del, i) => (
                              <li key={i}>{del}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL 1: AI REQUIREMENT ONBOARDING WIZARD                     */}
      {/* ------------------------------------------------------------- */}
      <Modal
        isOpen={showWizardModal}
        onClose={() => setShowWizardModal(false)}
        title="AI Requirement Onboarding Wizard"
        maxWidth="2xl"
      >
        <div className="space-y-5">
          {/* Wizard Step Indicator */}
          <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-3">
            <span className={`font-bold ${wizardStep === 1 ? 'text-brand-600' : 'text-slate-400'}`}>
              1. Brand & Objectives
            </span>
            <span>→</span>
            <span className={`font-bold ${wizardStep === 2 ? 'text-brand-600' : 'text-slate-400'}`}>
              2. Services & Budget
            </span>
            <span>→</span>
            <span className={`font-bold ${wizardStep === 3 ? 'text-brand-600' : 'text-slate-400'}`}>
              3. AI Search Brief
            </span>
          </div>

          {wizardStep === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Brand Name</label>
                  <input
                    type="text"
                    value={wizardBrand}
                    onChange={(e) => setWizardBrand(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Product Category</label>
                  <input
                    type="text"
                    value={wizardCategory}
                    onChange={(e) => setWizardCategory(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Business Stage</label>
                  <select
                    value={wizardStage}
                    onChange={(e) => setWizardStage(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="Early Stage (<₹5L/mo)">Early Stage (&lt;₹5L/mo)</option>
                    <option value="Scaling (₹5L-₹25L/mo)">Scaling (₹5L-₹25L/mo)</option>
                    <option value="Mature (>₹25L/mo)">Mature (&gt;₹25L/mo)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Location (City)</label>
                  <input
                    type="text"
                    value={wizardLocation}
                    onChange={(e) => setWizardLocation(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-2">Select Core Business Objectives</label>
                <div className="flex flex-wrap gap-2">
                  {STANDARD_OBJECTIVES.map((obj) => {
                    const isSelected = wizardObjectives.includes(obj);
                    return (
                      <button
                        type="button"
                        key={obj}
                        onClick={() => {
                          setWizardObjectives((prev) =>
                            isSelected ? prev.filter((o) => o !== obj) : [...prev, obj]
                          );
                        }}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                          isSelected
                            ? 'bg-brand-50 text-brand-700 border-brand-300 font-bold'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        {obj}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setWizardStep(2)}
                  className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs"
                >
                  Next: Services & Budget →
                </button>
              </div>
            </div>
          )}

          {wizardStep === 2 && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-2">
                  Select Required Services (from 16 Approved Categories)
                </label>
                <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto p-1">
                  {STANDARD_SERVICES.map((srv) => {
                    const isSelected = wizardServices.includes(srv);
                    return (
                      <button
                        type="button"
                        key={srv}
                        onClick={() => {
                          setWizardServices((prev) =>
                            isSelected ? prev.filter((s) => s !== srv) : [...prev, srv]
                          );
                        }}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                          isSelected
                            ? 'bg-brand-50 text-forest border-brand-300 font-bold'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        {srv}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Monthly Marketing Service Budget (INR)
                </label>
                <input
                  type="number"
                  value={wizardMonthlyBudget}
                  onChange={(e) => setWizardMonthlyBudget(Number(e.target.value))}
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono"
                />
                <span className="text-[11px] text-slate-400 mt-0.5 block">
                  Excludes ad media spend paid directly to Meta/Google.
                </span>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Brand Specific Directives or Notes
                </label>
                <textarea
                  rows={2}
                  value={wizardNotes}
                  onChange={(e) => setWizardNotes(e.target.value)}
                  placeholder="e.g. Handmade ceramics, need studio photoshoot and reels for Instagram..."
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => setWizardStep(1)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs"
                >
                  ← Back
                </button>
                <button
                  type="button"
                  onClick={handleRunAiWizard}
                  disabled={isAiExtracting}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs cursor-pointer shadow-xs"
                >
                  {isAiExtracting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Analyzing with Gemini AI...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      Analyze & Generate Brief →
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {wizardStep === 3 && aiExtractionResult && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-softbeige border border-bordergrey text-xs space-y-2">
                <span className="font-bold text-forest block">AI Formulated Agency Search Brief:</span>
                <p className="text-charcoal leading-relaxed">{aiExtractionResult.search_brief}</p>
              </div>

              {aiExtractionResult.suggested_additional_services?.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs">
                  <span className="font-bold text-amber-900 block mb-1">
                    Suggested Complementary Services:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {aiExtractionResult.suggested_additional_services.map((s: string) => (
                      <span key={s} className="px-2 py-0.5 rounded text-[10px] bg-white border border-amber-300 text-amber-900 font-medium">
                        + {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="font-bold text-slate-800 block">Budget Advisory:</span>
                <p className="text-slate-600 mt-0.5">{aiExtractionResult.budget_advisory}</p>
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => setWizardStep(2)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs"
                >
                  ← Edit Inputs
                </button>
                <button
                  type="button"
                  onClick={handleSaveWizardRequirement}
                  className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs shadow-xs cursor-pointer"
                >
                  Confirm & View Agency Matches
                </button>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* ------------------------------------------------------------- */}
      {/* MODAL 2: REQUEST QUOTATION (RFP) MODAL                        */}
      {/* ------------------------------------------------------------- */}
      <Modal
        isOpen={Boolean(selectedAgencyForQuote)}
        onClose={() => setSelectedAgencyForQuote(null)}
        title={`Request Quotation from ${selectedAgencyForQuote?.name}`}
        maxWidth="lg"
      >
        {selectedAgencyForQuote && (
          <form onSubmit={handleSubmitQuoteRequest} className="space-y-4">
            <p className="text-xs text-slate-500">
              Submit your project scope and budget. {selectedAgencyForQuote.name} will review your brief and respond with a formal quotation.
            </p>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Project Title</label>
              <input
                type="text"
                value={rfpTitle}
                onChange={(e) => setRfpTitle(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Scope & Deliverables Needed</label>
              <textarea
                rows={3}
                value={rfpDesc}
                onChange={(e) => setRfpDesc(e.target.value)}
                required
                placeholder="Describe your catalogue size, photoshoot requirements, or ad scaling goals..."
                className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Budget (INR)</label>
                <input
                  type="number"
                  value={rfpBudget}
                  onChange={(e) => setRfpBudget(Number(e.target.value))}
                  required
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Billing Type</label>
                <select
                  value={rfpType}
                  onChange={(e) => setRfpType(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="monthly">Monthly Retainer</option>
                  <option value="one_time">Fixed Project</option>
                </select>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <label className="flex items-start gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rfpConsent}
                  onChange={(e) => setRfpConsent(e.target.checked)}
                  className="rounded text-brand-600 focus:ring-brand-500 mt-0.5"
                />
                <span>
                  I consent to sharing my business brief and registered contact details with{' '}
                  <strong>{selectedAgencyForQuote.name}</strong> for the sole purpose of receiving a commercial proposal.
                </span>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedAgencyForQuote(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmittingRfp}
                className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs shadow-xs cursor-pointer"
              >
                {isSubmittingRfp ? 'Submitting...' : 'Submit Quote Request'}
              </button>
            </div>
          </form>
        )}
      </Modal>

      {/* ------------------------------------------------------------- */}
      {/* MODAL 3: SIDE-BY-SIDE COMPARISON MODAL                        */}
      {/* ------------------------------------------------------------- */}
      <Modal
        isOpen={showCompareModal}
        onClose={() => setShowCompareModal(false)}
        title={`Compare Agencies (${compareList.length})`}
        maxWidth="2xl"
      >
        <div className="space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border border-slate-200 rounded-xl overflow-hidden">
              <thead className="bg-slate-50 text-slate-700 uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-3 border-b border-r border-slate-200">Metric</th>
                  {compareList.map((a) => (
                    <th key={a.id} className="py-2.5 px-3 border-b border-slate-200">
                      {a.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="py-2.5 px-3 font-bold border-r border-slate-100 bg-slate-50/50">Location</td>
                  {compareList.map((a) => (
                    <td key={a.id} className="py-2.5 px-3">
                      {a.city}, {a.state}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-bold border-r border-slate-100 bg-slate-50/50">Min Budget</td>
                  {compareList.map((a) => (
                    <td key={a.id} className="py-2.5 px-3 font-extrabold text-slate-900">
                      ₹{a.min_budget_inr.toLocaleString('en-IN')}/mo
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-bold border-r border-slate-100 bg-slate-50/50">Team Size</td>
                  {compareList.map((a) => (
                    <td key={a.id} className="py-2.5 px-3">
                      {a.team_size}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-bold border-r border-slate-100 bg-slate-50/50">Verification</td>
                  {compareList.map((a) => (
                    <td key={a.id} className="py-2.5 px-3">
                      {a.verification_status === 'verified' ? (
                        <span className="text-emerald-600 font-bold">Verified Partner</span>
                      ) : (
                        <span className="text-slate-500">Registered</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-bold border-r border-slate-100 bg-slate-50/50">Core Services</td>
                  {compareList.map((a) => (
                    <td key={a.id} className="py-2.5 px-3">
                      {a.service_offerings.slice(0, 3).join(', ')}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center pt-2">
            <button
              onClick={() => setCompareList([])}
              className="text-xs text-rose-600 hover:underline cursor-pointer"
            >
              Clear Comparison List
            </button>
            <button
              onClick={() => setShowCompareModal(false)}
              className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold"
            >
              Close Comparison
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
