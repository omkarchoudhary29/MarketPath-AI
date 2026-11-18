import React, { useEffect, useState } from 'react';
import {
  Building,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  Search,
  CheckCircle2,
  XCircle,
  Star,
  ExternalLink,
  Power,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';

interface AdminAgencyItem {
  id: string;
  name: string;
  slug: string;
  city: string;
  state: string;
  min_budget_inr: number;
  verification_status: string;
  gst_number?: string;
  is_active: boolean;
  is_featured: boolean;
  is_demo: boolean;
  rating_avg: number;
  reviews_count: number;
  created_at: string;
}

export const AdminAgenciesPage: React.FC = () => {
  const { session } = useAuth();
  const { addToast } = useApp();
  const token = session?.access_token;

  const [agencies, setAgencies] = useState<AdminAgencyItem[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchAgencies = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await apiClient<AdminAgencyItem[]>('/api/v1/admin/agencies', { token });
      setAgencies(data);
    } catch (err: any) {
      console.error('Failed to load agencies for admin:', err);
      addToast({
        type: 'error',
        title: 'Failed to Query Agencies',
        message: err.message || 'Could not fetch platform agency directory.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAgencies();
  }, [token]);

  const handleUpdateStatus = async (
    agencyId: string,
    newStatus: string,
    notes?: string
  ) => {
    if (!token) return;
    setUpdatingId(agencyId);
    try {
      await apiClient(`/api/v1/admin/agencies/${agencyId}/verification`, {
        method: 'PATCH',
        token,
        body: JSON.stringify({
          verification_status: newStatus,
          verification_notes: notes || `Admin updated standing to ${newStatus}`,
        }),
      });

      setAgencies((prev) =>
        prev.map((a) => (a.id === agencyId ? { ...a, verification_status: newStatus } : a))
      );

      addToast({
        type: 'success',
        title: 'Verification Standing Updated',
        message: `Agency status changed to ${newStatus.toUpperCase()}.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Update Failed',
        message: err.message || 'Unable to update verification status.',
      });
    } finally {
      setUpdatingId(null);
    }
  };

  const handleToggleFeatured = async (agency: AdminAgencyItem) => {
    if (!token) return;
    setUpdatingId(agency.id);
    const newFeatured = !agency.is_featured;
    try {
      await apiClient(`/api/v1/admin/agencies/${agency.id}/verification`, {
        method: 'PATCH',
        token,
        body: JSON.stringify({
          verification_status: agency.verification_status,
          is_featured: newFeatured,
        }),
      });

      setAgencies((prev) =>
        prev.map((a) => (a.id === agency.id ? { ...a, is_featured: newFeatured } : a))
      );

      addToast({
        type: 'info',
        title: 'Placement Toggled',
        message: `Featured placement for "${agency.name}" is now ${newFeatured ? 'ENABLED' : 'DISABLED'}.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Toggle Failed',
        message: err.message || 'Could not update featured standing.',
      });
    } finally {
      setUpdatingId(null);
    }
  };

  const filtered = agencies.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.city.toLowerCase().includes(search.toLowerCase()) ||
      a.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-rose-400">
            Marketplace Verification Queue
          </span>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
            Agency Connect Partner Directory & Verification
          </h1>
        </div>
        <button
          onClick={fetchAgencies}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 transition-colors cursor-pointer"
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
            placeholder="Search agencies by name, city, or slug..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-800 bg-slate-900 text-white focus:outline-none focus:ring-1 focus:ring-rose-500 font-mono"
          />
        </div>
      </div>

      <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden font-mono text-xs">
        <table className="w-full text-left">
          <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
            <tr>
              <th className="py-3 px-5">Agency & City</th>
              <th className="py-3 px-4">Starting Retainer</th>
              <th className="py-3 px-4">GST Number</th>
              <th className="py-3 px-4">Verification Standing</th>
              <th className="py-3 px-4">Featured</th>
              <th className="py-3 px-5 text-right">Moderation Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-rose-500" />
                  Loading agencies from database...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  No agencies match the query criteria.
                </td>
              </tr>
            ) : (
              filtered.map((agency) => {
                const isVerified = agency.verification_status === 'verified';
                const isSuspended = agency.verification_status === 'suspended';

                return (
                  <tr key={agency.id} className="hover:bg-slate-900/60">
                    <td className="py-3.5 px-5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white block">{agency.name}</span>
                        {agency.is_demo && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] bg-slate-800 text-slate-400 border border-slate-700">
                            DEMO
                          </span>
                        )}
                      </div>
                      <span className="text-slate-400 text-[11px]">
                        {agency.city}, {agency.state}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-200">
                      ₹{agency.min_budget_inr.toLocaleString('en-IN')}/mo
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {agency.gst_number || 'Pending'}
                    </td>
                    <td className="py-3.5 px-4">
                      {isVerified ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                          <ShieldCheck className="w-3 h-3" />
                          VERIFIED
                        </span>
                      ) : isSuspended ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800">
                          <AlertTriangle className="w-3 h-3" />
                          SUSPENDED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-950 text-amber-400 border border-amber-800">
                          REGISTERED
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <button
                        onClick={() => handleToggleFeatured(agency)}
                        disabled={updatingId === agency.id}
                        className={`px-2 py-0.5 rounded text-[10px] font-medium border cursor-pointer ${
                          agency.is_featured
                            ? 'bg-amber-950 text-amber-300 border-amber-800'
                            : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
                        }`}
                      >
                        {agency.is_featured ? 'FEATURED' : 'Standard'}
                      </button>
                    </td>
                    <td className="py-3.5 px-5 text-right space-x-1.5">
                      {!isVerified && (
                        <button
                          onClick={() => handleUpdateStatus(agency.id, 'verified')}
                          disabled={updatingId === agency.id}
                          className="px-2.5 py-1 rounded bg-emerald-950/60 hover:bg-emerald-900 text-emerald-300 border border-emerald-800 text-[11px] cursor-pointer"
                        >
                          Approve & Verify
                        </button>
                      )}
                      {!isSuspended && (
                        <button
                          onClick={() => handleUpdateStatus(agency.id, 'suspended')}
                          disabled={updatingId === agency.id}
                          className="px-2.5 py-1 rounded bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800 text-[11px] cursor-pointer"
                        >
                          Suspend
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

