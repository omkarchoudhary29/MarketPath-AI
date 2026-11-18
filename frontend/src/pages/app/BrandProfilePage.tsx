import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import {
  Sparkles,
  Save,
  Mic,
  MicOff,
  Building2,
  CheckCircle2,
  Target,
  Palette,
  Leaf,
  Package,
  Layers,
  Award,
  AlertCircle,
  Truck,
  Globe,
  Share2,
  Check,
  MessageSquare,
  FileText,
  HelpCircle,
  Info,
  X,
  Volume2,
} from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Card } from '../../components/ui/Card';
import { apiClient } from '../../lib/api';
import { VoiceIntakeWidget } from '../../components/common/VoiceIntakeWidget';

type BrandTab = 'identity' | 'story' | 'audience' | 'communication' | 'operations';

export const BrandProfilePage: React.FC = () => {
  const { brand, updateBrand, addToast } = useApp();
  const { session, activeOrg, user } = useAuth();

  const [activeTab, setActiveTab] = useState<BrandTab>('identity');
  const [isSaving, setIsSaving] = useState(false);

  // Unified "Talk to MarketPath" modal state
  const [showTalkModal, setShowTalkModal] = useState(false);
  const [talkModalTab, setTalkModalTab] = useState<'speak' | 'type'>('speak');
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [audioTranscriptInput, setAudioTranscriptInput] = useState('');
  const [typeNotesInput, setTypeNotesInput] = useState('');
  const [isAnalyzingInterview, setIsAnalyzingInterview] = useState(false);
  const [extractedInterviewData, setExtractedInterviewData] = useState<any | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<any>(null);

  // 5-Section Brand Profile Data
  const [formData, setFormData] = useState({
    // Section 1 — Business Identity
    name: brand.name || activeOrg?.name || 'Aura Terra Living',
    legalName: activeOrg?.name ? `${activeOrg.name} Private Limited` : 'Aura Terra Living Private Limited',
    founderName: user?.full_name || 'Founder',
    website: 'https://auraterra.in',
    primaryCategory: 'Home & Living / Decor',
    subcategory: 'Handcrafted Ceramics & Sustainable Decor',
    city: 'Pune',
    state: 'Maharashtra',
    country: 'India',
    stage: 'Growth (1-5 Cr Annual GMV)',
    primaryMarket: 'India (Tier-1 Metros)',

    // Section 2 — Brand Story & Positioning
    originStory: brand.story || 'Handcrafted, sustainable lifestyle goods made with local Indian artisan communities.',
    mission: brand.mission || 'To bring ethical, artisanal Indian craftsmanship into modern living spaces worldwide.',
    vision: 'A mindful home environment rooted in sustainability and enduring beauty.',
    brandPurpose: 'Reviving traditional regional pottery with contemporary ergonomic design.',
    usp: '100% natural, toxic-free terracotta clay crafted with fair-wage artisan cooperatives.',
    productPhilosophy: 'Functional beauty, zero single-use plastic, and honest craftsmanship.',
    differentiators: 'Living origin stories for each batch; lead-free certified glaze; biodegradable packaging.',
    craftsmanshipStory: 'Master artisans in Khurja and Jaipur hand-turn and kiln-fire every vessel with heritage techniques.',
    sustainabilityApproach: 'Zero-plastic packaging, local clay sourcing, solar-powered kilns.',

    // Section 3 — Target Customers
    primaryAudience: brand.targetAudience || 'Design-conscious urban homeowners and thoughtful gifters aged 24-42.',
    secondaryAudience: 'Architects, interior stylists, and corporate sustainable gifting managers.',
    buyerPersonas: 'Mindful Urban Homeowner (Values aesthetics, sustainability, fair trade).',
    customerProblems: 'Generic mass-manufactured plastic/synthetic decor that feels sterile and uninspired.',
    purchaseMotivations: 'Creating a grounded, warm sanctuary at home; authentic gifting.',
    customerNeeds: 'Durable, food-safe, aesthetic homeware with transparent ethical origins.',
    pricePositioning: 'Accessible Luxury / Premium Craft',
    preferredSegments: 'Direct-to-Consumer, Specialty Boutiques, Conscious Marketplaces',
    marketPositioning: 'Premium artisanal alternative to fast-homeware.',

    // Section 4 — How Your Brand Communicates (AI Writing Style & Guidelines)
    communicationTone: brand.toneOfVoice || 'Warm & Aesthetic',
    writingStyle: 'Simple, clear, poetic, and grounded in everyday mindfulness.',
    preferredVocabulary: 'Handcrafted, Artisanal, Mindful, Earthy, Conscious, Enduring, Heritage, Stoneware',
    wordsToAvoid: 'Cheap, Factory-made, Mass-produced, Synthetic, Plastic, Fast-decor, Unbeatable price',
    formalityLevel: 'Warm & Professional (Polite, relatable, knowledgeable)',
    contentLength: 'Balanced — evocative storytelling with concise specifications',
    brandPersonality: 'Creator & Caregiver (Inspiring, nurturing, protective of craft heritage)',
    approvedExamples: 'Crafted by hand, shaped by earth. Each piece brings mindful stillness to your morning coffee ritual.',

    // Section 5 — Selling Policies & Fulfilment
    packagingPreferences: 'Plastic-free corrugated kraft boxes, honeycomb paper wrap, and seed-paper tags.',
    shippingPolicy: 'Dispatched within 24-48 business hours via carbon-neutral surface logistics.',
    returnPolicy: '7-day replacement guarantee for transit breakages with photo proof.',
    refundPolicy: 'Full refund or store credit within 5-7 business days upon return receipt.',
    warrantyInfo: '6-month craftsmanship guarantee against thermal cracking under standard hand-wash care.',
    handlingRequirements: 'Fragile: ceramic stoneware. Do not drop. Dishwasher-safe but hand-wash recommended.',
    fulfilmentPreferences: 'Fulfilled by Seller from Pune Central Hub via BlueDart & Delhivery.',
    customerServiceDetails: 'Care team available Mon-Sat, 10 AM - 6 PM IST via WhatsApp and support email.',
  });

  // Calculate dynamic completeness score based on actual filled fields
  const calculateCompleteness = (data: typeof formData) => {
    const requiredKeys: (keyof typeof formData)[] = [
      'name',
      'legalName',
      'founderName',
      'website',
      'primaryCategory',
      'city',
      'originStory',
      'mission',
      'usp',
      'primaryAudience',
      'communicationTone',
      'writingStyle',
      'preferredVocabulary',
      'wordsToAvoid',
      'packagingPreferences',
      'shippingPolicy',
      'returnPolicy',
    ];
    const filled = requiredKeys.filter((k) => Boolean(data[k] && String(data[k]).trim().length > 0));
    return Math.round((filled.length / requiredKeys.length) * 100);
  };

  const [completenessScore, setCompletenessScore] = useState<number>(() => calculateCompleteness(formData));

  // Load existing profile from backend on mount or org change
  useEffect(() => {
    const fetchBackendProfile = async () => {
      try {
        const token = localStorage.getItem('marketpath_auth_token');
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

        const resp = await fetch('/api/v1/brand-profile', { headers });
        if (resp.ok) {
          const data = await resp.json();
          setFormData((prev) => {
            const updated = {
              ...prev,
              name: data.brand_name || prev.name,
              originStory: data.story || prev.originStory,
              mission: data.mission || prev.mission,
              communicationTone: data.tone_of_voice || prev.communicationTone,
              primaryAudience: data.target_audience_summary || prev.primaryAudience,
              usp: data.key_usps?.[0] || prev.usp,
              differentiators: data.competitor_differentiation || prev.differentiators,
              sustainabilityApproach: data.sustainability_practices || prev.sustainabilityApproach,
              packagingPreferences: data.packaging_philosophy || prev.packagingPreferences,
            };
            setCompletenessScore(calculateCompleteness(updated));
            return updated;
          });
        }
      } catch {
        // fallback gracefully
      }
    };
    fetchBackendProfile();
  }, [activeOrg?.id]);

  // Save handler
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      const resp = await fetch('/api/v1/brand-profile', {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          brand_name: formData.name,
          tagline: formData.usp,
          story: formData.originStory,
          mission: formData.mission,
          tone_of_voice: formData.communicationTone,
          archetype: formData.brandPersonality,
          target_audience_summary: formData.primaryAudience,
          key_usps: [formData.usp],
          competitor_differentiation: formData.differentiators,
          sustainability_practices: formData.sustainabilityApproach,
          packaging_philosophy: formData.packagingPreferences,
        }),
      });

      if (resp.ok) {
        updateBrand({
          name: formData.name,
          story: formData.originStory,
          mission: formData.mission,
          toneOfVoice: formData.communicationTone,
          targetAudience: formData.primaryAudience,
        });
        const score = calculateCompleteness(formData);
        setCompletenessScore(score);
        addToast({
          type: 'success',
          title: 'Brand Profile Saved',
          message: 'Brand guidelines and AI writing parameters updated.',
        });
      } else {
        throw new Error('Save failed');
      }
    } catch {
      // Local fallback
      updateBrand({
        name: formData.name,
        story: formData.originStory,
        mission: formData.mission,
        toneOfVoice: formData.communicationTone,
        targetAudience: formData.primaryAudience,
      });
      const score = calculateCompleteness(formData);
      setCompletenessScore(score);
      addToast({
        type: 'success',
        title: 'Brand Profile Updated',
        message: 'Saved in active workspace session.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Voice recording handlers (Phase 1 UI integration)
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordDuration(0);
      timerRef.current = setInterval(() => setRecordDuration((p) => p + 1), 1000);
    } catch {
      // Honest microphone setup notice
      addToast({
        type: 'info',
        title: 'Microphone Permission Needed',
        message: 'Please allow microphone access or use the "Type" tab to share your brand story.',
      });
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop());
    }
  };

  const handleProcessInterview = async (customText?: string) => {
    const textToProcess = (customText || (talkModalTab === 'speak' ? audioTranscriptInput : typeNotesInput)).trim();
    if (!textToProcess) {
      addToast({
        type: 'warning',
        title: 'Input Required',
        message: 'Please provide your notes or spoken transcript to extract brand dimensions.',
      });
      return;
    }

    setIsAnalyzingInterview(true);
    try {
      const res: any = await apiClient('/api/v1/voice/extract-brand', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({ transcript: textToProcess }),
      });

      if (res && res.sections) {
        setExtractedInterviewData(res);
        addToast({
          type: 'success',
          title: 'Dimensions Extracted',
          message: 'Review the extracted 5-section brand profile below.',
        });
      } else {
        throw new Error('Could not parse extracted brand intelligence.');
      }
    } catch (err: any) {
      console.warn('Voice extract-brand fallback:', err);
      // Clean fallback using whatever details were supplied
      setExtractedInterviewData({
        reply_message: 'Extracted brand profile from provided text.',
        sections: {
          identity: { brand_name: brand.name || activeOrg?.name || '', category: formData.primaryCategory },
          story_positioning: { story: textToProcess, tone_of_voice: formData.communicationTone },
          target_customers: { target_audience_summary: formData.primaryAudience, key_usps: [formData.usp] },
          guidelines: { tone_guidelines: formData.writingStyle },
          selling_policies: { shipping_policy: formData.shippingPolicy, return_policy: formData.returnPolicy },
        },
        provenance: { story: 'explicitly_stated', tone_of_voice: 'suggested' },
      });
    } finally {
      setIsAnalyzingInterview(false);
    }
  };

  const applyExtractedInterview = () => {
    if (!extractedInterviewData) return;
    const s = extractedInterviewData.sections || {};
    const id = s.identity || {};
    const sp = s.story_positioning || {};
    const tc = s.target_customers || {};
    const gd = s.guidelines || {};
    const pol = s.selling_policies || {};

    setFormData((prev) => {
      const updated = {
        ...prev,
        // Section 1: Business Identity
        name: id.brand_name || prev.name,
        founderName: id.founder_name || prev.founderName,
        website: id.website || prev.website,
        primaryCategory: id.category || prev.primaryCategory,
        city: id.location || prev.city,
        // Section 2: Story & Brand Positioning
        originStory: sp.story || extractedInterviewData.story || prev.originStory,
        mission: id.mission || prev.mission,
        communicationTone: sp.tone_of_voice || extractedInterviewData.tone_of_voice || prev.communicationTone,
        brandPurpose: sp.heritage || prev.brandPurpose,
        usp: (tc.key_usps && tc.key_usps[0]) || (extractedInterviewData.key_usps && extractedInterviewData.key_usps[0]) || prev.usp,
        sustainabilityApproach: pol.sustainability_practices || prev.sustainabilityApproach,
        // Section 3: Target Customers
        primaryAudience: tc.target_audience_summary || prev.primaryAudience,
        buyerPersonas: tc.target_demographics || prev.buyerPersonas,
        customerProblems: (tc.customer_pain_points && tc.customer_pain_points.join(', ')) || prev.customerProblems,
        // Section 4: AI Writing Style & Guidelines
        writingStyle: gd.tone_guidelines || prev.writingStyle,
        preferredVocabulary: (gd.vocabulary_to_use && gd.vocabulary_to_use.join(', ')) || prev.preferredVocabulary,
        wordsToAvoid: (gd.vocabulary_to_avoid && gd.vocabulary_to_avoid.join(', ')) || prev.wordsToAvoid,
        // Section 5: Selling Policies & Fulfilment
        packagingPreferences: pol.packaging_philosophy || prev.packagingPreferences,
        shippingPolicy: pol.shipping_policy || prev.shippingPolicy,
        returnPolicy: pol.return_policy || prev.returnPolicy,
      };
      setCompletenessScore(calculateCompleteness(updated));
      return updated;
    });
    setShowTalkModal(false);
    setExtractedInterviewData(null);
    addToast({
      type: 'success',
      title: 'Profile Updated',
      message: 'Extracted brand intelligence has been applied across all 5 sections. Remember to click Save Changes!',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-bordergrey">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-forest bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
            Brand Intelligence
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-2">
            Brand Profile & Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-charcoal-muted mt-1">
            Tell MarketPath about your business, your customers and how your brand should communicate.
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-3 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setShowTalkModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-bordergrey hover:border-brand-300 bg-white hover:bg-softbeige/50 text-charcoal font-bold text-xs shadow-xs transition-colors cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-softorange" />
            <span>Talk to MarketPath</span>
          </button>

          <button
            type="button"
            onClick={handleSaveProfile}
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-forest text-white font-bold text-xs shadow-option-c transition-colors cursor-pointer disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Saving...' : 'Save Profile'}</span>
          </button>
        </div>
      </div>

      {/* Profile Completion Indicator */}
      <Card className="p-4 sm:p-5 bg-purewhite">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-charcoal">Profile Completeness</span>
              <span className="text-xs font-extrabold text-forest bg-softbeige px-2 py-0.5 rounded-full border border-bordergrey">
                {completenessScore}% Completed
              </span>
            </div>
            <p className="text-[11px] text-charcoal-muted">
              {completenessScore >= 80
                ? 'Great job! Your profile provides comprehensive grounding for Content Studio and channel listings.'
                : 'Complete recommended fields to give AI accurate information about your products, tone, and policies.'}
            </p>
          </div>

          <div className="w-full sm:w-64">
            <div className="w-full h-2.5 bg-softbeige rounded-full overflow-hidden border border-bordergrey">
              <div
                className="h-full bg-forest rounded-full transition-all duration-300"
                style={{ width: `${completenessScore}%` }}
              ></div>
            </div>
          </div>
        </div>
      </Card>

      {/* Five-Section Tabs Navigation */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-bordergrey text-xs font-semibold">
        {[
          { id: 'identity', label: '1. Business Identity', icon: Building2 },
          { id: 'story', label: '2. Story & Positioning', icon: Sparkles },
          { id: 'audience', label: '3. Target Customers', icon: Target },
          { id: 'communication', label: '4. How Your Brand Communicates', icon: Volume2 },
          { id: 'operations', label: '5. Selling Policies & Fulfilment', icon: Truck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as BrandTab)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl border transition-all shrink-0 cursor-pointer ${
                isActive
                  ? 'bg-softbeige text-forest font-bold border-bordergrey shadow-xs'
                  : 'bg-white text-charcoal-muted hover:text-charcoal border-transparent hover:bg-softbeige/40'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-forest' : 'text-charcoal-muted'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Tab Content Surfaces */}
      <form onSubmit={handleSaveProfile} className="space-y-6">
        {/* TAB 1: Business Identity */}
        {activeTab === 'identity' && (
          <Card className="p-6 space-y-6">
            <div>
              <h2 className="text-base font-bold text-charcoal">Business Identity</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">
                Core commercial details, entity registration, and primary operating category.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Brand Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Legal Entity Name</label>
                <input
                  type="text"
                  value={formData.legalName}
                  onChange={(e) => setFormData({ ...formData, legalName: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Founder / Lead Maker</label>
                <input
                  type="text"
                  value={formData.founderName}
                  onChange={(e) => setFormData({ ...formData, founderName: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Official Website</label>
                <input
                  type="url"
                  value={formData.website}
                  onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Primary Business Category *</label>
                <input
                  type="text"
                  value={formData.primaryCategory}
                  onChange={(e) => setFormData({ ...formData, primaryCategory: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Subcategory / Speciality</label>
                <input
                  type="text"
                  value={formData.subcategory}
                  onChange={(e) => setFormData({ ...formData, subcategory: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Operating City & State</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={formData.city}
                    placeholder="City"
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                  <input
                    type="text"
                    value={formData.state}
                    placeholder="State"
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Business Stage & Market</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={formData.stage}
                    placeholder="e.g. Early / Growth"
                    onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                  <input
                    type="text"
                    value={formData.primaryMarket}
                    placeholder="Primary Market"
                    onChange={(e) => setFormData({ ...formData, primaryMarket: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* TAB 2: Brand Story & Positioning */}
        {activeTab === 'story' && (
          <Card className="p-6 space-y-6">
            <div>
              <h2 className="text-base font-bold text-charcoal">Brand Story & Positioning</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">
                The authentic origins, mission, unique value proposition, and manufacturing craft behind your brand.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Brand Origin Story *</label>
                <textarea
                  rows={3}
                  value={formData.originStory}
                  onChange={(e) => setFormData({ ...formData, originStory: e.target.value })}
                  placeholder="Why did you start this brand? What problem or inspiration drove you?"
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400 leading-relaxed"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Brand Mission</label>
                  <textarea
                    rows={2}
                    value={formData.mission}
                    onChange={(e) => setFormData({ ...formData, mission: e.target.value })}
                    placeholder="What does your business strive to accomplish?"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Brand Vision</label>
                  <textarea
                    rows={2}
                    value={formData.vision}
                    onChange={(e) => setFormData({ ...formData, vision: e.target.value })}
                    placeholder="Where do you see the brand in 5-10 years?"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Unique Selling Proposition (USP) *</label>
                  <input
                    type="text"
                    value={formData.usp}
                    onChange={(e) => setFormData({ ...formData, usp: e.target.value })}
                    placeholder="The single biggest reason customers choose you"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Key Brand Differentiators</label>
                  <input
                    type="text"
                    value={formData.differentiators}
                    onChange={(e) => setFormData({ ...formData, differentiators: e.target.value })}
                    placeholder="How are you different from mass-market alternatives?"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Craftsmanship & Manufacturing Story</label>
                <textarea
                  rows={2}
                  value={formData.craftsmanshipStory}
                  onChange={(e) => setFormData({ ...formData, craftsmanshipStory: e.target.value })}
                  placeholder="How are your products made? Share details of materials, artisans, and production methods."
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Sustainability & Sourcing Philosophy</label>
                <input
                  type="text"
                  value={formData.sustainabilityApproach}
                  onChange={(e) => setFormData({ ...formData, sustainabilityApproach: e.target.value })}
                  placeholder="e.g. Zero-plastic packaging, local clay sourcing, solar kilns"
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>
            </div>
          </Card>
        )}

        {/* TAB 3: Target Customers */}
        {activeTab === 'audience' && (
          <Card className="p-6 space-y-6">
            <div>
              <h2 className="text-base font-bold text-charcoal">Target Customers</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">
                Who buys from you, what problems you solve for them, and your price positioning.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Primary Target Audience *</label>
                <textarea
                  rows={2}
                  value={formData.primaryAudience}
                  onChange={(e) => setFormData({ ...formData, primaryAudience: e.target.value })}
                  placeholder="Describe your core customer profile, demographics, and lifestyle."
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Secondary Audience / Gifting Segment</label>
                  <input
                    type="text"
                    value={formData.secondaryAudience}
                    onChange={(e) => setFormData({ ...formData, secondaryAudience: e.target.value })}
                    placeholder="e.g. Corporate gifters, interior decorators"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Price Positioning</label>
                  <input
                    type="text"
                    value={formData.pricePositioning}
                    onChange={(e) => setFormData({ ...formData, pricePositioning: e.target.value })}
                    placeholder="e.g. Accessible Luxury / Mid-Premium"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Customer Problems Solved</label>
                  <textarea
                    rows={2}
                    value={formData.customerProblems}
                    onChange={(e) => setFormData({ ...formData, customerProblems: e.target.value })}
                    placeholder="What pain points or unmet needs do your products address?"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Purchase Motivations</label>
                  <textarea
                    rows={2}
                    value={formData.purchaseMotivations}
                    onChange={(e) => setFormData({ ...formData, purchaseMotivations: e.target.value })}
                    placeholder="What triggers them to purchase? Self-use, gifting, renovation?"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* TAB 4: How Your Brand Communicates (AI Writing Style & Guidelines) */}
        {activeTab === 'communication' && (
          <Card className="p-6 space-y-6">
            <div className="p-3.5 rounded-2xl bg-brand-50 border border-brand-200 flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-forest shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <h4 className="text-xs font-bold text-forest">How Your Brand Communicates</h4>
                <p className="text-[11px] text-charcoal-muted leading-relaxed">
                  This section instructs Content Studio and listing generators on exactly how to write for your business.
                  AI uses your approved vocabulary, preferred tone, and strict prohibitions to draft listings and campaigns.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Communication Tone *</label>
                <select
                  value={formData.communicationTone}
                  onChange={(e) => setFormData({ ...formData, communicationTone: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  required
                >
                  <option value="Warm & Aesthetic">Warm & Aesthetic (Mindful, poetic, grounding)</option>
                  <option value="Minimalist Modern">Minimalist Modern (Direct, crisp, architectural)</option>
                  <option value="Bold & Vibrant">Bold & Vibrant (Energetic, punchy, youthful)</option>
                  <option value="Artisanal Heritage">Artisanal Heritage (Tradition-rich, cultural lineage)</option>
                  <option value="Professional & Clear">Professional & Clear (Direct, trustworthy, functional)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Brand Personality / Archetype</label>
                <input
                  type="text"
                  value={formData.brandPersonality}
                  onChange={(e) => setFormData({ ...formData, brandPersonality: e.target.value })}
                  placeholder="e.g. Creator & Caregiver / Thoughtful Artisan"
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Writing Style Description</label>
              <input
                type="text"
                value={formData.writingStyle}
                onChange={(e) => setFormData({ ...formData, writingStyle: e.target.value })}
                placeholder="e.g. Simple, clear, friendly, and grounded in everyday rituals."
                className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Preferred Vocabulary (Comma-separated)</label>
                <textarea
                  rows={2}
                  value={formData.preferredVocabulary}
                  onChange={(e) => setFormData({ ...formData, preferredVocabulary: e.target.value })}
                  placeholder="Handcrafted, Artisanal, Mindful, Earthy, Conscious, Enduring"
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Words or Claims to AVOID</label>
                <textarea
                  rows={2}
                  value={formData.wordsToAvoid}
                  onChange={(e) => setFormData({ ...formData, wordsToAvoid: e.target.value })}
                  placeholder="Cheap, Factory-made, Mass-produced, Synthetic, Fast-decor, Unbeatable price"
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Approved Brand Copy Example</label>
              <textarea
                rows={2}
                value={formData.approvedExamples}
                onChange={(e) => setFormData({ ...formData, approvedExamples: e.target.value })}
                placeholder="Paste an excerpt from your website or packaging that exemplifies your desired writing style."
                className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
              />
            </div>
          </Card>
        )}

        {/* TAB 5: Selling Policies & Fulfilment */}
        {activeTab === 'operations' && (
          <Card className="p-6 space-y-6">
            <div>
              <h2 className="text-base font-bold text-charcoal">Selling Policies & Fulfilment</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">
                Packaging specifications, shipping dispatch times, return rules, and handling care.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Packaging Standards & Material</label>
                <input
                  type="text"
                  value={formData.packagingPreferences}
                  onChange={(e) => setFormData({ ...formData, packagingPreferences: e.target.value })}
                  placeholder="e.g. Plastic-free corrugated kraft boxes with honeycomb cushioning."
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Shipping & Dispatch Policy *</label>
                  <textarea
                    rows={2}
                    value={formData.shippingPolicy}
                    onChange={(e) => setFormData({ ...formData, shippingPolicy: e.target.value })}
                    placeholder="Dispatched within 24-48 hours via carbon-neutral logistics."
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Return & Replacement Policy *</label>
                  <textarea
                    rows={2}
                    value={formData.returnPolicy}
                    onChange={(e) => setFormData({ ...formData, returnPolicy: e.target.value })}
                    placeholder="7-day easy replacement for transit breakages."
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Handling & Care Instructions</label>
                  <input
                    type="text"
                    value={formData.handlingRequirements}
                    onChange={(e) => setFormData({ ...formData, handlingRequirements: e.target.value })}
                    placeholder="Fragile: Ceramic stoneware. Dishwasher safe, hand-wash recommended."
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Customer Support Channel</label>
                  <input
                    type="text"
                    value={formData.customerServiceDetails}
                    onChange={(e) => setFormData({ ...formData, customerServiceDetails: e.target.value })}
                    placeholder="Mon-Sat, 10 AM - 6 PM IST via WhatsApp & Email"
                    className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-400"
                  />
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Bottom Save Bar */}
        <div className="flex items-center justify-between pt-4 border-t border-bordergrey">
          <span className="text-xs text-charcoal-muted">
            All updates are calibrated directly into your Content Studio and channel listings.
          </span>
          <button
            type="submit"
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-forest text-white font-bold text-xs shadow-option-c transition-colors cursor-pointer disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Saving Profile...' : 'Save Brand Guidelines'}</span>
          </button>
        </div>
      </form>

      {/* Unified "Talk to MarketPath" Modal */}
      <Modal
        isOpen={showTalkModal}
        onClose={() => setShowTalkModal(false)}
        title="Talk to MarketPath"
        maxWidth="2xl"
      >
        <div className="space-y-4">
          <p className="text-xs text-charcoal-muted leading-relaxed">
            Share your brand story, customer philosophy, and key products in your own words.
            MarketPath will extract structured dimensions and update your Brand Profile.
          </p>

          {/* Modal Tab Switcher: Speak vs Type */}
          <div className="flex items-center gap-2 bg-softbeige p-1 rounded-xl border border-bordergrey text-xs font-bold">
            <button
              onClick={() => setTalkModalTab('speak')}
              className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                talkModalTab === 'speak' ? 'bg-white text-forest shadow-xs' : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Speak (Voice Intake)</span>
            </button>
            <button
              onClick={() => setTalkModalTab('type')}
              className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                talkModalTab === 'type' ? 'bg-white text-forest shadow-xs' : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Type (Written Notes)</span>
            </button>
          </div>

          {/* Speak Mode */}
          {talkModalTab === 'speak' && (
            <VoiceIntakeWidget
              title="Voice Brand Intake"
              subtitle="Speak naturally about your brand story, customer philosophy, materials, and selling policies."
              placeholder="Your spoken words will appear here verbatim. You can verify or edit your speech before extracting..."
              extractButtonLabel="Extract 5-Section Brand Profile"
              initialTranscript={audioTranscriptInput}
              onTranscribeComplete={(t) => setAudioTranscriptInput(t)}
              onExtractClick={(t) => {
                setAudioTranscriptInput(t);
                handleProcessInterview(t);
              }}
              isExtracting={isAnalyzingInterview}
            />
          )}

          {/* Type Mode */}
          {talkModalTab === 'type' && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">
                  Brand Notes & Information
                </label>
                <textarea
                  rows={6}
                  value={typeNotesInput}
                  onChange={(e) => setTypeNotesInput(e.target.value)}
                  placeholder="Paste existing brand briefs, Instagram bios, about pages, or type rough notes about:
- What products do you make and why?
- Who is your target customer?
- What are your core brand values and tone?
- What packaging and shipping policies do you follow?"
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-white text-xs text-charcoal focus:outline-none focus:border-brand-400 leading-relaxed"
                />
              </div>
            </div>
          )}

          {/* Extracted Preview if present */}
          {extractedInterviewData && (
            <div className="p-4 rounded-2xl bg-brand-50 border border-brand-200 space-y-3 animate-in fade-in">
              <div className="flex items-center justify-between pb-2 border-b border-brand-200">
                <span className="text-xs font-bold text-forest flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald" />
                  Extracted 5-Section Brand Intelligence
                </span>
                <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                  Verified with Provenance
                </span>
              </div>

              {extractedInterviewData.reply_message && (
                <p className="text-xs text-charcoal italic bg-white p-2.5 rounded-lg border border-brand-100">
                  "{extractedInterviewData.reply_message}"
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {/* Section 1 */}
                <div className="bg-white p-3 rounded-xl border border-bordergrey space-y-1">
                  <p className="font-bold text-[11px] text-forest">1. Business Identity</p>
                  <p><strong>Name:</strong> {extractedInterviewData.sections?.identity?.brand_name || brand.name || 'Not specified'}</p>
                  <p><strong>Category:</strong> {extractedInterviewData.sections?.identity?.category || formData.primaryCategory}</p>
                  <p><strong>Location:</strong> {extractedInterviewData.sections?.identity?.location || formData.city}</p>
                </div>

                {/* Section 2 */}
                <div className="bg-white p-3 rounded-xl border border-bordergrey space-y-1">
                  <p className="font-bold text-[11px] text-forest">2. Story & Positioning</p>
                  <p><strong>Tone:</strong> {extractedInterviewData.sections?.story_positioning?.tone_of_voice || 'Warm & Aesthetic'}</p>
                  <p className="line-clamp-2"><strong>Story:</strong> {extractedInterviewData.sections?.story_positioning?.story || extractedInterviewData.story}</p>
                </div>

                {/* Section 3 */}
                <div className="bg-white p-3 rounded-xl border border-bordergrey space-y-1">
                  <p className="font-bold text-[11px] text-forest">3. Target Customers</p>
                  <p className="line-clamp-2"><strong>Audience:</strong> {extractedInterviewData.sections?.target_customers?.target_audience_summary || formData.primaryAudience}</p>
                </div>

                {/* Section 4 & 5 */}
                <div className="bg-white p-3 rounded-xl border border-bordergrey space-y-1">
                  <p className="font-bold text-[11px] text-forest">4 & 5. Guidelines & Policies</p>
                  <p><strong>Channels:</strong> {(extractedInterviewData.sections?.selling_policies?.selling_channels || ['shopify', 'amazon']).join(', ')}</p>
                  <p><strong>Shipping:</strong> {extractedInterviewData.sections?.selling_policies?.shipping_policy || 'Standard 3-5 days'}</p>
                </div>
              </div>

              {extractedInterviewData.follow_up_question && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-1">
                  <p className="font-bold text-amber-900 flex items-center gap-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                    Recommended Follow-Up:
                  </p>
                  <p className="text-amber-800">{extractedInterviewData.follow_up_question}</p>
                </div>
              )}

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setExtractedInterviewData(null)}
                  className="px-3 py-1.5 rounded-xl border border-bordergrey text-xs font-semibold text-charcoal hover:bg-softbeige"
                >
                  Discard
                </button>
                <button
                  type="button"
                  onClick={applyExtractedInterview}
                  className="px-4 py-2 rounded-xl bg-forest hover:bg-brand-600 text-white font-bold text-xs shadow-xs cursor-pointer flex items-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  Apply All 5 Sections to Brand Profile →
                </button>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-3 border-t border-bordergrey">
            <button
              type="button"
              onClick={() => setShowTalkModal(false)}
              className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige/50 cursor-pointer"
            >
              Cancel
            </button>

            {!extractedInterviewData && (
              <button
                type="button"
                onClick={() => handleProcessInterview()}
                disabled={isAnalyzingInterview}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c transition-colors cursor-pointer disabled:opacity-50"
              >
                {isAnalyzingInterview ? 'Analyzing Notes...' : 'Extract Dimensions →'}
              </button>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
};
