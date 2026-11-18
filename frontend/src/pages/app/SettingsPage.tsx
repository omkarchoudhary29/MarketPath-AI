import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Settings, ShieldCheck, Download, Save, Globe, KeyRound } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { org, addToast } = useApp();
  const [formData, setFormData] = useState({
    name: org.name,
    slug: org.slug,
    currency: org.currency,
    timezone: org.timezone,
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    addToast({
      type: 'success',
      title: 'Settings Saved',
      message: 'Workspace configurations updated.',
    });
  };

  const handleDownloadAudit = () => {
    addToast({
      type: 'info',
      title: 'Exporting Security Audit Trail',
      message: 'JSON file prepared with timestamped user logins, publish operations, and budget approvals.',
    });
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200/80">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-600">Workspace Settings</span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-0.5">
          Organization & Security Settings
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Configure regional preferences, default currency, and inspect cryptographic audit logs.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Org Settings */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-5">
          <h3 className="text-base font-bold text-charcoal">Organization Profile</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Company Entity Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Workspace Slug</label>
              <input
                type="text"
                disabled
                value={formData.slug}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-500 font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Default Commerce Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200 bg-white"
              >
                <option value="INR">INR (₹ Indian Rupee)</option>
                <option value="USD">USD ($ US Dollar)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Primary Reporting Timezone</label>
              <select
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="w-full text-xs px-3.5 py-2 rounded-xl border border-slate-200 bg-white"
              >
                <option value="Asia/Kolkata (IST)">Asia/Kolkata (IST • UTC+05:30)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-xs cursor-pointer flex items-center gap-1.5"
            >
              <Save className="w-4 h-4" /> Save Settings
            </button>
          </div>
        </div>

        {/* Security & Audit Export */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-charcoal">Security & Compliance Audit</h3>
              <p className="text-xs text-slate-500">Download immutable event records for your legal compliance.</p>
            </div>
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2">
            <p>
              MarketPath maintains an append-only audit trail recording: OAuth token lifecycle events, product publishing timestamps, user permission escalations, and budget approvals.
            </p>
            <button
              type="button"
              onClick={handleDownloadAudit}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs cursor-pointer"
            >
              <Download className="w-4 h-4" /> Export Complete Audit Log (JSON)
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

