import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { plansMock, managedServicesMock } from '../../data/mockData';

export const PricingPage: React.FC = () => {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  const discount = billingCycle === 'annual' ? 0.8 : 1.0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-24">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-600">Predictable Growth Pricing</span>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-charcoal tracking-tight">
          Transparent Plans for Emerging D2C Brands
        </h1>
        <p className="text-base sm:text-lg text-slate-600">
          Subscribe for software control, add managed services when you need execution horsepower, and pay ad networks directly.
        </p>

        {/* Billing Switcher */}
        <div className="pt-4 flex items-center justify-center gap-3">
          <span className={`text-xs font-semibold ${billingCycle === 'monthly' ? 'text-charcoal' : 'text-slate-500'}`}>
            Monthly Billing
          </span>
          <button
            onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
            className="w-12 h-6 rounded-full bg-brand-600 p-0.5 transition-colors relative cursor-pointer"
          >
            <div
              className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                billingCycle === 'annual' ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
          <span className={`text-xs font-semibold flex items-center gap-1.5 ${billingCycle === 'annual' ? 'text-charcoal' : 'text-slate-500'}`}>
            Annual Billing
            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full">
              Save 20%
            </span>
          </span>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {plansMock.map((plan) => {
          const effectivePrice = Math.round(plan.priceInr * discount);
          return (
            <div
              key={plan.id}
              className={`p-8 rounded-3xl bg-white border flex flex-col justify-between relative transition-all ${
                plan.isPopular
                  ? 'border-2 border-brand-500 shadow-xl ring-4 ring-brand-50'
                  : 'border-slate-200/90 shadow-xs hover:border-slate-300'
              }`}
            >
              {plan.isPopular && (
                <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-brand-600 text-white font-bold text-[10px] uppercase tracking-wider px-3 py-1 rounded-full shadow-xs">
                  Most Popular for Indian D2C
                </span>
              )}
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{plan.name}</span>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold text-charcoal">₹{effectivePrice.toLocaleString('en-IN')}</span>
                  <span className="text-xs text-slate-500">/ month</span>
                </div>
                {billingCycle === 'annual' && (
                  <span className="text-[11px] text-emerald-600 font-semibold block mt-1">
                    Billed annually (₹{(effectivePrice * 12).toLocaleString('en-IN')}/yr)
                  </span>
                )}
                <p className="text-xs text-slate-500 mt-3 leading-relaxed">{plan.description}</p>

                <div className="my-6 pt-6 border-t border-slate-100">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-3">
                    Included Quotas:
                  </span>
                  <ul className="space-y-3 text-xs text-slate-700">
                    <li className="flex items-center gap-2 font-semibold">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      Up to {plan.skuLimit} active master SKUs
                    </li>
                    <li className="flex items-center gap-2 font-semibold">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      Up to {plan.channelLimit} connected sales/social channels
                    </li>
                    {plan.features.slice(2).map((feature, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <Link
                to="/signup"
                className={`w-full py-3 rounded-xl text-center text-xs font-bold transition-all ${
                  plan.isPopular
                    ? 'bg-brand-600 hover:bg-brand-700 text-white shadow-md'
                    : 'border border-slate-300 hover:bg-slate-50 text-slate-700'
                }`}
              >
                Choose {plan.name}
              </Link>
            </div>
          );
        })}
      </div>

      {/* Managed Services Section */}
      <section className="p-8 sm:p-12 rounded-3xl bg-slate-100/70 border border-slate-200">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="text-xs font-bold uppercase tracking-wider text-amberbrand-700 bg-amberbrand-100 px-2.5 py-0.5 rounded-full">
            Optional High-Touch Services
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-charcoal mt-2">
            Need Expert Execution Support?
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 mt-2">
            Combine MarketPath software with hands-on assistance from our D2C growth operations team in Maharashtra.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {managedServicesMock.map((srv) => (
            <div key={srv.id} className="p-6 rounded-2xl bg-white border border-slate-200 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600">{srv.turnaround}</span>
                  <Sparkles className="w-4 h-4 text-amberbrand-500" />
                </div>
                <h3 className="text-base font-bold text-charcoal mt-2">{srv.title}</h3>
                <div className="mt-2 text-xl font-extrabold text-charcoal">
                  ₹{srv.priceInr.toLocaleString('en-IN')}
                </div>
                <p className="text-xs text-slate-500 mt-2">{srv.description}</p>
                <div className="my-4 pt-4 border-t border-slate-100 space-y-2">
                  {srv.deliverables.map((deliv, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-slate-600">
                      <span className="text-brand-600 font-bold">•</span>
                      <span>{deliv}</span>
                    </div>
                  ))}
                </div>
              </div>
              <Link
                to="/contact"
                className="block text-center py-2 rounded-lg border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-700 mt-4"
              >
                Inquire Service
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Trust & Guarantee Box */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-charcoal">100% Direct Account Ownership</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              MarketPath connects via official OAuth. You retain sole custody of your store and ad spend. No hidden commissions.
            </p>
          </div>
        </div>
        <Link
          to="/trust"
          className="text-xs font-semibold text-brand-600 hover:underline shrink-0"
        >
          Read Security Principles →
        </Link>
      </div>
    </div>
  );
};

