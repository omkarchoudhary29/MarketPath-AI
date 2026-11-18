import React, { useState } from 'react';
import { Calendar, Clock, Video, CheckCircle2, Sparkles } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const BookDemoPage: React.FC = () => {
  const { addToast } = useApp();
  const [booked, setBooked] = useState(false);
  const [selectedDate, setSelectedDate] = useState('Tomorrow, 3:00 PM IST');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    brandName: '',
    storeUrl: '',
    monthlySales: '₹1L – ₹5L / month',
  });

  const slots = [
    'Tomorrow, 11:30 AM IST',
    'Tomorrow, 3:00 PM IST',
    'Thursday, 2:00 PM IST',
    'Thursday, 5:30 PM IST',
    'Friday, 12:00 PM IST',
  ];

  const handleBooking = (e: React.FormEvent) => {
    e.preventDefault();
    setBooked(true);
    addToast({
      type: 'success',
      title: 'Demo Session Confirmed',
      message: `Google Meet link dispatched to ${formData.email} for ${selectedDate}.`,
    });
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-3 py-1 rounded-full">
          Personalized Growth Walkthrough
        </span>
        <h1 className="text-4xl font-extrabold text-charcoal">Book a Live 1-on-1 Strategy Demo</h1>
        <p className="text-slate-600 text-sm sm:text-base">
          30 minutes with a MarketPath product architect. See how your specific brand catalogue connects to Shopify, Instagram, and campaign planning.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Value Highlights */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-2xs space-y-5">
          <h3 className="text-sm font-bold text-charcoal uppercase tracking-wider">What We Will Cover</h3>
          <ul className="space-y-3.5 text-xs text-slate-600">
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>Reviewing your current SKU catalog & channel setup.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>Live AI Content Studio generation using your brand tone.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>Demonstration of authorized Shopify & Meta publishing queue.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>Campaign brief planning & ad budget stop-loss limits.</span>
            </li>
          </ul>

          <div className="p-4 rounded-xl bg-brand-50/60 border border-brand-100 flex items-center gap-3 text-xs text-brand-900 font-medium">
            <Video className="w-5 h-5 text-brand-600 shrink-0" />
            <span>Hosted via Google Meet. Recording provided after session.</span>
          </div>
        </div>

        {/* Booking Form */}
        <div className="lg:col-span-2 p-8 sm:p-10 rounded-3xl bg-white border border-slate-200/90 shadow-md">
          {booked ? (
            <div className="py-10 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
                <Calendar className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold text-charcoal">Demo Confirmed!</h3>
              <p className="text-sm text-slate-600 max-w-md mx-auto">
                We're excited to meet you, <strong>{formData.name}</strong>. A calendar invite for <strong>{selectedDate}</strong> has been sent to <strong>{formData.email}</strong>.
              </p>
            </div>
          ) : (
            <form onSubmit={handleBooking} className="space-y-5">
              <h3 className="text-lg font-bold text-charcoal">Select Preferred Date & Time</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {slots.map((slot) => (
                  <button
                    key={slot}
                    type="button"
                    onClick={() => setSelectedDate(slot)}
                    className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all cursor-pointer flex items-center gap-2 ${
                      selectedDate === slot
                        ? 'bg-brand-50 border-brand-500 text-brand-800 ring-2 ring-brand-100'
                        : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <Clock className="w-4 h-4 text-slate-400 shrink-0" />
                    <span>{slot}</span>
                  </button>
                ))}
              </div>

              <div className="pt-4 border-t border-slate-100 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Full Name *</label>
                    <input
                      type="text"
                      required
                      placeholder="Ananya Deshmukh"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
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
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Brand Name *</label>
                    <input
                      type="text"
                      required
                      placeholder="Aura Terra Living"
                      value={formData.brandName}
                      onChange={(e) => setFormData({ ...formData, brandName: e.target.value })}
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-charcoal mb-1">Online Store / Instagram Handle</label>
                    <input
                      type="text"
                      placeholder="auraterra.in or @auraterraliving"
                      value={formData.storeUrl}
                      onChange={(e) => setFormData({ ...formData, storeUrl: e.target.value })}
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">Current Monthly D2C Revenue</label>
                  <select
                    value={formData.monthlySales}
                    onChange={(e) => setFormData({ ...formData, monthlySales: e.target.value })}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                  >
                    <option>Pre-launch / Planning phase</option>
                    <option>Under ₹1 Lakh / month</option>
                    <option>₹1 Lakh – ₹5 Lakhs / month</option>
                    <option>₹5 Lakhs – ₹20 Lakhs / month</option>
                    <option>₹20 Lakhs+ / month</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-3.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-md transition-all cursor-pointer flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                Confirm 1-on-1 Walkthrough ({selectedDate})
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

