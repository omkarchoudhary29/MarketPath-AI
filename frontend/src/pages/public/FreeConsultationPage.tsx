import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Clock,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Building2,
  User,
  Mail,
  Phone,
  AlertCircle,
  Loader2,
  Check,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { apiClient } from '../../lib/api';

const CATEGORIES = [
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
  'Other',
];

const REVENUE_STAGES = [
  'Early Stage (< ₹5 Lakh/mo)',
  'Scaling (₹5 Lakh – ₹25 Lakh/mo)',
  'Growing (₹25 Lakh – ₹1 Crore/mo)',
  'Mature (> ₹1 Crore/mo)',
];

interface SlotInfo {
  slot: string;
  available: boolean;
  capacity: number;
  booked_count: number;
}

interface AvailabilityResponse {
  date: string;
  timezone: string;
  is_available: boolean;
  reason?: string | null;
  slots: SlotInfo[];
}

function getNextBusinessDayDateString(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  // If tomorrow is Sunday, skip to Monday
  if (d.getDay() === 0) {
    d.setDate(d.getDate() + 1);
  }
  return d.toISOString().split('T')[0];
}

function generateIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'idem-' + Math.random().toString(36).substring(2, 15) + '-' + Date.now();
}

export const FreeConsultationPage: React.FC = () => {
  const initialDate = getNextBusinessDayDateString();

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    brandName: '',
    category: 'Home & Decor',
    customCategory: '',
    businessStage: 'Scaling (₹5 Lakh – ₹25 Lakh/mo)',
    monthlyRevenue: '₹5L - ₹25L',
    challenges: '',
    preferredDate: initialDate,
    preferredTimeSlot: '',
  });

  const [idempotencyKey] = useState<string>(() => generateIdempotencyKey());

  // Dynamic Availability State
  const [slots, setSlots] = useState<SlotInfo[]>([]);
  const [isSlotsLoading, setIsSlotsLoading] = useState(false);
  const [dateAvailabilityReason, setDateAvailabilityReason] = useState<string | null>(null);
  const [isDateAvailable, setIsDateAvailable] = useState(true);

  // Submission State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [referenceCode, setReferenceCode] = useState<string | null>(null);
  const [bookingDetails, setBookingDetails] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch available slots whenever preferredDate changes
  useEffect(() => {
    if (!formData.preferredDate) {
      setSlots([]);
      setIsDateAvailable(true);
      setDateAvailabilityReason(null);
      return;
    }

    let isMounted = true;
    setIsSlotsLoading(true);
    setDateAvailabilityReason(null);

    apiClient<AvailabilityResponse>(`/api/v1/consultations/availability?date=${formData.preferredDate}`)
      .then((data) => {
        if (!isMounted) return;
        setIsDateAvailable(data.is_available);
        setDateAvailabilityReason(data.reason || null);
        setSlots(data.slots || []);

        // Auto-select the first available slot if currently selected is not in slots or unavailable
        const availableSlots = (data.slots || []).filter((s) => s.available);
        if (availableSlots.length > 0) {
          const currentlySelectedValid = availableSlots.some((s) => s.slot === formData.preferredTimeSlot);
          if (!currentlySelectedValid) {
            setFormData((prev) => ({ ...prev, preferredTimeSlot: availableSlots[0].slot }));
          }
        } else {
          setFormData((prev) => ({ ...prev, preferredTimeSlot: '' }));
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to fetch availability:', err);
        setIsDateAvailable(false);
        setDateAvailabilityReason('Unable to verify real-time slot availability for this date.');
        setSlots([]);
      })
      .finally(() => {
        if (isMounted) setIsSlotsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [formData.preferredDate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    const payload = {
      full_name: formData.fullName.trim(),
      email: formData.email.trim(),
      phone: formData.phone.trim() || null,
      brand_name: formData.brandName.trim(),
      category: formData.category === 'Other' && formData.customCategory ? formData.customCategory.trim() : formData.category,
      business_stage: formData.businessStage,
      monthly_revenue: formData.monthlyRevenue || null,
      challenges: formData.challenges.trim() || null,
      preferred_date: formData.preferredDate || null,
      preferred_time_slot: formData.preferredTimeSlot || null,
      timezone: 'Asia/Kolkata',
      idempotency_key: idempotencyKey,
    };

    try {
      const resData = await apiClient<any>('/api/v1/consultations', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setReferenceCode(resData.reference_code || 'MP-CONS-PROVISIONAL');
      setBookingDetails(resData);
      setIsSubmitted(true);
    } catch (err: any) {
      console.error('Consultation booking error:', err);
      setErrorMessage(err.message || 'Failed to submit consultation request. Please try another slot or verify your inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const todayStr = new Date().toISOString().split('T')[0];

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 bg-warmwhite">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-softbeige border border-bordergrey text-xs font-bold text-forest mb-2">
            <Sparkles className="w-3.5 h-3.5 text-softorange" />
            1-on-1 Growth Consultation
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-charcoal tracking-tight">
            Schedule a Free Omnichannel Strategy Session
          </h1>
          <p className="text-sm sm:text-base text-charcoal-muted leading-relaxed">
            Speak directly with our commerce growth specialists. We review your product catalog, marketplace readiness, and structure a custom expansion plan.
          </p>
        </div>

        {isSubmitted ? (
          <Card className="p-8 sm:p-12 text-center space-y-6 max-w-xl mx-auto border-bordergrey shadow-option-c">
            <div className="w-16 h-16 rounded-3xl bg-emerald-50 text-emerald flex items-center justify-center mx-auto border border-emerald-200">
              <CheckCircle2 className="w-9 h-9" />
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-extrabold text-charcoal tracking-tight">
                Consultation Request Received!
              </h2>

              <div className="flex items-center justify-center gap-2 pt-1">
                <span className="text-xs font-bold uppercase tracking-wider text-charcoal-muted">Booking Reference:</span>
                <span className="px-3 py-1 bg-softbeige text-forest font-mono font-bold text-sm rounded-lg border border-bordergrey">
                  {referenceCode}
                </span>
              </div>

              <div className="inline-block mt-2 px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-xs font-semibold">
                Status: Request Received (Awaiting Advisor Confirmation)
              </div>

              <p className="text-sm text-charcoal-muted leading-relaxed pt-2">
                Thank you, <strong className="text-charcoal">{formData.fullName}</strong>. A MarketPath senior advisor will review your brand details for <strong className="text-charcoal">{formData.brandName}</strong> and prepare your diagnostic roadmap.
              </p>
            </div>

            {/* Confirmed Details Card */}
            <div className="p-4 rounded-2xl bg-softbeige/50 border border-bordergrey text-xs text-charcoal-muted space-y-2 text-left">
              <div className="font-bold text-charcoal text-sm flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-forest" />
                Requested Session Window
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div>
                  <span className="text-charcoal-muted block">Date:</span>
                  <span className="font-bold text-charcoal">{bookingDetails?.preferred_date || formData.preferredDate || 'Flexible'}</span>
                </div>
                <div>
                  <span className="text-charcoal-muted block">Time Slot:</span>
                  <span className="font-bold text-charcoal">{bookingDetails?.preferred_time_slot || formData.preferredTimeSlot || 'Standard 30-min window'}</span>
                </div>
                <div>
                  <span className="text-charcoal-muted block">Timezone:</span>
                  <span className="font-bold text-charcoal">Asia/Kolkata (IST)</span>
                </div>
                <div>
                  <span className="text-charcoal-muted block">Email Delivery:</span>
                  <span className="font-mono text-forest font-semibold">{bookingDetails?.email_delivery_status || 'logged'}</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-bordergrey text-xs text-charcoal-muted space-y-1.5 text-left">
              <div className="font-bold text-charcoal">What to expect on your call:</div>
              <div>• Detailed review of your master SKU attributes and packaging specs</div>
              <div>• Channel expansion blueprint (Amazon, Flipkart, Shopify, Quick Commerce)</div>
              <div>• Guidance on AI Content Studio and verified Agency Connect matches</div>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link to="/">
                <Button variant="outline" size="md">
                  Return to Homepage
                </Button>
              </Link>
              <Link to="/signup">
                <Button size="md">
                  Create Brand Account <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </Link>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Context & Guarantees */}
            <div className="lg:col-span-5 space-y-6">
              <Card className="p-6 space-y-4">
                <h3 className="text-base font-bold text-charcoal">Why Book a Growth Consultation?</h3>
                <ul className="space-y-3 text-xs text-charcoal-muted leading-relaxed">
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald shrink-0 mt-0.5" />
                    <span><strong>Channel Suitability Audit:</strong> Determine whether Amazon, Flipkart, Myntra, or Blinkit fits your margins and category best.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald shrink-0 mt-0.5" />
                    <span><strong>Catalogue Architecture:</strong> Learn how to structure master products, variants, and carton volumetric weights to avoid shipping penalties.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald shrink-0 mt-0.5" />
                    <span><strong>No Pressure:</strong> Completely free 30-minute strategy session. Zero credit card or store credentials required.</span>
                  </li>
                </ul>
              </Card>

              <Card className="p-6 bg-softbeige/50 border-bordergrey space-y-3 text-xs">
                <div className="flex items-center gap-2 font-bold text-forest">
                  <ShieldCheck className="w-4 h-4 text-emerald" />
                  <span>Confidentiality Guarantee</span>
                </div>
                <p className="text-charcoal-muted leading-relaxed">
                  All brand information, margins, and roadmap details shared remain strictly private and will never be shared without your explicit consent.
                </p>
              </Card>

              <div className="p-4 rounded-2xl bg-white border border-bordergrey text-xs text-charcoal-muted space-y-2">
                <div className="font-bold text-charcoal flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-forest" /> Real-Time Availability
                </div>
                <p className="leading-relaxed">
                  Operating hours: <strong>Monday – Saturday, 10:00 AM – 6:00 PM IST</strong>. Slots are reserved exclusively on a 1-on-1 basis to ensure undivided advisory focus.
                </p>
              </div>
            </div>

            {/* Right Column: Intake Form */}
            <div className="lg:col-span-7">
              <Card className="p-6 sm:p-8">
                {errorMessage && (
                  <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2.5">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                    <div className="space-y-0.5">
                      <strong className="block font-bold">Booking Request Notice</strong>
                      <span>{errorMessage}</span>
                    </div>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Full Name */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Your Name *
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-charcoal-muted">
                          <User className="w-4 h-4" />
                        </div>
                        <input
                          type="text"
                          required
                          value={formData.fullName}
                          onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                          placeholder="Ananya Sharma"
                          className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                        />
                      </div>
                    </div>

                    {/* Email */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Work Email *
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-charcoal-muted">
                          <Mail className="w-4 h-4" />
                        </div>
                        <input
                          type="email"
                          required
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          placeholder="ananya@auraterra.in"
                          className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                        />
                      </div>
                    </div>

                    {/* Phone Number */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Phone Number (Optional)
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-charcoal-muted">
                          <Phone className="w-4 h-4" />
                        </div>
                        <input
                          type="tel"
                          value={formData.phone}
                          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                          placeholder="+91 98200 12345"
                          className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                        />
                      </div>
                    </div>

                    {/* Brand Name */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Brand / Business Name *
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-charcoal-muted">
                          <Building2 className="w-4 h-4" />
                        </div>
                        <input
                          type="text"
                          required
                          value={formData.brandName}
                          onChange={(e) => setFormData({ ...formData, brandName: e.target.value })}
                          placeholder="Aura Terra Living"
                          className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                        />
                      </div>
                    </div>

                    {/* Primary Category */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Primary Product Category *
                      </label>
                      <select
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white cursor-pointer"
                      >
                        {CATEGORIES.map((cat) => (
                          <option key={cat} value={cat}>
                            {cat}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Business Stage */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Business Stage & Scale
                      </label>
                      <select
                        value={formData.businessStage}
                        onChange={(e) => setFormData({ ...formData, businessStage: e.target.value })}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white cursor-pointer"
                      >
                        {REVENUE_STAGES.map((stg) => (
                          <option key={stg} value={stg}>
                            {stg}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Preferred Date */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Preferred Date *
                      </label>
                      <input
                        type="date"
                        required
                        value={formData.preferredDate}
                        onChange={(e) => setFormData({ ...formData, preferredDate: e.target.value })}
                        min={todayStr}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white cursor-pointer"
                      />
                    </div>

                    {/* Timezone Indicator */}
                    <div>
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                        Timezone
                      </label>
                      <div className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal bg-slate-50 flex items-center justify-between">
                        <span>Asia/Kolkata (IST)</span>
                        <span className="text-[11px] font-mono font-bold text-forest">UTC+5:30</span>
                      </div>
                    </div>
                  </div>

                  {/* Dynamic Time Slot Picker */}
                  <div className="space-y-2 pt-1">
                    <div className="flex items-center justify-between">
                      <label className="block text-xs font-bold text-charcoal uppercase tracking-wider">
                        Available Time Slots (IST) *
                      </label>
                      {isSlotsLoading && (
                        <span className="text-xs text-charcoal-muted flex items-center gap-1">
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-forest" />
                          Checking live availability...
                        </span>
                      )}
                    </div>

                    {dateAvailabilityReason && (
                      <div className="p-3.5 rounded-xl bg-softorange-50 border border-softorange-200 text-xs text-softorange-900 flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-softorange" />
                        <span>{dateAvailabilityReason}</span>
                      </div>
                    )}

                    {!isDateAvailable ? (
                      <div className="p-4 rounded-xl border border-dashed border-bordergrey text-center text-xs text-charcoal-muted">
                        Please choose an alternate date to see available advisory windows.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                        {slots.map((slotInfo) => {
                          const isSelected = formData.preferredTimeSlot === slotInfo.slot;
                          return (
                            <button
                              key={slotInfo.slot}
                              type="button"
                              disabled={!slotInfo.available}
                              onClick={() => setFormData({ ...formData, preferredTimeSlot: slotInfo.slot })}
                              className={`p-3 rounded-xl text-left border text-xs font-semibold transition-all flex flex-col justify-between gap-1 cursor-pointer ${
                                isSelected
                                  ? 'bg-softbeige text-forest border-brand-600 ring-2 ring-brand-500/30'
                                  : slotInfo.available
                                  ? 'bg-white text-charcoal border-bordergrey hover:border-brand-500 hover:bg-slate-50'
                                  : 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed opacity-60'
                              }`}
                            >
                              <div className="flex items-center justify-between w-full">
                                <span>{slotInfo.slot}</span>
                                {isSelected && <Check className="w-4 h-4 text-forest shrink-0" />}
                              </div>
                              <div className="text-[10px] font-normal">
                                {slotInfo.available ? (
                                  <span className="text-emerald font-semibold">● Available (1-on-1)</span>
                                ) : (
                                  <span className="text-slate-400">Reserved</span>
                                )}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Challenges & Objectives */}
                  <div>
                    <label className="block text-xs font-bold text-charcoal uppercase tracking-wider mb-1.5">
                      Primary Objectives & Challenges
                    </label>
                    <textarea
                      rows={3}
                      value={formData.challenges}
                      onChange={(e) => setFormData({ ...formData, challenges: e.target.value })}
                      placeholder="E.g., We sell on Shopify and want to expand to Amazon and Blinkit without duplicating catalogue work. Need guidance on AI content generation and agency partners."
                      className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey text-sm text-charcoal focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 bg-white"
                    />
                  </div>

                  {/* Trust Notice */}
                  <div className="flex items-center gap-2 text-xs text-charcoal-muted pt-1">
                    <ShieldCheck className="w-4 h-4 text-emerald shrink-0" />
                    <span>No obligation. We respect your confidentiality. Zero credentials or sensitive store data requested.</span>
                  </div>

                  {/* Submit Button */}
                  <div className="pt-2">
                    <Button
                      type="submit"
                      disabled={isSubmitting || !isDateAvailable || !formData.preferredTimeSlot}
                      className="w-full py-3 text-base font-bold shadow-sm"
                    >
                      {isSubmitting ? (
                        <span className="flex items-center justify-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Securing Consultation...
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          Request Free Consultation
                          <ArrowRight className="w-4 h-4" />
                        </span>
                      )}
                    </Button>
                  </div>
                </form>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
