import React, { useEffect, useState } from 'react';
import { AlertOctagon, RefreshCw, CheckCircle2, RotateCcw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';

interface AdminJob {
  id: string;
  organization_id: string;
  organization_name: string;
  product_title: string;
  channel_type: string;
  job_type: string;
  status: string;
  retry_count: number;
  created_at: string;
  completed_at?: string;
}

export const AdminJobsPage: React.FC = () => {
  const { session } = useAuth();
  const { addToast } = useApp();
  const token = session?.access_token;

  const [jobs, setJobs] = useState<AdminJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  const fetchJobs = () => {
    if (!token) return;
    setIsLoading(true);
    const query = filter !== 'all' ? `?status=${filter}` : '';
    apiClient<AdminJob[]>(`/api/v1/admin/jobs${query}`, { token })
      .then((data) => setJobs(data))
      .catch((err) => console.error('Failed to load admin jobs:', err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchJobs();
  }, [token, filter]);

  const handleRetry = async (jobId: string) => {
    if (!token) return;
    try {
      await apiClient(`/api/v1/admin/jobs/${jobId}/retry`, {
        method: 'POST',
        token,
      });

      setJobs((prev) =>
        prev.map((j) => (j.id === jobId ? { ...j, status: 'queued', retry_count: j.retry_count + 1 } : j))
      );
      addToast({
        type: 'success',
        title: 'Task Re-queued',
        message: `Job ${jobId.slice(0, 8)} reset to queued status for worker execution.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Retry Failed',
        message: err.message || 'Could not retry publishing job.',
      });
    }
  };

  return (
    <div className="space-y-6 max-w-6xl font-mono text-xs">
      <div className="pb-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-rose-400">Queue Telemetry</span>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5 font-sans">
            Central Job Queue & Publishing Triage
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Monitor asynchronous omnichannel publishing tasks and retry failed jobs across tenants.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-bold"
          >
            <option value="all">All Jobs</option>
            <option value="failed">Failed Only</option>
            <option value="queued">Queued</option>
            <option value="completed">Completed</option>
          </select>
          <button onClick={fetchJobs} className="p-2 text-slate-400 hover:text-white rounded-lg">
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden">
        {jobs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No publishing queue jobs match the current filter.
          </div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="py-3 px-4">Organization</th>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4">Channel</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Retries</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {jobs.map((j) => (
                <tr key={j.id} className="hover:bg-slate-900/50">
                  <td className="py-3 px-4 font-bold text-white font-sans">{j.organization_name}</td>
                  <td className="py-3 px-4 text-slate-300">{j.product_title}</td>
                  <td className="py-3 px-4 uppercase font-bold text-sky-400">{j.channel_type}</td>
                  <td className="py-3 px-4 text-slate-400">{j.job_type}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        j.status === 'completed'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : j.status === 'failed'
                          ? 'bg-rose-950 text-rose-400 border border-rose-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}
                    >
                      {j.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400">{j.retry_count}</td>
                  <td className="py-3 px-4 text-right">
                    {j.status === 'failed' && (
                      <button
                        onClick={() => handleRetry(j.id)}
                        className="px-2.5 py-1 rounded bg-rose-950 text-rose-300 border border-rose-800 hover:bg-rose-900 cursor-pointer inline-flex items-center gap-1"
                      >
                        <RotateCcw className="w-3 h-3" /> Re-queue
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
