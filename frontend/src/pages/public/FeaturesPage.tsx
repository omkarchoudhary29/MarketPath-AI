import React from 'react';
import { Link } from 'react-router-dom';
import {
  Package,
  Wand2,
  Send,
  Megaphone,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

export const FeaturesPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-24">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-600">Complete Platform Suite</span>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-charcoal tracking-tight mt-2">
          Engineered for D2C Brand Simplicity
        </h1>
        <p className="mt-4 text-base sm:text-lg text-slate-600">
          Explore the five modular engines powering MarketPath AI. Each module solves a critical bottleneck in the seller growth journey.
        </p>
      </div>

      {/* Module 1: Master Catalogue */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-50 text-sky-700 text-xs font-bold border border-sky-200">
            <Package className="w-4 h-4" /> Module 1: Master Catalogue
          </div>
          <h2 className="text-3xl font-extrabold text-charcoal">
            The Immutable Source of Truth for Your Products
          </h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            Stop updating multiple spreadsheets. Define your product specifications once: SKU hierarchy, dimensions, weight, confirmed material claims, base pricing, and private cost thresholds.
          </p>
          <ul className="space-y-3 text-sm text-slate-700">
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Separation of Master vs. Channel Overrides:</strong> External channel rejections will never corrupt your master product records.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Cloudinary Media Pipeline:</strong> Direct signed browser uploads with responsive transformations (square crops for Shopify, 4:5 vertical crops for Instagram).</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Multi-Attribute Variants:</strong> Color, size, scent, and pack-size configurations with independent SKU inventory tracking.</span>
            </li>
          </ul>
        </div>
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-md">
          <div className="text-xs font-mono text-slate-400 mb-3">Master Product Record • CER-MUG-001</div>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex justify-between">
              <span className="text-xs text-slate-600 font-medium">Title:</span>
              <span className="text-xs text-charcoal font-bold">Speckled Stoneware Artisan Mug (350ml)</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex justify-between">
              <span className="text-xs text-slate-600 font-medium">Materials:</span>
              <span className="text-xs text-charcoal font-semibold">Stoneware Clay, Food-safe Matte Glaze</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex justify-between">
              <span className="text-xs text-slate-600 font-medium">Pricing:</span>
              <span className="text-xs text-charcoal font-semibold">₹899 Base • ₹1,199 Compare-at</span>
            </div>
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100 flex justify-between items-center text-emerald-800 text-xs font-medium">
              <span>Channel Customization:</span>
              <span className="font-bold">Shopify & Instagram Overrides Configured</span>
            </div>
          </div>
        </div>
      </section>

      {/* Module 2: AI Content Studio */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="order-2 lg:order-1 p-6 rounded-2xl bg-white border border-slate-200 shadow-md space-y-4">
          <div className="text-xs font-mono text-slate-400">AI Studio • Google Gemini Provider</div>
          <div className="p-4 rounded-xl bg-amberbrand-50/60 border border-amberbrand-200 text-xs">
            <span className="font-bold text-amberbrand-900 block mb-1">Tone: Warm & Aesthetic Storytelling</span>
            <p className="text-slate-700 italic">
              "Quiet mornings hit differently with a warm cup held in both hands. ✨ Hand-thrown in Pune, double-fired for durability. Link in bio to shop the Speckled Artisan Mug."
            </p>
            <div className="mt-3 flex flex-wrap gap-1.5 text-[10px] text-amberbrand-800 font-mono">
              <span>#ArtisanPottery</span> <span>#HandmadeCeramics</span> <span>#SlowLivingIndia</span>
            </div>
          </div>
          <div className="flex items-center justify-between pt-2 text-xs">
            <span className="text-emerald-700 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" /> 100% Grounded in Product Specs
            </span>
            <span className="text-slate-500 font-medium">Approved by Seller</span>
          </div>
        </div>

        <div className="order-1 lg:order-2 space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amberbrand-50 text-amberbrand-700 text-xs font-bold border border-amberbrand-200">
            <Wand2 className="w-4 h-4" /> Module 2: AI Content Studio
          </div>
          <h2 className="text-3xl font-extrabold text-charcoal">
            Channel-Tailored Copy Without Hallucinations
          </h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            MarketPath leverages Google Gemini through a secure server-side adapter. Our prompt engineering injects your verified master product attributes into strict XML boundaries, completely forbidding invented certifications, fake ingredients, or unrealistic promises.
          </p>
          <ul className="space-y-3 text-sm text-slate-700">
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Brand Voice Presets:</strong> Adapt copy to your brand personality (Warm & Aesthetic, Minimalist, Bold & Vibrant, Artisanal Heritage).</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Version Comparison:</strong> Generate 3 creative angles, edit inline, and select the winning version for channel publishing.</span>
            </li>
          </ul>
        </div>
      </section>

      {/* Module 3: Omnichannel Publishing */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 text-teal-700 text-xs font-bold border border-teal-200">
            <Send className="w-4 h-4" /> Module 3: Omnichannel Publishing
          </div>
          <h2 className="text-3xl font-extrabold text-charcoal">
            Authorized, Idempotent 1-Click Publishing
          </h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            Publishing doesn't mean typing passwords. MarketPath connects directly to Shopify Admin GraphQL and Meta Graph API. Our background queue handles network timeouts and rate limits with exponential backoff.
          </p>
          <ul className="space-y-3 text-sm text-slate-700">
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Idempotency Keys:</strong> Prevents accidental duplicate product creation if a network request drops.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Error Triage Drawer:</strong> If Shopify rejects an unmapped tax code, MarketPath highlights the exact field with guidance.</span>
            </li>
          </ul>
        </div>
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-md">
          <div className="text-xs font-mono text-slate-400 mb-3">Live Publishing Queue</div>
          <div className="space-y-2.5">
            <div className="p-3 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-charcoal block">Speckled Ceramic Mug</span>
                <span className="text-[10px] text-slate-500">Shopify Admin GraphQL</span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px]">
                ● Published
              </span>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-charcoal block">Botanical Soy Candle</span>
                <span className="text-[10px] text-slate-500">Instagram Graph API</span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px]">
                ● Live
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Module 4: Marketing Studio */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="order-2 lg:order-1 p-6 rounded-2xl bg-white border border-slate-200 shadow-md space-y-4">
          <div className="text-xs font-mono text-slate-400">Campaign Brief • ATL-CAMP-001</div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2 text-xs">
            <div className="flex justify-between font-semibold">
              <span className="text-slate-600">Total Budget:</span>
              <span className="text-charcoal">₹15,000 (Capped at ₹1,500/day)</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span className="text-slate-600">Targeting:</span>
              <span className="text-charcoal">Urban Home Enthusiasts (Pune & Mumbai)</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span className="text-slate-600">Approval State:</span>
              <span className="text-emerald-700">Owner Sign-off Confirmed</span>
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-sky-50 text-sky-800 text-[11px] font-medium border border-sky-100">
            Ad spend flows directly to Meta Ads. MarketPath never handles seller ad funds.
          </div>
        </div>

        <div className="order-1 lg:order-2 space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold border border-indigo-200">
            <Megaphone className="w-4 h-4" /> Module 4: Marketing & Ad Studio
          </div>
          <h2 className="text-3xl font-extrabold text-charcoal">
            Guided Campaign Strategy with Stop-Loss Controls
          </h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            Eliminate wasted ad spend. MarketPath drafts comprehensive campaign briefs, recommends realistic audience angles, formats approved product creatives, and enforces strict owner sign-offs before any ad dollar is committed.
          </p>
          <ul className="space-y-3 text-sm text-slate-700">
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Manual Ad Pack Export:</strong> While API approvals are pending, export copy, dimensions, and targeting checklists for fast manual setup.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Explicit Budget Sign-off:</strong> The system strictly prevents campaigns from launching without direct founder confirmation.</span>
            </li>
          </ul>
        </div>
      </section>

      {/* Module 5: Unified Analytics */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 text-purple-700 text-xs font-bold border border-purple-200">
            <BarChart3 className="w-4 h-4" /> Module 5: Unified Analytics
          </div>
          <h2 className="text-3xl font-extrabold text-charcoal">
            Honest Performance Reporting Grounded in Reality
          </h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            No fabricated numbers or mysterious attribution models. MarketPath displays real orders from your connected Shopify store and verified engagement metrics from Instagram, each with explicit sync timestamps.
          </p>
          <ul className="space-y-3 text-sm text-slate-700">
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Data Source Transparency:</strong> Every card clearly states whether it originates from Shopify, Meta Graph, or Demo Fixtures.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span><strong>Deterministic AI Analytics Assistant:</strong> Ask natural language questions; calculations are executed via exact SQL queries before LLM summarization.</span>
            </li>
          </ul>
        </div>
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-md">
          <div className="text-xs font-mono text-slate-400 mb-3">Live Reporting Telemetry</div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] text-slate-500 font-medium block">Shopify Gross Sales</span>
              <span className="text-lg font-bold text-charcoal block mt-0.5">₹1,48,200</span>
              <span className="text-[9px] text-slate-400">Last sync: 10m ago</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] text-slate-500 font-medium block">Instagram Reach</span>
              <span className="text-lg font-bold text-charcoal block mt-0.5">48,200 views</span>
              <span className="text-[9px] text-slate-400">Organic impressions</span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <div className="text-center pt-8 border-t border-slate-200">
        <Link
          to="/signup"
          className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm shadow-md transition-all"
        >
          Explore All Features in the Workspace
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};

