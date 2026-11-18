import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Sparkles,
  Layers,
  CheckCircle2,
  Send,
  BarChart3,
  Megaphone,
  ChevronDown,
  Building2,
  Package,
  ShieldCheck,
  ShoppingBag,
  Store,
  Share2,
  Zap,
  Mic,
  Calendar,
  Users2,
  Lock,
  Calculator,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  AlertCircle,
  Check,
  Play,
} from 'lucide-react';
import { siteConfig } from '../../config/site';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card, CardContent } from '../../components/ui/Card';
import {
  HeroD2CIllustration,
  CatalogueIllustration,
  OmnichannelHubIllustration,
} from '../../components/common/OptionCIllustrations';
import { RecruiterDemoSection } from '../../components/common/RecruiterDemoSection';

export const HomePage: React.FC = () => {
  const [activeFaq, setActiveFaq] = useState<number | null>(null);
  const [activeChannelGroup, setActiveChannelGroup] = useState<'storefronts' | 'marketplaces' | 'social' | 'quick_commerce'>('storefronts');

  // Interactive ROI Calculator State
  const [activeSkus, setActiveSkus] = useState<number>(45);
  const [currentChannels, setCurrentChannels] = useState<number>(2);

  // Computed Savings
  const hoursSavedPerMonth = Math.round(activeSkus * 0.8 + currentChannels * 12);
  const estimatedAgencyCostSavings = Math.round(hoursSavedPerMonth * 750);

  const categories = [
    'Home & Decor',
    'Fashion & Apparel',
    'Beauty & Personal Care',
    'Food & Beverage',
    'Health & Wellness',
    'Jewelry & Accessories',
    'Baby & Kids',
    'Pet Supplies',
    'Electronics & Gadgets',
    'Sports & Fitness',
    'Art & Collectibles',
    'Books & Stationery',
    'Footwear',
    'Bags & Luggage',
    'Organic & Sustainable',
    'Handcrafted & Artisanal',
    'Gourmet & Confectionery',
    'Gifts & Festive',
    'Kitchen & Dining',
  ];

  const channelDirectory = {
    storefronts: [
      { name: 'Shopify', status: 'Connected / Live Ready', badge: 'Live GraphQL API', desc: 'Direct catalogue sync, inventory tracking, and order ingestion.' },
      { name: 'WooCommerce', status: 'Ready for Connection', badge: 'REST API v3', desc: 'Self-hosted WordPress store sync with multi-variant mapping.' },
    ],
    marketplaces: [
      { name: 'Amazon India', status: 'Roadmap / SP-API Ready', badge: 'Selling Partner API', desc: 'A+ content mapping, Buy Box tracking, and FBA inventory sync.' },
      { name: 'Flipkart', status: 'Roadmap / Sandbox Ready', badge: 'Seller Hub API', desc: 'Category-specific attribute compliance and Flipkart Assured validation.' },
      { name: 'Myntra', status: 'Partner Access Required', badge: 'Partner Hub', desc: 'Fashion and lifestyle syndication with enterprise vendor agreement.' },
      { name: 'Nykaa', status: 'Partner Access Required', badge: 'Vendor Portal', desc: 'Beauty, personal care, and wellness brand catalog syndication.' },
      { name: 'AJIO', status: 'Partner Access Required', badge: 'Reliance Retail', desc: 'Reliance Retail brand supplier onboarding and EDI/REST syndication.' },
    ],
    social: [
      { name: 'Instagram Professional', status: 'Live Ready / App Review', badge: 'Meta Graph API', desc: 'Publish organic carousels, feed posts, and brand story captions.' },
      { name: 'Facebook Shops', status: 'App Review Dependent', badge: 'Commerce Manager', desc: 'Social commerce catalog linking with checkout sync.' },
      { name: 'YouTube Shopping', status: 'Coming Soon', badge: 'Google Partner', desc: 'Tag approved products across brand video content and live streams.' },
    ],
    quick_commerce: [
      { name: 'Zepto', status: 'Partner Access Required', badge: 'Indian Quick Commerce', desc: 'Dark-store 10-minute grocery and retail delivery network in top metro hubs.' },
      { name: 'Blinkit', status: 'Partner Access Required', badge: 'Zomato Commerce', desc: 'Instant hyperlocal dispatch with localized batch inventory tracking.' },
      { name: 'Swiggy Instamart', status: 'Partner Access Required', badge: 'Brand Partner', desc: 'Urban quick commerce procurement and FMCG shelf placement.' },
      { name: 'Tata Neu', status: 'Coming Soon', badge: 'Tata Digital', desc: 'Unified omni-channel ecosystem syndication.' },
    ],
  };

  const faqs = [
    {
      q: 'What is MarketPath AI and what is its core promise?',
      a: 'MarketPath AI is the unified commerce and growth operating platform for emerging Indian product brands. Our core promise: "Run your product business across channels, effortlessly. Manage products, publish across marketplaces, automate marketing and understand growth — all from one platform."',
    },
    {
      q: 'How does MarketPath ensure AI will never hallucinate specs or certifications?',
      a: 'We use strict Fact-Checking Guardrails powered by Google Gemini 2.5 Flash. All generation prompts are grounded deterministically in your verified master product records (ingredients, dimensions, certifications). The AI is strictly constrained from inventing unlisted benefits or fake claims.',
    },
    {
      q: 'Will AI ever publish listings or launch ad spend automatically?',
      a: 'Never. MarketPath enforces a strict Human-in-the-Loop policy across the entire platform. AI generates suggestions, but a human brand owner or marketer must explicitly review and click approve before any channel listing publishes or ad budget launches.',
    },
    {
      q: 'Does MarketPath take custody of my advertising budget?',
      a: 'Never. You maintain 100% direct ownership of your advertising accounts with Meta and Google. MarketPath plans campaigns, generates creatives, and enforces your approved budget caps. You pay advertising media spend directly to the advertising networks.',
    },
    {
      q: 'What is MarketPath Agency Connect?',
      a: 'Agency Connect is our integrated discovery directory connecting D2C brands with verified marketing, creative, and catalog agencies across 10 service categories. Demo agencies are clearly flagged, and founder private contact details (personal phone/email) and cost prices are strictly sanitized to protect your privacy.',
    },
    {
      q: 'Why did MarketPath replace standalone public pricing with Free Consultation?',
      a: 'Emerging Indian D2C brands vary greatly by SKU count, sales channels, and stage of maturity. We believe in high-touch, consultative onboarding where our product specialists evaluate your catalog and tailor an expansion roadmap. Authenticated users still manage their plans and quotas transparently under Settings > Billing.',
    },
    {
      q: 'How does Voice-Based Brand Onboarding work?',
      a: 'Instead of filling out tedious forms, founders can record their voice directly in the browser describing their origin story, target audience, and key USPs. Gemini 2.5 Flash transcribes and extracts the attributes into structured fields. You review, edit, and confirm before saving.',
    },
    {
      q: 'What is your integration policy for channels like Zepto and AJIO?',
      a: 'We uphold a strict Zero-Faking Policy. We never claim a connection is live when it requires enterprise partner access. Indian quick-commerce networks like Zepto and marketplaces like AJIO require brand partner agreements. We display "Partner Access Required" and provide an AI Setup Assistant to guide your onboarding.',
    },
  ];

  return (
    <div className="space-y-24 sm:space-y-28 pb-20">
      {/* SECTION 1: HERO SECTION */}
      <section className="relative pt-10 pb-16 md:pt-16 md:pb-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Column: Core Value Proposition */}
            <div className="lg:col-span-7 space-y-6 text-left">
              {/* Central Promise Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-softbeige border border-bordergrey text-forest text-xs font-bold tracking-tight">
                <span className="w-2 h-2 rounded-full bg-brand-600 animate-pulse" />
                <span>One Product Catalogue • Connected Channels • Unified Growth</span>
              </div>

              {/* Master Approved Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-charcoal tracking-tight leading-[1.12]">
                Run your product business across channels,{' '}
                <span className="text-brand-600 underline decoration-softorange decoration-4 underline-offset-6">
                  effortlessly.
                </span>
              </h1>

              {/* Approved Supporting Text */}
              <p className="text-lg sm:text-xl text-charcoal-muted max-w-2xl font-normal leading-relaxed">
                Manage products, publish across marketplaces, automate marketing and understand growth — all from one platform.
              </p>

              {/* Call to Actions */}
              <div className="pt-2 flex flex-wrap items-center gap-3">
                <Link to="/signup">
                  <Button size="lg" className="px-6 py-3.5 text-base shadow-sm">
                    Start Free Workspace <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
                <Link to="/login?type=company">
                  <Button variant="secondary" size="lg" className="px-6 py-3.5 text-base bg-softorange/10 hover:bg-softorange/20 border-softorange/40 text-charcoal">
                    <Play className="w-4 h-4 mr-2 text-softorange fill-softorange" /> Explore Live Demo
                  </Button>
                </Link>
                <a
                  href={siteConfig.githubRepoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="View MarketPath AI source code on GitHub"
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-bordergrey bg-white hover:bg-softbeige/50 text-sm font-bold text-charcoal shadow-xs transition-colors"
                >
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                  <span>GitHub</span>
                </a>
              </div>

              {/* Trust Guarantees */}
              <div className="pt-3 flex flex-wrap items-center gap-y-2 gap-x-5 text-xs text-charcoal-muted font-medium">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald" /> No Credit Card Required
                </span>
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-brand-600" /> Scoped API & OAuth Credentials
                </span>
                <span className="flex items-center gap-1.5">
                  <Lock className="w-4 h-4 text-forest font-semibold" /> Mandatory Human Approval Gate
                </span>
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-softorange" /> Grounded Spec Accuracy
                </span>
              </div>
            </div>

            {/* Right Column: Friendly Option C D2C Illustration */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="w-full max-w-lg bg-white rounded-3xl p-4 sm:p-6 border border-bordergrey shadow-option-c-md hover:shadow-option-c-lg transition-all duration-300">
                <HeroD2CIllustration className="w-full h-auto drop-shadow-xs" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 1.5: RECRUITER DEMO ACCESS */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 my-8">
        <RecruiterDemoSection />
      </div>

      {/* SECTION 2: PRODUCT & BUSINESS BENEFITS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="text-xs font-bold text-brand-600 uppercase tracking-wider bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
            Why MarketPath AI
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-charcoal tracking-tight mt-3">
            Built for Makers, Not Operations Technicians
          </h2>
          <p className="text-charcoal-muted mt-2 text-sm sm:text-base leading-relaxed">
            Eliminate repetitive copy-pasting, multi-tab marketplace portals, and fragmented spreadsheets.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
          <Card className="p-7 space-y-4 hover:border-brand-300">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-700 flex items-center justify-center font-bold text-lg">
              01
            </div>
            <h3 className="text-lg font-bold text-charcoal">Define Once, Publish Everywhere</h3>
            <p className="text-xs sm:text-sm text-charcoal-muted leading-relaxed">
              Maintain a single master source of product truth. Specifications, packaging dimensions, outer carton weights, and compliance certificates map automatically to each channel.
            </p>
          </Card>

          <Card className="p-7 space-y-4 hover:border-brand-300">
            <div className="w-12 h-12 rounded-2xl bg-softbeige text-forest flex items-center justify-center font-bold text-lg">
              02
            </div>
            <h3 className="text-lg font-bold text-charcoal">Grounded AI Copy & Validation</h3>
            <p className="text-xs sm:text-sm text-charcoal-muted leading-relaxed">
              Google Gemini 2.5 Flash crafts marketplace titles, 5 bullet points, and SEO metadata strictly grounded in your verified attributes with zero hallucinated specs.
            </p>
          </Card>

          <Card className="p-7 space-y-4 hover:border-brand-300">
            <div className="w-12 h-12 rounded-2xl bg-softorange-50 text-softorange-700 flex items-center justify-center font-bold text-lg">
              03
            </div>
            <h3 className="text-lg font-bold text-charcoal">Human-Approved Publishing</h3>
            <p className="text-xs sm:text-sm text-charcoal-muted leading-relaxed">
              You stay in complete control. Review channel-tailored listings side-by-side, verify compliance, and click approve once before jobs broadcast to external APIs.
            </p>
          </Card>
        </div>
      </section>

      {/* SECTION 3: PRODUCT CATALOGUE */}
      <section id="catalogue" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl border border-bordergrey p-8 sm:p-12 shadow-option-c">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-6 space-y-5">
              <span className="text-xs font-bold text-forest uppercase tracking-wider bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
                Master Catalogue
              </span>
              <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">
                Deep Category Specifications & Freight Packaging
              </h2>
              <p className="text-sm text-charcoal-muted leading-relaxed">
                Every physical product is stored with immutable master purity. We capture inner packaging, outer carton dimensions, automated volumetric weight (`(L×W×H)/5000 kg`), and compliance certifications.
              </p>
              <ul className="space-y-2.5 text-xs text-charcoal font-medium">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-brand-600 shrink-0" />
                  Product (Parent) vs Variant (Sellable Option) vs SKU (Stock Code) hierarchy
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-brand-600 shrink-0" />
                  19 structured Indian D2C categories with FSSAI, CDSCO, and Legal Metrology support
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-brand-600 shrink-0" />
                  Clean separation between immutable master specifications and channel-specific overrides
                </li>
              </ul>
              <div className="pt-2">
                <Link to="/signup">
                  <Button size="sm">
                    Explore Catalogue Intake <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                  </Button>
                </Link>
              </div>
            </div>

            <div className="lg:col-span-6">
              <div className="bg-warmwhite rounded-2xl p-4 border border-bordergrey shadow-xs">
                <CatalogueIllustration className="w-full h-auto" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: MULTI-CHANNEL PUBLISHING */}
      <section id="publishing" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl border border-bordergrey p-8 sm:p-12 shadow-option-c">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-6 order-2 lg:order-1">
              <div className="bg-warmwhite rounded-2xl p-4 border border-bordergrey shadow-xs">
                <OmnichannelHubIllustration className="w-full h-auto" />
              </div>
            </div>

            <div className="lg:col-span-6 order-1 lg:order-2 space-y-5">
              <span className="text-xs font-bold text-brand-600 uppercase tracking-wider bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
                Publishing Engine
              </span>
              <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">
                7-Step Guided Publishing with Cryptographic Integrity
              </h2>
              <p className="text-sm text-charcoal-muted leading-relaxed">
                Prepare, validate, preview, and dispatch product listings to connected storefronts and marketplaces with immutable approval snapshots and automatic duplicate prevention.
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-softbeige/50 border border-bordergrey">
                  <div className="font-bold text-forest">Channel Capabilities</div>
                  <div className="text-charcoal-muted text-[11px] mt-0.5">Strict schema retrieval per platform</div>
                </div>
                <div className="p-3 rounded-xl bg-softbeige/50 border border-bordergrey">
                  <div className="font-bold text-forest">Missing Attribute Guard</div>
                  <div className="text-charcoal-muted text-[11px] mt-0.5">Identifies required fields pre-flight</div>
                </div>
                <div className="p-3 rounded-xl bg-softbeige/50 border border-bordergrey">
                  <div className="font-bold text-forest">Snapshot Hash</div>
                  <div className="text-charcoal-muted text-[11px] mt-0.5">SHA-256 tamper detection</div>
                </div>
                <div className="p-3 rounded-xl bg-softbeige/50 border border-bordergrey">
                  <div className="font-bold text-forest">Partial Success Safety</div>
                  <div className="text-charcoal-muted text-[11px] mt-0.5">Granular channel status & retry</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 5: ORDERS & INVENTORY */}
      <section id="orders" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-softbeige/40 rounded-3xl border border-bordergrey p-8 sm:p-12">
          <div className="max-w-3xl mx-auto text-center space-y-4 mb-10">
            <span className="text-xs font-bold text-forest uppercase tracking-wider bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
              Omnichannel Operations
            </span>
            <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">
              Central Order Ingestion & Stock Guardrails
            </h2>
            <p className="text-sm text-charcoal-muted leading-relaxed">
              When an order arrives on Shopify, Amazon, or retail channels, MarketPath ingests, deduplicates, and decrements stock with safety guards preventing negative inventory.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 bg-white rounded-2xl border border-bordergrey shadow-xs space-y-3">
              <ShoppingBag className="w-8 h-8 text-brand-600" />
              <h3 className="text-base font-bold text-charcoal">Unified Order Ledger</h3>
              <p className="text-xs text-charcoal-muted leading-relaxed">
                View orders across channels in one deduplicated stream with customer city, SKU quantities, and fulfillment tracking.
              </p>
            </div>

            <div className="p-6 bg-white rounded-2xl border border-bordergrey shadow-xs space-y-3">
              <Package className="w-8 h-8 text-forest" />
              <h3 className="text-base font-bold text-charcoal">Negative Stock Protection</h3>
              <p className="text-xs text-charcoal-muted leading-relaxed">
                Zero overselling guarantee. Stock allocation checks prevent decrements beyond available quantities, flagging low-stock alerts.
              </p>
            </div>

            <div className="p-6 bg-white rounded-2xl border border-bordergrey shadow-xs space-y-3">
              <BarChart3 className="w-8 h-8 text-softorange" />
              <h3 className="text-base font-bold text-charcoal">Grounded Order Analytics</h3>
              <p className="text-xs text-charcoal-muted leading-relaxed">
                Revenue, average order value, and top-selling SKUs calculated strictly from authentic ingested orders with zero simulated numbers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 6: AI CONTENT STUDIO */}
      <section id="ai-studio" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl border border-bordergrey p-8 sm:p-12 shadow-option-c">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-7 space-y-5">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softorange-50 border border-softorange-200 text-softorange-700 text-xs font-bold">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI Content Studio — Powered by Gemini 2.5 Flash</span>
              </div>
              <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">
                Tone-Specific Copy Tailored Per Platform
              </h2>
              <p className="text-sm text-charcoal-muted leading-relaxed">
                Generate high-converting Shopify SEO titles, Amazon 5 bullet points, Instagram viral captions, and Meta ad hooks in seconds. The AI studio prepares and optimizes copy; publishing executes through the Publishing Hub.
              </p>
              <div className="space-y-2.5 text-xs text-charcoal-muted">
                <div className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-emerald shrink-0 mt-0.5" />
                  <span><strong>Fact-Checked:</strong> Deterministically references only your approved master specs.</span>
                </div>
                <div className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-emerald shrink-0 mt-0.5" />
                  <span><strong>Tone Selector:</strong> Artisanal, modern minimal, playful energetic, or scientific clinical.</span>
                </div>
                <div className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-emerald shrink-0 mt-0.5" />
                  <span><strong>Human-in-the-Loop:</strong> Copy is editable before publishing. No automated unapproved releases.</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-5 bg-warmwhite rounded-2xl p-6 border border-bordergrey space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-bordergrey text-xs font-bold text-charcoal">
                <span>Sample Generated Output</span>
                <span className="text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full text-[10px]">Shopify Ready</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="font-bold text-charcoal">SEO Title:</div>
                <div className="p-2.5 bg-white rounded-xl border border-bordergrey text-charcoal text-[11px]">
                  Hand-Poured Terracotta Soy Candle (350g) | Pure Lavender & Cedarwood
                </div>
                <div className="font-bold text-charcoal mt-2">Key Highlights:</div>
                <div className="p-2.5 bg-white rounded-xl border border-bordergrey text-charcoal-muted text-[11px] leading-relaxed">
                  • 100% natural soy wax hand-poured in Pune, Maharashtra<br/>
                  • Lead-free cotton wick providing 55+ hours clean burn<br/>
                  • Reusable artisan terracotta container with cork lid
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 7: GROWTH & INSIGHTS (BUSINESS CALENDAR & ROI) */}
      <section id="marketing" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl border border-bordergrey p-8 sm:p-12 shadow-option-c">
          <div className="max-w-3xl mx-auto text-center space-y-3 mb-10">
            <span className="text-xs font-bold text-brand-600 uppercase tracking-wider bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
              Interactive Impact Calculator
            </span>
            <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">
              Calculate Your Operational Time & Cost Savings
            </h2>
            <p className="text-sm text-charcoal-muted leading-relaxed">
              Estimate monthly hours reclaimed from repetitive catalog formatting and administrative publishing overhead.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
            {/* Controls */}
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-xs font-bold text-charcoal mb-2">
                  <span>Active Products & SKUs: {activeSkus}</span>
                  <span className="text-brand-600">{activeSkus} SKUs</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="250"
                  step="5"
                  value={activeSkus}
                  onChange={(e) => setActiveSkus(Number(e.target.value))}
                  className="w-full accent-brand-600 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-bold text-charcoal mb-2">
                  <span>Connected Sales Channels: {currentChannels}</span>
                  <span className="text-brand-600">{currentChannels} Channels</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="6"
                  step="1"
                  value={currentChannels}
                  onChange={(e) => setCurrentChannels(Number(e.target.value))}
                  className="w-full accent-brand-600 cursor-pointer"
                />
              </div>

              <div className="text-xs text-charcoal-muted leading-relaxed p-4 rounded-2xl bg-softbeige/50 border border-bordergrey">
                Includes automated title formatting, bullet points, attribute mapping, inventory tracking, and RFC 5545 calendar export.
              </div>
            </div>

            {/* Results Display */}
            <div className="p-8 rounded-3xl bg-brand-50 border border-brand-200 text-center space-y-4">
              <span className="text-xs font-bold text-forest uppercase tracking-wider block">Estimated Monthly Impact</span>
              <div className="text-4xl sm:text-5xl font-extrabold text-charcoal">
                {hoursSavedPerMonth} <span className="text-2xl font-bold text-brand-600">Hours Saved</span>
              </div>
              <div className="text-sm text-charcoal-muted font-medium">
                Equivalent to approx <span className="font-bold text-forest">₹{estimatedAgencyCostSavings.toLocaleString('en-IN')} / month</span> in administrative and copy formatting overhead.
              </div>
              <Link to="/free-consultation" className="inline-block pt-2">
                <Button size="sm">
                  Schedule Free Audit <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 8: AGENCY CONNECT */}
      <section id="agency-connect" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl border border-bordergrey p-8 sm:p-12 shadow-option-c">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-7 space-y-4">
              <span className="text-xs font-bold text-forest uppercase tracking-wider bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
                Agency Connect Directory
              </span>
              <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">
                Vetted Human Creative & Performance Expertise
              </h2>
              <p className="text-sm text-charcoal-muted leading-relaxed">
                When your brand scales beyond software automation, discover vetted agencies specializing in product photography, performance ad scaling, and catalog management across 10 core D2C categories.
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-warmwhite rounded-xl border border-bordergrey">
                  <div className="font-bold text-charcoal">8 Verified Demo Agencies</div>
                  <div className="text-[11px] text-charcoal-muted">Pune, Mumbai, Bangalore & Pan-India</div>
                </div>
                <div className="p-3 bg-warmwhite rounded-xl border border-bordergrey">
                  <div className="font-bold text-charcoal">PII Privacy Vault</div>
                  <div className="text-[11px] text-charcoal-muted">Founder personal phone & email scrubbed</div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-5 bg-softbeige/50 rounded-2xl p-6 border border-bordergrey space-y-3 text-xs">
              <div className="font-bold text-forest">Core Agency Services Available:</div>
              <ul className="space-y-1.5 text-charcoal-muted">
                <li>• Artisanal Product Photography & Video</li>
                <li>• D2C Brand Storytelling & Packaging Design</li>
                <li>• Performance Marketing & Meta ROAS Scaling</li>
                <li>• Amazon India A+ Catalog & SEO Optimization</li>
                <li>• Quick Commerce Dark Store Placement (Zepto / Blinkit)</li>
              </ul>
              <div className="pt-2">
                <Link to="/signup" className="text-brand-600 font-bold hover:underline inline-flex items-center gap-1">
                  Browse Agency Directory <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 9: HOW MARKETPATH WORKS */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="text-xs font-bold text-brand-600 uppercase tracking-wider bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
            Operating Loop
          </span>
          <h2 className="text-3xl font-extrabold text-charcoal tracking-tight mt-3">
            The 10-Step Growth Workflow
          </h2>
          <p className="text-charcoal-muted mt-2 text-sm">
            From initial voice onboarding to multi-channel inventory synchronization.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 sm:gap-4 text-center">
          {[
            { step: '01', title: 'Describe Business', desc: 'Voice or text brand profile' },
            { step: '02', title: 'Understand Brand', desc: '15 structured dimensions' },
            { step: '03', title: 'Structure Products', desc: 'Master catalogue purity' },
            { step: '04', title: 'Connect Channels', desc: '4-group ecosystem' },
            { step: '05', title: 'Prepare Listings', desc: 'Grounded AI studio copy' },
            { step: '06', title: 'Validate Specs', desc: 'Attribute & compliance check' },
            { step: '07', title: 'Approve Batch', desc: 'Mandatory human approval' },
            { step: '08', title: 'Publish APIs', desc: 'Idempotent dispatch' },
            { step: '09', title: 'Sync Orders', desc: 'Deduplicated stock ledger' },
            { step: '10', title: 'Manage Growth', desc: 'Verified analytics & calendar' },
          ].map((item) => (
            <div key={item.step} className="p-4 bg-white rounded-2xl border border-bordergrey shadow-xs space-y-1.5">
              <span className="text-xs font-bold text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full">{item.step}</span>
              <div className="text-xs font-bold text-charcoal">{item.title}</div>
              <div className="text-[10px] text-charcoal-muted leading-tight">{item.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 10: CHANNEL ECOSYSTEM */}
      <section id="channels" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="text-xs font-bold text-forest uppercase tracking-wider bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
            Ecosystem Directory
          </span>
          <h2 className="text-3xl font-extrabold text-charcoal tracking-tight mt-3">
            4-Group Channel Ecosystem
          </h2>
          <p className="text-charcoal-muted mt-2 text-sm">
            Strict, honest status disclosures. We never claim a connection is live when it requires enterprise partner access.
          </p>
        </div>

        {/* Channel Group Tabs */}
        <div className="flex justify-center mb-8">
          <div className="p-1 rounded-2xl bg-softbeige border border-bordergrey flex flex-wrap gap-1 text-xs font-semibold">
            {[
              { id: 'storefronts', label: 'Storefronts (Shopify, Woo)' },
              { id: 'marketplaces', label: 'Marketplaces (Amazon, Flipkart)' },
              { id: 'social', label: 'Social & Ads (Meta, Instagram)' },
              { id: 'quick_commerce', label: 'Quick Commerce (Zepto, Blinkit)' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveChannelGroup(tab.id as any)}
                className={`px-4 py-2 rounded-xl transition-all cursor-pointer ${
                  activeChannelGroup === tab.id
                    ? 'bg-white text-forest font-bold shadow-xs'
                    : 'text-charcoal-muted hover:text-charcoal'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Channel Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {channelDirectory[activeChannelGroup].map((channel) => (
            <Card key={channel.name} className="p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-charcoal">{channel.name}</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-softbeige text-forest border border-bordergrey">
                  {channel.badge}
                </span>
              </div>
              <div className="text-xs text-charcoal-muted leading-relaxed">{channel.desc}</div>
              <div className="pt-2 border-t border-bordergrey text-[11px] font-semibold text-brand-700">
                Status: {channel.status}
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* SECTION 11: TRUST & SECURITY */}
      <section id="trust-security" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-forest bg-[#075443] text-white rounded-3xl p-8 sm:p-12 shadow-option-c-lg border border-[#0A6B53]">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <ShieldCheck className="w-12 h-12 text-emerald mx-auto" />
            <h2 className="text-3xl font-extrabold tracking-tight text-white">
              Trust & Architectural Security Guarantees
            </h2>
            <p className="text-[#E0EFE9] text-sm leading-relaxed">
              We uphold genuine software integrity. We never ask for or store your marketplace passwords or direct ad budgets. All external connections use scoped official OAuth and API tokens, tenant isolation is strictly enforced at the database level, and AI never publishes or spends without mandatory human approval.
            </p>
            <div className="pt-4 flex flex-wrap justify-center gap-6 text-xs text-[#C1E0D4] font-semibold">
              <span>• Mandatory Human Approval Gate</span>
              <span>• Scoped API & OAuth Credentials</span>
              <span>• Organization-Level Data Isolation</span>
              <span>• Grounded Spec Accuracy (Zero Hallucination)</span>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 12: COMPREHENSIVE FAQ */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <span className="text-xs font-bold text-brand-600 uppercase tracking-wider bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
            Frequently Asked Questions
          </span>
          <h2 className="text-3xl font-extrabold text-charcoal tracking-tight mt-3">
            Everything You Need to Know
          </h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => (
            <div key={idx} className="border border-bordergrey rounded-2xl bg-white overflow-hidden shadow-xs">
              <button
                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                className="w-full p-5 text-left flex items-center justify-between text-sm sm:text-base font-bold text-charcoal hover:text-forest transition-colors cursor-pointer"
              >
                <span>{faq.q}</span>
                <ChevronDown className={`w-5 h-5 text-charcoal-muted shrink-0 transition-transform duration-200 ${activeFaq === idx ? 'rotate-180 text-brand-600' : ''}`} />
              </button>
              {activeFaq === idx && (
                <div className="px-5 pb-5 text-xs sm:text-sm text-charcoal-muted leading-relaxed border-t border-bordergrey pt-3 animate-in fade-in duration-150">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 13: FINAL HIGH-CONTRAST CONVERSION CALL-TO-ACTION (CRITICAL FIX) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-forest-deep bg-[#053F32] rounded-3xl p-10 sm:p-16 text-center text-white shadow-option-c-lg relative overflow-hidden border border-[#075443]">
          {/* Subtle Decorative Elements (High Contrast) */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-brand-600/20 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald/15 rounded-full blur-3xl pointer-events-none" />

          <div className="max-w-3xl mx-auto space-y-6 relative z-10">
            <span className="inline-block px-3.5 py-1.5 rounded-full bg-[#075443] text-emerald text-xs font-bold uppercase tracking-wider border border-[#15966F]/30">
              Start Your Omnichannel Operations
            </span>

            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
              Ready to run your product business across channels, effortlessly?
            </h2>

            <p className="text-[#E0EFE9] text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
              Join emerging Indian D2C brands unifying their catalogue, AI copy, and multi-channel publishing in one seamless control centre.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup" className="w-full sm:w-auto">
                <Button size="lg" className="w-full sm:w-auto bg-brand-600 hover:bg-[#075443] text-white px-8 py-3.5 text-base font-bold shadow-md border border-[#15966F]/40">
                  Start Free Workspace <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
              <Link to="/free-consultation" className="w-full sm:w-auto">
                <Button variant="secondary" size="lg" className="w-full sm:w-auto bg-softbeige hover:bg-softbeige-dark text-charcoal px-8 py-3.5 text-base font-bold shadow-md border border-bordergrey">
                  <Sparkles className="w-4 h-4 mr-2 text-softorange" /> Book Free Consultation
                </Button>
              </Link>
            </div>

            <p className="text-xs text-[#A0C4B8] font-medium pt-2">
              Instant setup • No credit card required • Dedicated Indian D2C support
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
