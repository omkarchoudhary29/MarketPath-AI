import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { HelpCircle, BookOpen, Send, CheckCircle2, Video, MessageSquare } from 'lucide-react';

export const HelpPage: React.FC = () => {
  const { addToast } = useApp();
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketMessage, setTicketMessage] = useState('');
  const [ticketSubmitted, setTicketSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setTicketSubmitted(true);
    addToast({
      type: 'success',
      title: 'Support Ticket #MP-892 Created',
      message: 'Priority support response dispatched within 4 business hours.',
    });
  };

  const guides = [
    {
      title: 'Connecting a Shopify Development Store',
      desc: 'Step-by-step instructions on creating a custom app, generating Admin API scopes, and validating OAuth handshake.',
      tag: 'Shopify Admin GraphQL',
    },
    {
      title: 'Instagram Professional & Meta Page Linking',
      desc: 'How to convert personal Instagram accounts to Creator/Business and bind them to your brand Facebook Page.',
      tag: 'Meta Graph API',
    },
    {
      title: 'Structuring Master Catalogue Variants & SKU Families',
      desc: 'Best practices for organizing multi-attribute variants without causing channel synchronization rejections.',
      tag: 'Master Catalogue',
    },
    {
      title: 'Setting Ad Spend Stop-Loss Limits in MarketPath',
      desc: 'How to use our Human-in-the-Loop approval workflows to prevent accidental budget overruns on Meta Ads.',
      tag: 'Marketing Studio',
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200/80">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-600">Knowledge & Support</span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-0.5">
          Documentation & Seller Help Centre
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Technical integration guides, troubleshooting steps, and direct access to our operations team.
        </p>
      </div>

      {/* Guide Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {guides.map((g, i) => (
          <div key={i} className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-2xs space-y-2 hover:border-slate-300 transition-all">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-700 bg-brand-50 px-2 py-0.5 rounded">
              {g.tag}
            </span>
            <h3 className="text-sm font-bold text-charcoal">{g.title}</h3>
            <p className="text-xs text-slate-500 leading-relaxed">{g.desc}</p>
            <a href="#read" className="inline-block text-xs font-semibold text-brand-600 hover:underline pt-2">
              Read Guide →
            </a>
          </div>
        ))}
      </div>

      {/* Direct Ticket Submission */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <MessageSquare className="w-5 h-5 text-brand-600" />
          <h3 className="text-base font-bold text-charcoal">Submit a Support Request</h3>
        </div>

        {ticketSubmitted ? (
          <div className="p-6 bg-emerald-50 rounded-2xl text-center space-y-2 text-emerald-900">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
            <h4 className="text-sm font-bold">Ticket Submitted (#MP-892)</h4>
            <p className="text-xs">
              Our support engineer in Pune has received your inquiry. We typically reply in under 4 hours.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Subject</label>
              <input
                type="text"
                required
                placeholder="e.g. Shopify channel sync error on ceramic mugs"
                value={ticketSubject}
                onChange={(e) => setTicketSubject(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Detailed Description</label>
              <textarea
                rows={4}
                required
                placeholder="Include SKU IDs, error codes, or screenshots if applicable..."
                value={ticketMessage}
                onChange={(e) => setTicketMessage(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-xs cursor-pointer flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              Dispatch Ticket to Operations
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

