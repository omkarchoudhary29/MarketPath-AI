import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Building2, CheckCircle2, ChevronRight, Globe, Lock, Mail, MapPin, Phone, ShieldCheck, Sparkles, User } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const AGENCY_SERVICES = [
  'Performance Marketing (Meta & Google)',
  'Creative Studio & UGC Production',
  'Marketplace Account Management (Amazon & Flipkart)',
  'Shopify & Storefront Development',
  'Catalogue Photography & 3D Renders',
  'Retention & WhatsApp Marketing',
  'Influencer Collaborations & PR',
  'SEO & Organic Search Scaling',
];

export const AgencySignupPage: React.FC = () => {
  const [formData, setFormData] = useState({
    agencyName: '',
    contactName: '',
    email: '',
    password: '',
    phone: '',
    website: '',
    city: '',
    state: '',
    services: [] as string[],
    yearsExperience: 2,
    portfolioUrl: '',
    description: '',
    gstNumber: '',
    agreed: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const toggleService = (srv: string) => {
    setFormData((prev) => ({
      ...prev,
      services: prev.services.includes(srv)
        ? prev.services.filter((s) => s !== srv)
        : [...prev.services, srv],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.agreed) {
      setErrorMessage('Please accept the Partner Code of Conduct and Terms of Service.');
      return;
    }
    if (formData.services.length === 0) {
      setErrorMessage('Please select at least one core service category.');
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    try {
      const res = await fetch('/api/v1/auth/agency/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agency_name: formData.agencyName.trim(),
          contact_name: formData.contactName.trim(),
          email: formData.email.trim().toLowerCase(),
          password: formData.password,
          phone: formData.phone.trim() || undefined,
          website: formData.website.trim() || undefined,
          city: formData.city.trim(),
          state: formData.state.trim(),
          service_categories: formData.services,
          years_of_experience: Number(formData.yearsExperience) || 1,
          portfolio_url: formData.portfolioUrl.trim() || undefined,
          description: formData.description.trim(),
          gst_number: formData.gstNumber.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Agency registration could not be processed.');
      }

      setIsSubmitted(true);
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred during agency registration.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-warmwhite">
      <div className="max-w-2xl w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl border border-bordergrey shadow-option-c-lg">
        {/* Header */}
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center gap-2 mb-2">
            <div className="w-9 h-9 rounded-xl bg-forest bg-gradient-to-tr from-[#075443] via-[#08765B] to-[#15966F] border border-[#15966F]/40 flex items-center justify-center text-white font-extrabold text-sm shadow-sm">
              MP
            </div>
            <span className="text-xl font-bold text-charcoal tracking-tight">MarketPath AI</span>
          </Link>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-softbeige border border-bordergrey text-[11px] font-bold text-forest">
            <Briefcase className="w-3.5 h-3.5" />
            <span>Agency Partner Network</span>
          </div>
          <h2 className="text-2xl font-extrabold text-charcoal tracking-tight">Apply as a Growth Partner</h2>
          <p className="text-xs text-charcoal-muted max-w-md mx-auto">
            Connect with verified D2C brand founders seeking high-performance marketing, creative production, and marketplace scaling.
          </p>
        </div>

        {isSubmitted ? (
          <div className="text-center py-8 space-y-5">
            <div className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center mx-auto text-emerald-600 shadow-sm">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold text-charcoal">Agency Application Submitted</h3>
              <p className="text-xs text-charcoal-muted max-w-md mx-auto leading-relaxed">
                Thank you for applying to the MarketPath Partner Network. Your application is currently <strong className="text-forest font-semibold">Under Review</strong>. Our operations team will verify your portfolio and activate your portal access within 24–48 hours.
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-softbeige/60 border border-bordergrey text-xs text-charcoal space-y-1.5 text-left max-w-md mx-auto">
              <div className="font-bold text-forest flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" /> Next Steps:
              </div>
              <p className="text-charcoal-muted">1. Account verification email dispatched to <strong>{formData.email}</strong>.</p>
              <p className="text-charcoal-muted">2. Platform review for service capability alignment.</p>
              <p className="text-charcoal-muted">3. Direct access granted to inbound RFPs and proposal management.</p>
            </div>
            <div className="pt-2">
              <Link to="/login?type=agency">
                <Button className="px-6 py-2.5 text-xs font-bold">
                  Go to Partner Login <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <>
            {errorMessage && (
              <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 leading-relaxed">
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Agency Name & Contact */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Agency Business Name *
                  </label>
                  <div className="relative">
                    <Building2 className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="text"
                      required
                      value={formData.agencyName}
                      onChange={(e) => setFormData({ ...formData, agencyName: e.target.value })}
                      placeholder="e.g. CraftVerve Media"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Primary Contact Name *
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="text"
                      required
                      value={formData.contactName}
                      onChange={(e) => setFormData({ ...formData, contactName: e.target.value })}
                      placeholder="e.g. Vikram Mehta"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>
              </div>

              {/* Email & Password */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Business Email *
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="partner@youragency.in"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Portal Password *
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="At least 8 characters"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>
              </div>

              {/* Phone & Website */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+91 98765 43210"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Agency Website
                  </label>
                  <div className="relative">
                    <Globe className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="url"
                      value={formData.website}
                      onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                      placeholder="https://youragency.in"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>
              </div>

              {/* Location & Experience */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    City *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    placeholder="e.g. Pune"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    State *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.state}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    placeholder="e.g. Maharashtra"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Years in Business
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={50}
                    value={formData.yearsExperience}
                    onChange={(e) => setFormData({ ...formData, yearsExperience: parseInt(e.target.value) || 1 })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>
              </div>

              {/* Service Categories */}
              <div>
                <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                  Core Service Offerings * (Select All That Apply)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {AGENCY_SERVICES.map((srv) => (
                    <button
                      key={srv}
                      type="button"
                      onClick={() => toggleService(srv)}
                      className={`text-left text-xs p-2.5 rounded-xl border transition-all flex items-center justify-between cursor-pointer ${
                        formData.services.includes(srv)
                          ? 'border-forest bg-forest/5 text-forest font-bold'
                          : 'border-bordergrey bg-white text-charcoal hover:border-forest/40'
                      }`}
                    >
                      <span>{srv}</span>
                      {formData.services.includes(srv) && <CheckCircle2 className="w-3.5 h-3.5 shrink-0 ml-1 text-forest" />}
                    </button>
                  ))}
                </div>
              </div>

              {/* Description & Portfolio */}
              <div>
                <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                  Agency Overview & Track Record *
                </label>
                <textarea
                  required
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Tell brand owners about your client portfolio, average ROAS delivered, and core expertise..."
                  className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                />
              </div>

              {/* Portfolio URL & GST */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Case Studies / Portfolio Link
                  </label>
                  <input
                    type="url"
                    value={formData.portfolioUrl}
                    onChange={(e) => setFormData({ ...formData, portfolioUrl: e.target.value })}
                    placeholder="https://drive.google.com/deck or notion"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    GST Number (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.gstNumber}
                    onChange={(e) => setFormData({ ...formData, gstNumber: e.target.value })}
                    placeholder="27AAAAA0000A1Z5"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>
              </div>

              {/* Code of conduct acceptance */}
              <div className="pt-2">
                <label className="flex items-start gap-2.5 text-xs text-charcoal-muted cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.agreed}
                    onChange={(e) => setFormData({ ...formData, agreed: e.target.checked })}
                    className="mt-0.5 rounded border-bordergrey text-forest focus:ring-forest"
                  />
                  <span>
                    I confirm that our agency complies with the MarketPath Partner Code of Conduct and will safeguard merchant data confidentiality.
                  </span>
                </label>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 text-sm font-bold shadow-sm"
              >
                {isLoading ? 'Submitting Partner Application...' : 'Submit Partner Application'}
              </Button>
            </form>

            <div className="text-center pt-3 border-t border-bordergrey">
              <p className="text-xs text-charcoal-muted">
                Already registered as an agency partner?{' '}
                <Link to="/login?type=agency" className="font-bold text-forest hover:underline">
                  Sign in to Agency Portal
                </Link>
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
