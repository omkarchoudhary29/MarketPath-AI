import React, { useEffect, useState } from 'react';
import { Sliders, Save, CheckCircle2, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';

interface PlanItem {
  id: string;
  name: string;
  monthly_price_inr: number;
  max_active_skus: number;
  max_connected_channels: number;
  ai_generation_monthly_quota: number;
  description?: string;
  is_active: boolean;
}

export const AdminPlansPage: React.FC = () => {
  const { session } = useAuth();
  const { addToast } = useApp();
  const token = session?.access_token;

  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!token) return;
    apiClient<PlanItem[]>('/api/v1/admin/plans', { token })
      .then((data) => setPlans(data))
      .catch((err) => console.error('Failed to load plans:', err))
      .finally(() => setIsLoading(false));
  }, [token]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setIsSaving(true);
    try {
      await Promise.all(
        plans.map((p) =>
          apiClient(`/api/v1/admin/plans/${p.id}`, {
            method: 'PUT',
            token,
            body: JSON.stringify({
              monthly_price_inr: p.monthly_price_inr,
              max_active_skus: p.max_active_skus,
              max_connected_channels: p.max_connected_channels,
              ai_generation_monthly_quota: p.ai_generation_monthly_quota,
            }),
          })
        )
      );

      addToast({
        type: 'success',
        title: 'Plan Tier Limits Updated',
        message: 'Dynamic quotas pushed to database. New subscriptions will consume revised quotas.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: err.message || 'Could not update plans.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="pb-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-rose-400">Dynamic Pricing</span>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
            Subscription Plan & Quota Configurator
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Edit platform subscription prices and resource quotas without hardcoded code changes.
          </p>
        </div>
        {isLoading && <RefreshCw className="w-5 h-5 text-rose-500 animate-spin" />}
      </div>

      <form onSubmit={handleUpdate} className="space-y-5 font-mono text-xs">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((p, idx) => (
            <div key={p.id} className="p-6 rounded-3xl bg-slate-950 border border-slate-800 space-y-4">
              <span className="font-bold text-white text-sm block">{p.name} Tier</span>
              <div>
                <label className="block text-slate-400 text-[11px] mb-1">Price (₹/mo)</label>
                <input
                  type="number"
                  value={p.monthly_price_inr}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setPlans((prev) => prev.map((pl, i) => (i === idx ? { ...pl, monthly_price_inr: val } : pl)));
                  }}
                  className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 text-white font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[11px] mb-1">Max Master SKUs</label>
                <input
                  type="number"
                  value={p.max_active_skus}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setPlans((prev) => prev.map((pl, i) => (i === idx ? { ...pl, max_active_skus: val } : pl)));
                  }}
                  className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 text-white"
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[11px] mb-1">Max Channels</label>
                <input
                  type="number"
                  value={p.max_connected_channels}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setPlans((prev) => prev.map((pl, i) => (i === idx ? { ...pl, max_connected_channels: val } : pl)));
                  }}
                  className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 text-white"
                />
              </div>

              <div>
                <label className="block text-slate-400 text-[11px] mb-1">Monthly AI Credits</label>
                <input
                  type="number"
                  value={p.ai_generation_monthly_quota}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setPlans((prev) => prev.map((pl, i) => (i === idx ? { ...pl, ai_generation_monthly_quota: val } : pl)));
                  }}
                  className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 text-white"
                />
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-md cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <Save className="w-4 h-4" /> {isSaving ? 'Saving...' : 'Save Quota Rules'}
          </button>
        </div>
      </form>
    </div>
  );
};
