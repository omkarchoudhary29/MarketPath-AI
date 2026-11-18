import React, { useEffect, useState } from 'react';
import { Building2, Search, Sliders, ShieldCheck, AlertTriangle, RefreshCw, Power } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';

interface OrgItem {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  plan_name?: string;
  subscription_status?: string;
  products_count: number;
  channels_count: number;
  members_count: number;
  created_at: string;
}

export const AdminOrgsPage: React.FC = () => {
  const { session } = useAuth();
  const { addToast } = useApp();
  const token = session?.access_token;

  const [orgs, setOrgs] = useState<OrgItem[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchOrgs = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await apiClient<OrgItem[]>('/api/v1/admin/organizations', { token });
      setOrgs(data);
    } catch (err: any) {
      console.error('Failed to load organizations:', err);
      addToast({
        type: 'error',
        title: 'Failed to Load Tenants',
        message: err.message || 'Could not query organization registry.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, [token]);

  const handleToggleStatus = async (org: OrgItem) => {
    if (!token) return;
    const newStatus = !org.is_active;
    const actionLabel = newStatus ? 'Reactivated' : 'Suspended';
    setUpdatingId(org.id);
    try {
      await apiClient(`/api/v1/admin/organizations/${org.id}/status`, {
        method: 'PATCH',
        token,
        body: JSON.stringify({
          is_active: newStatus,
          reason: `Operator manual ${actionLabel.toLowerCase()} action via Admin Console`,
        }),
      });

      setOrgs((prev) =>
        prev.map((o) => (o.id === org.id ? { ...o, is_active: newStatus } : o))
      );

      addToast({
        type: newStatus ? 'success' : 'warning',
        title: `Tenant ${actionLabel}`,
        message: `Organization "${org.name}" has been ${actionLabel.toLowerCase()}.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Action Failed',
        message: err.message || `Failed to update tenant status.`,
      });
    } finally {
      setUpdatingId(null);
    }
  };

  const filtered = orgs.filter(
    (o) =>
      o.name.toLowerCase().includes(search.toLowerCase()) ||
      o.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-rose-400">
            Tenant Management
          </span>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
            Seller Organizations & Tenant Standing
          </h1>
        </div>
        <button
          onClick={fetchOrgs}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search organizations by name or slug..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-800 bg-slate-900 text-white focus:outline-none focus:ring-1 focus:ring-rose-500 font-mono"
          />
        </div>
      </div>

      <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden font-mono text-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="py-3 px-5">Organization</th>
                <th className="py-3 px-4">Plan Tier</th>
                <th className="py-3 px-4">Active SKUs</th>
                <th className="py-3 px-4">Channels</th>
                <th className="py-3 px-4">Members</th>
                <th className="py-3 px-4">Standing</th>
                <th className="py-3 px-5 text-right">Administrative Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-rose-500" />
                    Loading tenants from database...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No organizations match the filter criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((org) => (
                  <tr key={org.id} className="hover:bg-slate-900/60">
                    <td className="py-3.5 px-5">
                      <div className="font-bold text-white">{org.name}</div>
                      <div className="text-[10px] text-slate-500">{org.slug}</div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 border border-slate-800 text-slate-200">
                        {org.plan_name || 'Growth'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-emerald-400 font-bold">{org.products_count}</td>
                    <td className="py-3.5 px-4 text-sky-400">{org.channels_count} Live</td>
                    <td className="py-3.5 px-4 text-slate-400">{org.members_count}</td>
                    <td className="py-3.5 px-4">
                      {org.is_active ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800">
                          <AlertTriangle className="w-3 h-3" />
                          Suspended
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      <button
                        onClick={() => handleToggleStatus(org)}
                        disabled={updatingId === org.id}
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded text-[11px] font-medium border transition-colors cursor-pointer ${
                          org.is_active
                            ? 'bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border-rose-800/60'
                            : 'bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border-emerald-800/60'
                        }`}
                      >
                        <Power className="w-3 h-3" />
                        {updatingId === org.id ? 'Updating...' : org.is_active ? 'Suspend Tenant' : 'Reactivate'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
