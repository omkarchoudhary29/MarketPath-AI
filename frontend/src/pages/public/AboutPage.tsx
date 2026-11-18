import React, { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Target, Sparkles, MapPin, ShieldCheck, Lock, CheckCircle2, ArrowRight, Layers, FileCheck, Users2, Package, Wand2, Send, ShoppingBag, BarChart3, Play } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { siteConfig } from '../../config/site';

export const AboutPage: React.FC = () => {
  const location = useLocation();

  useEffect(() => {
    if (location.hash) {
      const el = document.getElementById(location.hash.replace('#', ''));
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      window.scrollTo(0, 0);
    }
  }, [location]);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-14 space-y-16">
      {/* 1. Header */}
      <div id="about" className="text-center space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-forest bg-softbeige px-3.5 py-1.5 rounded-full border border-bordergrey">
          About MarketPath AI
        </span>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-charcoal tracking-tight">
          Empowering India’s Emerging Product Creators
        </h1>
        <p className="text-base sm:text-lg text-charcoal-muted max-w-2xl mx-auto leading-relaxed">
          We believe the future of Indian D2C commerce belongs to authentic product makers—not repetitive spreadsheets, multiple marketplace tabs, and operational confusion.
        </p>
      </div>

      {/* 2. Origin & Philosophy Card */}
      <Card className="p-8 sm:p-12 space-y-6 text-charcoal-muted leading-relaxed text-sm sm:text-base border-bordergrey shadow-option-c">
        <div className="flex items-center gap-2 text-xs font-bold text-forest bg-brand-50 px-3 py-1 rounded-full w-fit border border-brand-200">
          <MapPin className="w-3.5 h-3.5 text-brand-600" /> Founded in Maharashtra (Pune & Mumbai)
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight">
          The Problem We Are Solving
        </h2>
        <p>
          Across Pune, Mumbai, Kolhapur, Delhi NCR, Bangalore, and across India, gifted makers are formulating botanical skincare, hand-pouring scented candles, crafting sustainable homeware, and designing contemporary apparel. Yet, the moment they begin digital selling, they run into an exhausting operational maze.
        </p>
        <p>
          Today, a seller has to manually type the same product details across Shopify, Amazon, and Flipkart; rewrite different titles and descriptions; upload images repeatedly; format different attribute sheets; manage inventory separately; and decipher fragmented analytics dashboards.
        </p>
        <div className="p-5 bg-softbeige/50 rounded-2xl border border-bordergrey text-charcoal font-semibold text-sm">
          <strong>MarketPath AI's Mission:</strong> "Tell MarketPath about your brand and products once. Connect your selling channels. Approve your listings once. Manage your selling operations from one workspace."
        </div>
      </Card>

      {/* 3. Who We Serve */}
      <div className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
            Target Audience
          </span>
          <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">Who MarketPath Serves</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center font-bold text-sm">
              01
            </div>
            <h3 className="text-base font-bold text-charcoal">Independent Product Makers</h3>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              Artisans, craftspeople, and manufacturers who want to focus on creating great physical products without becoming technical catalog operators.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-softbeige text-forest flex items-center justify-center font-bold text-sm">
              02
            </div>
            <h3 className="text-base font-bold text-charcoal">Emerging D2C Brands</h3>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              Growing direct-to-consumer businesses expanding from their primary storefront to Amazon, Flipkart, quick-commerce, and social sales channels.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-softorange-50 text-softorange-700 flex items-center justify-center font-bold text-sm">
              03
            </div>
            <h3 className="text-base font-bold text-charcoal">Vetted Agency Partners</h3>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              Marketing and creative agencies seeking qualified client proposals with sanitized founder privacy and structured deliverables in the Agency Partner Portal.
            </p>
          </Card>
        </div>
      </div>

      {/* 4. The 10-Step Connected Workflow */}
      <div id="how-it-works" className="pt-8 border-t border-bordergrey space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-forest bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
            How It Works
          </span>
          <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">The 10-Step Connected Workflow</h2>
          <p className="text-xs sm:text-sm text-charcoal-muted">
            The full operating journey from voice onboarding to live inventory synchronization.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
          {[
            { step: '01', title: 'Describe Business', icon: Sparkles },
            { step: '02', title: 'Understand Brand', icon: Target },
            { step: '03', title: 'Structure Products', icon: Package },
            { step: '04', title: 'Connect Channels', icon: Layers },
            { step: '05', title: 'Prepare Listings', icon: Wand2 },
            { step: '06', title: 'Validate Specs', icon: FileCheck },
            { step: '07', title: 'Approve Batch', icon: CheckCircle2 },
            { step: '08', title: 'Publish APIs', icon: Send },
            { step: '09', title: 'Sync Orders', icon: ShoppingBag },
            { step: '10', title: 'Manage Growth', icon: BarChart3 },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.step} className="p-4 bg-white rounded-2xl border border-bordergrey shadow-xs space-y-2">
                <div className="w-7 h-7 mx-auto rounded-lg bg-softbeige text-forest flex items-center justify-center">
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="text-xs font-bold text-charcoal">{item.title}</div>
                <div className="text-[10px] text-charcoal-muted font-mono font-semibold">Step {item.step}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 5. Trust & Security Architecture */}
      <div id="trust-security" className="pt-8 border-t border-bordergrey space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
            Trust & Security
          </span>
          <h2 className="text-3xl font-extrabold text-charcoal tracking-tight">Verified Technical Security Controls</h2>
          <p className="text-xs sm:text-sm text-charcoal-muted">
            We only claim security controls supported directly by our architecture and test suites.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <Card className="p-6 space-y-3">
            <div className="flex items-center gap-2 text-forest font-bold text-sm">
              <ShieldCheck className="w-5 h-5 text-emerald" />
              AES-256-GCM Token Encryption
            </div>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              Third-party OAuth credentials (Shopify tokens, Meta tokens) are encrypted at rest using Galois/Counter Mode with 256-bit master keys. Cleartext tokens never leak to the browser.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="flex items-center gap-2 text-forest font-bold text-sm">
              <Lock className="w-5 h-5 text-brand-600" />
              Tenant Context Isolation (RLS)
            </div>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              Every database entity is locked behind non-nullable organization boundaries. Queries are strictly scoped via `TenantContext` to prevent cross-tenant data access.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="flex items-center gap-2 text-forest font-bold text-sm">
              <FileCheck className="w-5 h-5 text-softorange" />
              Strict Zero-Faking Policy
            </div>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              We never simulate third-party connections, generate fake listing URLs, invent ad spend, or fabricate sales metrics. When partner credentials are unconfigured, we honestly report it.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="flex items-center gap-2 text-forest font-bold text-sm">
              <Users2 className="w-5 h-5 text-purple-600" />
              Founder Privacy in Agency Connect
            </div>
            <p className="text-xs text-charcoal-muted leading-relaxed">
              Founder personal phone numbers, personal emails, cost prices, and margins are sanitized from project briefs before agencies view them, preventing unsolicited contact.
            </p>
          </Card>
        </div>
      </div>

      {/* CTA Footer */}
      <div className="text-center pt-8 border-t border-bordergrey flex flex-wrap items-center justify-center gap-3.5">
        <Link to="/signup">
          <Button size="lg" className="px-7 shadow-sm">
            Start Free Workspace <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
        <Link to="/login?type=company">
          <Button variant="secondary" size="lg" className="px-6 bg-softorange/10 hover:bg-softorange/20 border-softorange/40 text-charcoal">
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
        <Link to="/free-consultation">
          <Button variant="secondary" size="lg" className="px-6">
            <Sparkles className="w-4 h-4 mr-2 text-softorange" /> Free Consultation
          </Button>
        </Link>
      </div>
    </div>
  );
};
