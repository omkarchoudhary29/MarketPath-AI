import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ChevronRight, Globe, Lock, Mail, MapPin, Phone, ShieldCheck, Sparkles, User, UserCheck } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const CONSULTANT_EXPERTISE_CATEGORIES = [
  'D2C Unit Economics & Margin Optimization',
  'Marketplace Scaling (Amazon & Flipkart)',
  'Packaging Engineering & Damage Reduction',
  'Omnichannel Supply Chain & Warehousing',
  'Brand Positioning & High-AOV Bundling',
  'Retention & Customer Lifetime Value (LTV)',
  'Organic Content & Founder-led Storytelling',
  'D2C Export Readiness & Global Expansion',
];

export const ConsultantSignupPage: React.FC = () => {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    phone: '',
    location: '',
    professionalTitle: '',
    expertise: [] as string[],
    yearsExperience: 5,
    bio: '',
    linkedinUrl: '',
    portfolioUrl: '',
    availability: 'part_time',
    agreed: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const toggleExpertise = (cat: string) => {
    setFormData((prev) => ({
      ...prev,
      expertise: prev.expertise.includes(cat)
        ? prev.expertise.filter((c) => c !== cat)
        : [...prev.expertise, cat],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.agreed) {
      setErrorMessage('Please accept the Advisor Code of Ethics and Confidentiality Agreement.');
      return;
    }
    if (formData.expertise.length === 0) {
      setErrorMessage('Please select at least one core domain of expertise.');
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    try {
      const res = await fetch('/api/v1/auth/consultant/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: formData.fullName.trim(),
          email: formData.email.trim().toLowerCase(),
          password: formData.password,
          phone: formData.phone.trim() || undefined,
          location: formData.location.trim(),
          professional_title: formData.professionalTitle.trim(),
          expertise_categories: formData.expertise,
          years_of_experience: Number(formData.yearsExperience) || 1,
          bio: formData.bio.trim(),
          linkedin_url: formData.linkedinUrl.trim() || undefined,
          portfolio_url: formData.portfolioUrl.trim() || undefined,
          availability: formData.availability,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Consultant registration could not be processed.');
      }

      setIsSubmitted(true);
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred during consultant registration.');
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
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-softbeige border border-bordergrey text-[11px] font-bold text-softorange">
            <UserCheck className="w-3.5 h-3.5" />
            <span>Advisory Council</span>
          </div>
          <h2 className="text-2xl font-extrabold text-charcoal tracking-tight">Join as a Growth Consultant</h2>
          <p className="text-xs text-charcoal-muted max-w-md mx-auto">
            Provide diagnostic growth sessions, category audits, and strategy consultations to emerging Indian D2C brands.
          </p>
        </div>

        {isSubmitted ? (
          <div className="text-center py-8 space-y-5">
            <div className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center mx-auto text-emerald-600 shadow-sm">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold text-charcoal">Advisory Application Received</h3>
              <p className="text-xs text-charcoal-muted max-w-md mx-auto leading-relaxed">
                Thank you for applying to the MarketPath Advisory Network. Your credentials are currently <strong className="text-forest font-semibold">Under Review</strong> by our category board. You will receive an onboarding confirmation email once approved.
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-softbeige/60 border border-bordergrey text-xs text-charcoal space-y-1.5 text-left max-w-md mx-auto">
              <div className="font-bold text-forest flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" /> What Happens Next:
              </div>
              <p className="text-charcoal-muted">1. Credentials and track record evaluation by the advisory board.</p>
              <p className="text-charcoal-muted">2. Calendar availability & consultation dispatch integration.</p>
              <p className="text-charcoal-muted">3. Direct access to assigned founder diagnostic sessions and private notes.</p>
            </div>
            <div className="pt-2">
              <Link to="/login?type=consultant">
                <Button className="px-6 py-2.5 text-xs font-bold">
                  Go to Consultant Login <ChevronRight className="w-4 h-4 ml-1" />
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
              {/* Name & Professional Title */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Full Legal Name *
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="text"
                      required
                      value={formData.fullName}
                      onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                      placeholder="e.g. Dr. Rajesh Sharma"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Professional Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.professionalTitle}
                    onChange={(e) => setFormData({ ...formData, professionalTitle: e.target.value })}
                    placeholder="e.g. Lead D2C Growth Advisor"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>
              </div>

              {/* Email & Password */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Professional Email *
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="advisor@consulting.in"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Workspace Password *
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

              {/* Phone, Location, Experience */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+91 98201 00000"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Location (City, State) *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="e.g. Mumbai, MH"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Years of Advisory Exp.
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={40}
                    value={formData.yearsExperience}
                    onChange={(e) => setFormData({ ...formData, yearsExperience: parseInt(e.target.value) || 1 })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                  />
                </div>
              </div>

              {/* Expertise Categories */}
              <div>
                <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                  Core Advisory Domains * (Select All That Apply)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {CONSULTANT_EXPERTISE_CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => toggleExpertise(cat)}
                      className={`text-left text-xs p-2.5 rounded-xl border transition-all flex items-center justify-between cursor-pointer ${
                        formData.expertise.includes(cat)
                          ? 'border-forest bg-forest/5 text-forest font-bold'
                          : 'border-bordergrey bg-white text-charcoal hover:border-forest/40'
                      }`}
                    >
                      <span>{cat}</span>
                      {formData.expertise.includes(cat) && <CheckCircle2 className="w-3.5 h-3.5 shrink-0 ml-1 text-forest" />}
                    </button>
                  ))}
                </div>
              </div>

              {/* Bio */}
              <div>
                <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                  Professional Bio & Executive Background *
                </label>
                <textarea
                  required
                  rows={3}
                  value={formData.bio}
                  onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                  placeholder="Outline your background advising brands, past leadership roles, and notable case outcomes..."
                  className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                />
              </div>

              {/* LinkedIn & Portfolio */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    LinkedIn Profile URL
                  </label>
                  <div className="relative">
                    <Globe className="w-4 h-4 absolute left-3.5 top-3 text-charcoal-muted pointer-events-none" />
                    <input
                      type="url"
                      value={formData.linkedinUrl}
                      onChange={(e) => setFormData({ ...formData, linkedinUrl: e.target.value })}
                      placeholder="https://linkedin.com/in/username"
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                    Availability Mode
                  </label>
                  <select
                    value={formData.availability}
                    onChange={(e) => setFormData({ ...formData, availability: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-xs text-charcoal focus:ring-2 focus:ring-forest/20 focus:border-forest bg-white"
                  >
                    <option value="advisory">Advisory Only (2-4 hrs/wk)</option>
                    <option value="part_time">Part-Time (5-10 hrs/wk)</option>
                    <option value="full_time">Full-Time Available</option>
                  </select>
                </div>
              </div>

              {/* Code of ethics acceptance */}
              <div className="pt-2">
                <label className="flex items-start gap-2.5 text-xs text-charcoal-muted cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.agreed}
                    onChange={(e) => setFormData({ ...formData, agreed: e.target.checked })}
                    className="mt-0.5 rounded border-bordergrey text-forest focus:ring-forest"
                  />
                  <span>
                    I agree to the MarketPath Advisor Code of Ethics, fiduciary merchant confidentiality, and independent advisory guidelines.
                  </span>
                </label>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 text-sm font-bold shadow-sm"
              >
                {isLoading ? 'Submitting Advisor Application...' : 'Submit Advisor Application'}
              </Button>
            </form>

            <div className="text-center pt-3 border-t border-bordergrey">
              <p className="text-xs text-charcoal-muted">
                Already approved as an advisor?{' '}
                <Link to="/login?type=consultant" className="font-bold text-forest hover:underline">
                  Sign in to Advisory Workspace
                </Link>
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
