import React from 'react';
import { Network, CheckCircle2, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';

export const AdminIntegrationsPage: React.FC = () => {
  const connectors = [
    {
      name: 'Shopify Admin API',
      version: '2024-10 (Current Stable)',
      protocol: 'GraphQL',
      totalTenants: 124,
      status: 'Optimal (No Deprecations)',
      errorRate: '0.02%',
    },
    {
      name: 'Meta Graph API',
      version: 'v20.0',
      protocol: 'REST / Media Containers',
      totalTenants: 98,
      status: 'App Review Pending for Content Publish',
      errorRate: '0.14%',
    },
    {
      name: 'Razorpay Subscriptions',
      version: 'v1 Subscriptions API',
      protocol: 'Webhooks HMAC SHA256',
      totalTenants: 142,
      status: 'Operational',
      errorRate: '0.00%',
    },
    {
      name: 'Google Gemini Provider Adapter',
      version: 'gemini-3.8-flash',
      protocol: 'Server-Side GenAI SDK',
      totalTenants: 142,
      status: 'Operational (Anti-Hallucination Active)',
      errorRate: '0.01%',
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl font-mono text-xs">
      <div className="pb-4 border-b border-slate-800">
        <span className="text-xs font-bold uppercase tracking-wider text-rose-400">Connector Health</span>
        <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5 font-sans">
          Third-Party Connectors & API Versions
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {connectors.map((c) => (
          <div key={c.name} className="p-6 rounded-3xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm font-sans">{c.name}</span>
              <span className="text-[10px] text-emerald-400 bg-emerald-950 border border-emerald-800 px-2 py-0.5 rounded">
                Active
              </span>
            </div>
            <div className="space-y-1 text-slate-400">
              <div>Version: <span className="text-slate-200">{c.version}</span></div>
              <div>Protocol: <span className="text-slate-200">{c.protocol}</span></div>
              <div>Connected Tenants: <span className="text-slate-200 font-bold">{c.totalTenants}</span></div>
              <div>Status: <span className="text-slate-300">{c.status}</span></div>
              <div>Error Rate: <span className="text-emerald-400 font-bold">{c.errorRate}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

