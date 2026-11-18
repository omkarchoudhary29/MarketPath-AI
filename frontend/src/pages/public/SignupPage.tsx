import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { UserPlus, Sparkles, Lock, Mail, Building2, User, AlertCircle, Tag, Globe, ArrowRight, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const D2C_CATEGORIES = [
  'Home & Living / Decor',
  'Kitchen & Dining',
  'Artisanal Gifting & Hampers',
  'Lifestyle & Wellness',
  'Organic Food & Gourmet Staples',
  'Health Supplements & Nutraceuticals',
  'Clean Skincare & Beauty',
  'Sustainable Fashion & Apparel',
  'Footwear & Everyday Bags',
  'Handcrafted Jewellery & Accessories',
  'Specialty Tea & Single-Origin Coffee',
  'Baby & Kids Essentials',
  'Pet Care & Functional Nutrition',
  'Fragrance, Attars & Aromatherapy',
  'Eco-Friendly Cleaning & Household',
  'Stationery & Hand-bound Journals',
  'Fitness Equipment & Athleisure',
  'Indian Regional Heritage Crafts',
  'Consumer Electronics & Smart Accessories',
  'Other',
];

export const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const { registerCompany } = useAuth();
  const { addToast } = useApp();

  const [formData, setFormData] = useState({
    brandName: '',
    fullName: '',
    email: '',
    password: '',
    category: 'Home & Living / Decor',
    customCategory: '',
    websiteUrl: '',
    agreed: true,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.agreed) {
      setErrorMessage('Please accept the Terms of Service to continue.');
      return;
    }

    if (formData.category === 'Other' && !formData.customCategory.trim()) {
      setErrorMessage('Please specify your custom business category.');
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    const res = await registerCompany({
      brand_name: formData.brandName.trim(),
      category: formData.category === 'Other' ? formData.customCategory.trim() : formData.category,
      custom_category: formData.category === 'Other' ? formData.customCategory.trim() : undefined,
      founder_name: formData.fullName.trim(),
      email: formData.email.trim().toLowerCase(),
      password: formData.password,
      website_url: formData.websiteUrl.trim() || undefined,
    });
    setIsLoading(false);

    if (res.success) {
      addToast({
        type: 'success',
        title: 'Brand Workspace Initialized!',
        message: `Welcome to MarketPath AI, ${formData.fullName}! Your workspace is active.`,
      });
      navigate(res.redirect_url || '/app/dashboard');
    } else {
      setErrorMessage(res.error || 'Failed to create brand workspace.');
      addToast({
        type: 'error',
        title: 'Registration Failed',
        message: res.error || 'Could not register organization.',
      });
    }
  };

  return (
    <div className="min-h-[90vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-warmwhite">
      <div className="max-w-lg w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl border border-bordergrey shadow-option-c-lg">
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center gap-2 mb-2">
            <div className="w-9 h-9 rounded-xl bg-forest bg-gradient-to-tr from-[#075443] via-[#08765B] to-[#15966F] border border-[#15966F]/40 flex items-center justify-center text-white font-extrabold text-sm shadow-sm">
              MP
            </div>
            <span className="text-xl font-bold text-charcoal tracking-tight">MarketPath AI</span>
          </Link>
          <h2 className="text-2xl font-extrabold text-charcoal tracking-tight">Start Your Brand Workspace</h2>
          <p className="text-xs text-charcoal-muted">
            Already have an account?{' '}
            <Link to="/login" className="font-bold text-brand-600 hover:text-forest hover:underline">
              Sign in here
            </Link>
          </p>
        </div>

        <div className="p-3.5 bg-softbeige/70 border border-bordergrey rounded-2xl text-xs text-charcoal flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-softorange shrink-0" />
          <span className="font-medium">
            Setup your master product catalogue, connected channels, and AI content studio in minutes.
          </span>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSignup} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1 uppercase tracking-wider">Brand Name *</label>
              <div className="relative">
                <Building2 className="w-4 h-4 text-charcoal-muted absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Aura Terra Living"
                  value={formData.brandName}
                  onChange={(e) => setFormData({ ...formData, brandName: e.target.value })}
                  className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-bordergrey focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-charcoal mb-1 uppercase tracking-wider">Founder Name *</label>
              <div className="relative">
                <User className="w-4 h-4 text-charcoal-muted absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Ananya Deshmukh"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-bordergrey focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-charcoal mb-1 uppercase tracking-wider">Primary Product Category *</label>
            <div className="relative">
              <Tag className="w-4 h-4 text-charcoal-muted absolute left-3 top-3" />
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-bordergrey focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white cursor-pointer"
              >
                {D2C_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {formData.category === 'Other' && (
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1 uppercase tracking-wider">Specify Custom Category *</label>
              <input
                type="text"
                required
                placeholder="e.g. Vegan Leather Accessories"
                value={formData.customCategory}
                onChange={(e) => setFormData({ ...formData, customCategory: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-bordergrey focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-charcoal mb-1 uppercase tracking-wider">Work / Business Email *</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-charcoal-muted absolute left-3 top-3" />
              <input
                type="email"
                required
                placeholder="founder@yourbrand.com or name@gmail.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-bordergrey focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1 uppercase tracking-wider">Password *</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-charcoal-muted absolute left-3 top-3" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={8}
                  placeholder="Min 8 characters"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full text-xs pl-9 pr-10 py-2.5 rounded-xl border border-bordergrey focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-charcoal-muted hover:text-charcoal cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-charcoal mb-1 uppercase tracking-wider">Website URL (Optional)</label>
              <div className="relative">
                <Globe className="w-4 h-4 text-charcoal-muted absolute left-3 top-3" />
                <input
                  type="url"
                  placeholder="https://yourbrand.com"
                  value={formData.websiteUrl}
                  onChange={(e) => setFormData({ ...formData, websiteUrl: e.target.value })}
                  className="w-full text-xs pl-9 pr-3.5 py-2.5 rounded-xl border border-bordergrey focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                />
              </div>
            </div>
          </div>

          <div className="flex items-start pt-1">
            <input
              id="terms"
              type="checkbox"
              checked={formData.agreed}
              onChange={(e) => setFormData({ ...formData, agreed: e.target.checked })}
              className="h-4 w-4 text-brand-600 focus:ring-brand-500 border-bordergrey rounded mt-0.5"
            />
            <label htmlFor="terms" className="ml-2 block text-xs text-charcoal-muted leading-tight">
              I agree to the{' '}
              <Link to="/about#trust-security" className="text-brand-600 font-semibold hover:underline">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link to="/about#trust-security" className="text-brand-600 font-semibold hover:underline">
                Privacy Policy
              </Link>
              . No credit card required.
            </label>
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 text-sm font-bold shadow-sm"
          >
            {isLoading ? 'Initializing Workspace...' : 'Initialize Brand Workspace'}
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </form>
      </div>
    </div>
  );
};
