import React from 'react';
import { FileText, ShieldAlert, Download } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const AdminAuditLogsPage: React.FC = () => {
  const { addToast } = useApp();

  const logs = [
    {
      id: 'aud_881',
      actor: 'ananya@auraterra.in (Owner)',
      org: 'Aura Terra Living',
      action: 'CAMPAIGN_BUDGET_APPROVED',
      resource: 'camp_001 (Monsoon Chai Ritual)',
      ip: '49.36.12.89 (Pune, IN)',
      time: 'Today 18:30 IST',
    },
    {
      id: 'aud_880',
      actor: 'SYSTEM_WORKER_04',
      org: 'Aura Terra Living',
      action: 'PRODUCT_PUBLISHED_REMOTE',
      resource: 'ATL-CER-MUG-01 -> Shopify',
      ip: 'Internal Worker VPC',
      time: 'Today 18:30 IST',
    },
    {
      id: 'aud_879',
      actor: 'rohan.ops@marketpath.ai (Admin)',
      org: 'System Console',
      action: 'QUOTA_OVERRIDE_GRANTED',
      resource: 'org_01 (+50 SKUs)',
      ip: '103.21.58.12 (Mumbai, IN)',
      time: 'Today 15:10 IST',
    },
    {
      id: 'aud_878',
      actor: 'deepak@khurjapottery.in (Admin)',
      org: 'Khurja Pottery Co.',
      action: 'OAUTH_TOKEN_ROTATED',
      resource: 'Shopify Admin GraphQL',
      ip: '122.161.42.10 (Delhi, IN)',
      time: 'Yesterday 21:15 IST',
    },
  ];

  const handleExport = () => {
    addToast({
      type: 'info',
      title: 'Global Audit Trail Exported',
      message: 'Downloaded tamper-evident cryptographic log archive.',
    });
  };

  return (
    <div className="space-y-6 max-w-6xl font-mono text-xs">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-rose-400">Security Governance</span>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5 font-sans">
            Global Administrative Audit Log
          </h1>
          <p className="text-slate-400 text-[11px] mt-1">
            Immutable, append-only record of administrative, authentication, and publishing actions.
          </p>
        </div>

        <button
          onClick={handleExport}
          className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-slate-700 cursor-pointer flex items-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5" /> Export Log Archive
        </button>
      </div>

      <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
            <tr>
              <th className="py-3 px-5">Event ID & Actor</th>
              <th className="py-3 px-4">Organization</th>
              <th className="py-3 px-4">Action</th>
              <th className="py-3 px-4">Target Resource</th>
              <th className="py-3 px-4">IP Address</th>
              <th className="py-3 px-5 text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-[11px]">
            {logs.map((l) => (
              <tr key={l.id} className="hover:bg-slate-900/60">
                <td className="py-3.5 px-5">
                  <span className="font-bold text-white block">{l.actor}</span>
                  <span className="text-slate-500 text-[10px]">{l.id}</span>
                </td>
                <td className="py-3.5 px-4 text-slate-300">{l.org}</td>
                <td className="py-3.5 px-4 text-rose-300 font-bold">{l.action}</td>
                <td className="py-3.5 px-4 text-slate-400">{l.resource}</td>
                <td className="py-3.5 px-4 text-slate-500">{l.ip}</td>
                <td className="py-3.5 px-5 text-right text-slate-400">{l.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

