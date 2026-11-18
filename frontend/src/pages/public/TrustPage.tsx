import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Lock, Eye, KeyRound, Sparkles, Database, ArrowRight } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';

export const TrustPage: React.FC = () => {
  const commitments = [
    {
      title: 'Zero Password Custody',
      desc: 'We never ask for or store your Shopify, Amazon, or Meta account passwords. All integrations use official OAuth 2.0 flows with least-privilege permission scopes.',
      icon: KeyRound,
      tag: 'Credential Safety',
    },
    {
      title: 'Media Spend Sovereignty',
      desc: 'MarketPath AI never takes custody of your advertising budget. All advertising bills are paid directly by you to Meta or Google Ads in your own authorized account.',
      icon: Lock,
      tag: 'Financial Independence',
    },
    {
      title: 'Mandatory Human Sign-off',
      desc: 'We strictly forbid autonomous changes. No product listing goes live on Shopify or Amazon, no Instagram post broadcasts, and no ad campaign launches without your explicit review and approval.',
      icon: Eye,
      tag: 'Human Control',
    },
    {
      title: 'Deterministic AI Anti-Hallucination',
      desc: 'Our Gemini integration injects verified product specs into isolated prompt boundaries. The model is forbidden from inventing certifications, ingredients, or fake guarantees.',
      icon: Sparkles,
      tag: 'Verified Facts',
    },
    {
      title: 'Two-Tier Multi-Tenant Isolation',
      desc: 'Your catalogue, campaigns, and financial metrics are protected by tenant-scoping middleware at the API layer and Row-Level Security (RLS) at the PostgreSQL database layer.',
      icon: Database,
      tag: 'Tenant Security',
    },
    {
      title: 'Grounded Analytics Truth',
      desc: 'We do not generate speculative ROAS or fabricated conversion metrics. Every number shown originates directly from connected platform APIs with exact sync timestamps.',
      icon: ShieldCheck,
      tag: 'Data Integrity',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-14 space-y-16">
      <div className="text-center space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-emerald bg-emerald-50 px-3.5 py-1.5 rounded-full border border-emerald-200">
          Security Manifesto & Trust Architecture
        </span>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-charcoal tracking-tight">
          Trust & Technical Integrity at Every Step
        </h1>
        <p className="text-base sm:text-lg text-charcoal-muted max-w-2xl mx-auto leading-relaxed">
          We treat your brand's data, store access, and customer privacy with the highest degree of cryptographic care and engineering discipline.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {commitments.map((c, i) => {
          const Icon = c.icon;
          return (
            <Card key={i} className="p-7 space-y-3 hover:border-brand-300">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-softbeige text-forest flex items-center justify-center">
                  <Icon className="w-5 h-5 text-brand-600" />
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-brand-50 text-brand-700 border border-brand-200">
                  {c.tag}
                </span>
              </div>
              <h3 className="text-lg font-bold text-charcoal">{c.title}</h3>
              <p className="text-xs sm:text-sm text-charcoal-muted leading-relaxed">{c.desc}</p>
            </Card>
          );
        })}
      </div>

      {/* CTA Footer */}
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
