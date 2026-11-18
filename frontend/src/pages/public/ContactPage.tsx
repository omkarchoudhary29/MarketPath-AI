import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, CheckCircle2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const ContactPage: React.FC = () => {
  const { addToast } = useApp();
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    brandName: '',
    email: '',
    phone: '',
    category: 'Home & Kitchen',
    message: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    addToast({
      type: 'success',
      title: 'Message Sent Successfully',
      message: 'Our founder / operations team in Pune will contact you within 24 hours.',
    });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-600">Get in Touch</span>
        <h1 className="text-4xl font-extrabold text-charcoal">Connect with MarketPath AI</h1>
        <p className="text-slate-600 text-sm sm:text-base">
          Whether you want to explore a customized pilot or need help onboarding your catalogue, we are here.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Contact Info Card */}
        <div className="p-8 rounded-3xl bg-slate-900 text-white space-y-8 flex flex-col justify-between">
          <div className="space-y-6">
            <h3 className="text-xl font-bold text-white">Direct Communication</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              We work closely with emerging D2C brands across Maharashtra and major Indian cities.
            </p>

            <div className="space-y-4 text-xs text-slate-300">
              <div className="flex items-start gap-3">
                <MapPin className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Pune Office:</span>
                  <span>Kalyani Nagar & Baner Tech Corridor, Pune, MH, India</span>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Mail className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Inquiries:</span>
                  <span>hello@marketpath.ai</span>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Phone className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Founder Desk:</span>
                  <span>+91 98220 00000</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-800/80 border border-slate-700 text-[11px] text-slate-400">
            Current Pilot: Offering 30-day guided onboarding for Pune & Mumbai home/lifestyle brands.
          </div>
        </div>

        {/* Form */}
        <div className="lg:col-span-2 p-8 sm:p-10 rounded-3xl bg-white border border-slate-200/90 shadow-xs">
          {submitted ? (
            <div className="py-12 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold text-charcoal">Thank You, {formData.name}!</h3>
              <p className="text-sm text-slate-600 max-w-md mx-auto">
                We received your note regarding <strong>{formData.brandName}</strong>. Our team will get back to you shortly.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Your Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Vikram Sharma"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Brand Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Mitti Living"
                    value={formData.brandName}
                    onChange={(e) => setFormData({ ...formData, brandName: e.target.value })}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Work Email *</label>
                  <input
                    type="email"
                    required
                    placeholder="founder@brand.in"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Phone / WhatsApp</label>
                  <input
                    type="tel"
                    placeholder="+91 98000 00000"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Primary Product Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                >
                  <option>Home & Kitchen Ceramics</option>
                  <option>Soy Candles & Aromatherapy</option>
                  <option>Handcrafted Woodware</option>
                  <option>Block-printed Textiles & Linen</option>
                  <option>Artisanal Gifting & Hampers</option>
                  <option>Other D2C Category</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">How can we help your brand?</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Tell us about your current channels (Shopify, Instagram) and growth goals..."
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <button
                type="submit"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-xs transition-colors cursor-pointer"
              >
                <Send className="w-4 h-4" />
                Submit Inquiry
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

