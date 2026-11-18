import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  Package,
  Wand2,
  Sliders,
  Send,
  BarChart3,
  CheckCircle2,
  Layers,
  FileCheck,
  ShoppingBag,
  ShieldCheck,
  Check,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';

export const HowItWorksPage: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Describe Business',
      desc: 'Tell MarketPath about your brand origin, aesthetic, target customer, and values using voice recording or guided form inputs.',
      type: 'Seller Input',
      badge: 'Voice or Form',
      icon: Sparkles,
    },
    {
      num: '02',
      title: 'Understand Brand',
      desc: 'Our Gemini-powered intelligence structures your brand into 15 dimensions (voice guidelines, archetypes, color palette, compliance badges).',
      type: 'AI Structuring',
      badge: 'Brand Profile',
      icon: Wand2,
    },
    {
      num: '03',
      title: 'Structure Products',
      desc: 'Create master product records with immutable specifications: materials, variant matrix, packaging dimensions, outer carton, and certifications.',
      type: 'Master Truth',
      badge: 'Master Catalogue',
      icon: Package,
    },
    {
      num: '04',
      title: 'Connect Channels',
      desc: 'Authorize external sales channels across Storefronts (Shopify, WooCommerce), Marketplaces (Amazon, Flipkart), Social, and Quick Commerce.',
      type: 'Channel Integrations',
      badge: 'OAuth Connectors',
      icon: Layers,
    },
    {
      num: '05',
      title: 'Prepare Listings',
      desc: 'AI Content Studio generates channel-tailored copy: Shopify SEO tags, Amazon 5 bullet points, and Instagram storytelling strictly grounded in your master specs.',
      type: 'AI Content Studio',
      badge: 'Fact-Grounded',
      icon: Wand2,
    },
    {
      num: '06',
      title: 'Validate Specs',
      desc: 'Automated pre-flight checks inspect category requirements, character limits, required attributes, and packaging certifications before dispatch.',
      type: 'Compliance Validation',
      badge: 'Zero-Error Check',
      icon: FileCheck,
    },
    {
      num: '07',
      title: 'Approve Batch',
      desc: 'Mandatory human approval gate. Brand owners review side-by-side previews and click Approve. A cryptographic hash snapshot prevents tampering.',
      type: 'Human-in-the-Loop',
      badge: 'Seller Approval',
      icon: CheckCircle2,
    },
    {
      num: '08',
      title: 'Publish APIs',
      desc: 'MarketPath dispatches listings via official APIs (Shopify Admin GraphQL, Amazon SP-API, Meta Graph) with idempotent background workers.',
      type: 'Official Publishing',
      badge: 'API Broadcaster',
      icon: Send,
    },
    {
      num: '09',
      title: 'Synchronise Orders',
      desc: 'Ingests and deduplicates sales orders from all connected channels in real time, decrementing stock with negative inventory guardrails.',
      type: 'Operations Sync',
      badge: 'Live Stock Guard',
      icon: ShoppingBag,
    },
    {
      num: '10',
      title: 'Manage Growth',
      desc: 'Track authentic multi-channel revenue, schedule festive campaigns in the Business Calendar, and engage vetted partners via Agency Connect.',
      type: 'Business Growth',
      badge: 'Analytics & Calendar',
      icon: BarChart3,
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-14 space-y-16">
      {/* Header */}
      <div className="text-center space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-forest bg-softbeige px-3.5 py-1.5 rounded-full border border-bordergrey">
          Operating Lifecycle
        </span>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-charcoal tracking-tight">
          How MarketPath AI Works
        </h1>
        <p className="text-base sm:text-lg text-charcoal-muted max-w-2xl mx-auto leading-relaxed">
          The 10-step connected loop engineered for emerging Indian D2C brands. Clear boundaries between AI assistance, seller approval, and external execution.
        </p>
      </div>

      {/* Clear Distinction Banner */}
      <div className="p-6 rounded-2xl bg-white border border-bordergrey shadow-option-c grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center shrink-0 font-bold">AI</div>
          <div>
            <div className="font-bold text-charcoal text-sm">1. AI Prepares & Tailors</div>
            <p className="text-charcoal-muted mt-1 leading-relaxed">Transcribes voice, structures attributes, and generates channel copy grounded in your verified facts.</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-xl bg-softorange-50 text-softorange-700 flex items-center justify-center shrink-0 font-bold">YOU</div>
          <div>
            <div className="font-bold text-charcoal text-sm">2. Seller Approves</div>
            <p className="text-charcoal-muted mt-1 leading-relaxed">Mandatory human control. Nothing is broadcast to external platforms without explicit seller sign-off.</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-xl bg-forest text-white flex items-center justify-center shrink-0 font-bold">API</div>
          <div>
            <div className="font-bold text-charcoal text-sm">3. Platform Executes</div>
            <p className="text-charcoal-muted mt-1 leading-relaxed">Official API connectors publish listings, sync incoming orders, and protect against negative stock.</p>
          </div>
        </div>
      </div>

      {/* 10-Step Interactive Process Visualization */}
      <div className="space-y-4">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <Card key={step.num} className="p-5 sm:p-6 hover:border-brand-300">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-softbeige text-forest flex items-center justify-center font-extrabold text-base shrink-0 border border-bordergrey">
                    {step.num}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-brand-50 text-brand-700 border border-brand-200">
                        {step.type}
                      </span>
                      <span className="text-xs text-charcoal-muted font-medium">
                        {step.badge}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-charcoal">{step.title}</h3>
                    <p className="text-xs sm:text-sm text-charcoal-muted leading-relaxed max-w-2xl">
                      {step.desc}
                    </p>
                  </div>
                </div>
                <div className="shrink-0 self-end sm:self-center">
                  <div className="w-9 h-9 rounded-xl bg-warmwhite border border-bordergrey flex items-center justify-center text-forest">
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Bottom CTA */}
      <div className="text-center pt-8 border-t border-bordergrey flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link to="/signup">
          <Button size="lg" className="px-8 shadow-sm">
            Start Free Workspace <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
        <Link to="/free-consultation">
          <Button variant="secondary" size="lg" className="px-8">
            <Sparkles className="w-4 h-4 mr-2 text-softorange" /> Book Free Growth Consultation
          </Button>
        </Link>
      </div>
    </div>
  );
};
