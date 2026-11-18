import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import {
  Package,
  Wand2,
  Send,
  Plus,
  ArrowRight,
  TrendingUp,
  Link2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ShoppingBag,
  HelpCircle,
  BarChart3,
  Calendar,
  Compass,
  ArrowUpRight,
  Check,
  AlertCircle,
  ShieldCheck,
  Store,
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  const { brand, products, channels, publishingJobs, isDemoMode } = useApp();
  const { user, activeOrg } = useAuth();

  const [dateRange, setDateRange] = useState<'today' | '7d' | '30d' | 'quarter'>('30d');
  const [showSkuInfo, setShowSkuInfo] = useState<boolean>(false);

  const firstName = user?.full_name?.split(' ')[0] || 'Brand Owner';
  const orgName = activeOrg?.name || brand.name;

  // Real operational counts
  const totalProducts = products.length;
  const connectedChannels = channels.filter((c) => c.status === 'connected');
  const publishedJobs = publishingJobs.filter((j) => j.status === 'published');
  const actionRequiredJobs = publishingJobs.filter((j) => j.status === 'action_required' || j.status === 'failed');

  // Operational items needing attention
  const needsAttentionItems = [
    ...(actionRequiredJobs.length > 0
      ? [
          {
            id: 'job-issues',
            title: `${actionRequiredJobs.length} Channel Publishing Issue${actionRequiredJobs.length > 1 ? 's' : ''}`,
            desc: 'Listings require category attributes or validation review.',
            actionLabel: 'Review Listings',
            to: '/app/publishing',
            severity: 'warning' as const,
          },
        ]
      : []),
    ...(totalProducts === 0
      ? [
          {
            id: 'no-prods',
            title: 'Catalogue is empty',
            desc: 'Add your first master SKU to start adapting content across channels.',
            actionLabel: 'Add Product',
            to: '/app/products?create=true',
            severity: 'info' as const,
          },
        ]
      : []),
    ...(connectedChannels.length === 0
      ? [
          {
            id: 'no-channels',
            title: 'No sales channels connected',
            desc: 'Connect your Shopify store or marketplaces to sync listings and orders.',
            actionLabel: 'Connect Store',
            to: '/app/integrations',
            severity: 'warning' as const,
          },
        ]
      : []),
    {
      id: 'brand-check',
      title: 'Brand Intelligence Tone Active',
      desc: `Content Studio calibrated for ${orgName} communication style.`,
      actionLabel: 'View Guidelines',
      to: '/app/brand',
      severity: 'success' as const,
    },
  ];

  return (
    <div className="space-y-8">
      {/* 01. Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-bordergrey">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-forest bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
              Owner Overview
            </span>
            {isDemoMode && (
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-softorange bg-softorange/10 px-2.5 py-0.5 rounded-full border border-softorange/30">
                Demo Workspace
              </span>
            )}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-2">
            Welcome back, {firstName}
          </h1>
          <p className="text-xs sm:text-sm text-charcoal-muted mt-1">
            Operating workspace for <strong className="text-charcoal font-bold">{orgName}</strong> • Master catalogue adapted across connected channels.
          </p>
        </div>

        {/* Date Selector & Primary Action */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center bg-purewhite border border-bordergrey rounded-xl p-1 shadow-xs text-xs font-semibold text-charcoal-muted">
            <button
              onClick={() => setDateRange('today')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                dateRange === 'today' ? 'bg-softbeige text-forest font-bold shadow-xs' : 'hover:text-charcoal'
              }`}
            >
              Today
            </button>
            <button
              onClick={() => setDateRange('7d')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                dateRange === '7d' ? 'bg-softbeige text-forest font-bold shadow-xs' : 'hover:text-charcoal'
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setDateRange('30d')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                dateRange === '30d' ? 'bg-softbeige text-forest font-bold shadow-xs' : 'hover:text-charcoal'
              }`}
            >
              30 Days
            </button>
            <button
              onClick={() => setDateRange('quarter')}
              className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                dateRange === 'quarter' ? 'bg-softbeige text-forest font-bold shadow-xs' : 'hover:text-charcoal'
              }`}
            >
              This Quarter
            </button>
          </div>

          <Link
            to="/app/products?create=true"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white font-bold text-xs shadow-option-c transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Add Product</span>
          </Link>

          <div className="relative">
            <button
              type="button"
              onClick={() => setShowSkuInfo(!showSkuInfo)}
              className="p-2 text-charcoal-muted hover:text-charcoal rounded-xl border border-bordergrey hover:bg-softbeige/50 transition-colors cursor-pointer"
              title="Catalogue hierarchy help"
            >
              <HelpCircle className="w-4 h-4" />
            </button>

            {showSkuInfo && (
              <div className="absolute right-0 mt-2 w-72 p-4 bg-white rounded-2xl shadow-option-c-lg border border-bordergrey z-30 text-xs space-y-2.5 animate-in fade-in">
                <div className="flex items-center justify-between border-b border-bordergrey pb-2">
                  <span className="font-bold text-charcoal">Catalogue Hierarchy</span>
                  <button onClick={() => setShowSkuInfo(false)} className="text-charcoal-muted hover:text-charcoal text-[11px] cursor-pointer">
                    ✕
                  </button>
                </div>
                <div className="space-y-1.5 text-charcoal-muted text-[11px] leading-relaxed">
                  <p><strong className="text-charcoal">Product:</strong> The parent item (e.g. Handcrafted Ceramic Mug).</p>
                  <p><strong className="text-charcoal">Variant:</strong> Option set (e.g. Terracotta Clay / 350ml).</p>
                  <p><strong className="text-charcoal">SKU:</strong> Master tracking code for inventory and channel syncing.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 02. KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Products */}
        <Card className="p-4 sm:p-5 hover:border-brand-300 transition-colors">
          <div className="flex items-center justify-between text-charcoal-muted">
            <span className="text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">Master Products</span>
            <Package className="w-4 h-4 text-brand-600" />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-charcoal">{totalProducts}</span>
            <span className="text-[10px] text-forest font-semibold bg-softbeige px-2 py-0.5 rounded-full">
              {totalProducts > 0 ? 'In Catalogue' : 'Empty'}
            </span>
          </div>
          <Link to="/app/products" className="text-[11px] text-brand-600 hover:underline font-semibold mt-1 block">
            Manage catalogue →
          </Link>
        </Card>

        {/* Published Listings */}
        <Card className="p-4 sm:p-5 hover:border-brand-300 transition-colors">
          <div className="flex items-center justify-between text-charcoal-muted">
            <span className="text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">Published Listings</span>
            <Send className="w-4 h-4 text-emerald" />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-charcoal">
              {isDemoMode ? publishedJobs.length : 0}
            </span>
            <span className="text-[10px] text-emerald font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              Live
            </span>
          </div>
          <Link to="/app/publishing" className="text-[11px] text-brand-600 hover:underline font-semibold mt-1 block">
            Listings & performance →
          </Link>
        </Card>

        {/* Connected Channels */}
        <Card className="p-4 sm:p-5 hover:border-brand-300 transition-colors">
          <div className="flex items-center justify-between text-charcoal-muted">
            <span className="text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">Sales Channels</span>
            <Link2 className="w-4 h-4 text-forest" />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-charcoal">{connectedChannels.length}</span>
            <span className="text-[10px] text-forest font-semibold bg-softbeige px-2 py-0.5 rounded-full">
              {connectedChannels.length > 0 ? 'Active' : 'Not Connected'}
            </span>
          </div>
          <Link to="/app/integrations" className="text-[11px] text-brand-600 hover:underline font-semibold mt-1 block">
            Manage integrations →
          </Link>
        </Card>

        {/* Orders */}
        <Card className="p-4 sm:p-5 hover:border-brand-300 transition-colors">
          <div className="flex items-center justify-between text-charcoal-muted">
            <span className="text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">Orders</span>
            <ShoppingBag className="w-4 h-4 text-softorange" />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-charcoal">
              {isDemoMode ? '14' : '0'}
            </span>
            <span className="text-[10px] text-charcoal-muted font-semibold bg-warmwhite px-2 py-0.5 rounded-full border border-bordergrey">
              {dateRange.toUpperCase()}
            </span>
          </div>
          <Link to="/app/orders" className="text-[11px] text-brand-600 hover:underline font-semibold mt-1 block">
            Orders & inventory →
          </Link>
        </Card>

        {/* Revenue */}
        <Card className="p-4 sm:p-5 hover:border-brand-300 transition-colors">
          <div className="flex items-center justify-between text-charcoal-muted">
            <span className="text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">Revenue</span>
            <TrendingUp className="w-4 h-4 text-forest" />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-charcoal">
              {isDemoMode ? '₹1,48,200' : '₹0'}
            </span>
            {isDemoMode && (
              <span className="text-[10px] text-emerald font-bold flex items-center">
                +18%
              </span>
            )}
          </div>
          <span className="text-[11px] text-charcoal-muted mt-1 block truncate">
            {isDemoMode ? 'Sample verified store data' : 'Awaiting channel connection'}
          </span>
        </Card>
      </div>

      {/* 03. Sales Performance & Channel Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sales Performance Time-Series */}
        <Card className="lg:col-span-2 p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-bordergrey">
            <div>
              <h2 className="text-base font-bold text-charcoal">Sales & Channel Velocity</h2>
              <p className="text-xs text-charcoal-muted">Consolidated order volume across connected sales channels</p>
            </div>
            <Link
              to="/app/analytics"
              className="text-xs font-bold text-brand-600 hover:text-forest hover:underline flex items-center gap-1"
            >
              Growth Analytics <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {isDemoMode ? (
            /* Visual time-series graph for verified demo mode */
            <div className="space-y-4 pt-2">
              <div className="h-48 w-full flex items-end justify-between gap-2 pt-6 px-2">
                {[
                  { day: 'Day 1', val: 35, amt: '₹14k' },
                  { day: 'Day 5', val: 52, amt: '₹22k' },
                  { day: 'Day 10', val: 40, amt: '₹18k' },
                  { day: 'Day 15', val: 68, amt: '₹31k' },
                  { day: 'Day 20', val: 85, amt: '₹42k' },
                  { day: 'Day 25', val: 74, amt: '₹36k' },
                  { day: 'Day 30', val: 92, amt: '₹49k' },
                ].map((pt, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 group">
                    <div className="text-[10px] font-bold text-charcoal-muted opacity-0 group-hover:opacity-100 transition-opacity">
                      {pt.amt}
                    </div>
                    <div className="w-full max-w-[36px] bg-softbeige rounded-t-xl group-hover:bg-brand-500 transition-all flex flex-col justify-end" style={{ height: `${pt.val}%` }}>
                      <div className="w-full bg-forest rounded-t-xl" style={{ height: '70%' }}></div>
                    </div>
                    <span className="text-[10px] text-charcoal-muted">{pt.day}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between text-xs text-charcoal-muted pt-2 border-t border-bordergrey">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-forest inline-block"></span>
                  Shopify Direct Store
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-softbeige-dark inline-block"></span>
                  Marketplaces Pending Sync
                </span>
              </div>
            </div>
          ) : (
            /* Clean, honest empty state for live workspace */
            <div className="p-10 text-center space-y-3 bg-warmwhite rounded-2xl border border-dashed border-bordergrey">
              <div className="w-12 h-12 rounded-2xl bg-softbeige text-forest flex items-center justify-center mx-auto">
                <BarChart3 className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-charcoal">No Live Sales Data Recorded</h3>
              <p className="text-xs text-charcoal-muted max-w-md mx-auto leading-relaxed">
                Connect your Shopify or marketplace accounts in Connected Channels and publish products to automatically ingest real-time order volume.
              </p>
              <div className="pt-2">
                <Link
                  to="/app/integrations"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold transition-all shadow-xs"
                >
                  <Link2 className="w-3.5 h-3.5" />
                  Connect Sales Channel
                </Link>
              </div>
            </div>
          )}
        </Card>

        {/* Channel Health Card */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-bordergrey">
            <div>
              <h2 className="text-base font-bold text-charcoal">Channel Health</h2>
              <p className="text-xs text-charcoal-muted">Integration and sync status</p>
            </div>
            <Link to="/app/integrations" className="text-xs font-bold text-brand-600 hover:underline">
              All Channels →
            </Link>
          </div>

          <div className="space-y-3">
            {channels.slice(0, 3).map((chan) => (
              <div key={chan.id} className="p-3.5 rounded-xl border border-bordergrey bg-warmwhite space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-charcoal flex items-center gap-1.5">
                    <Store className="w-3.5 h-3.5 text-forest" />
                    {chan.name}
                  </span>
                  <Badge variant={chan.status === 'connected' ? 'success' : 'warning'} size="sm">
                    {chan.status}
                  </Badge>
                </div>
                <div className="text-[11px] text-charcoal-muted truncate">{chan.identifier}</div>
                {chan.lastSyncAt && (
                  <div className="text-[10px] text-charcoal-muted pt-1 border-t border-bordergrey flex items-center justify-between">
                    <span>Sync Health: OK</span>
                    <span>{chan.lastSyncAt}</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          <Link
            to="/app/integrations"
            className="block w-full py-2.5 text-center text-xs font-bold text-charcoal bg-softbeige hover:bg-softbeige-dark rounded-xl transition-colors border border-bordergrey"
          >
            + Connect New Channel
          </Link>
        </Card>
      </div>

      {/* 04. Needs Attention & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Needs Attention */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-bordergrey">
            <div>
              <h2 className="text-base font-bold text-charcoal flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-softorange" />
                Needs Attention
              </h2>
              <p className="text-xs text-charcoal-muted">Real operational tasks and publishing blockers</p>
            </div>
            <span className="text-[10px] font-bold text-forest bg-softbeige px-2.5 py-0.5 rounded-full border border-bordergrey">
              {needsAttentionItems.length} Items
            </span>
          </div>

          <div className="space-y-3">
            {needsAttentionItems.map((item) => (
              <div
                key={item.id}
                className="p-3.5 rounded-2xl border border-bordergrey bg-warmwhite flex items-start justify-between gap-3 hover:border-brand-300 transition-colors"
              >
                <div className="space-y-0.5">
                  <h4 className="text-xs font-bold text-charcoal">{item.title}</h4>
                  <p className="text-[11px] text-charcoal-muted leading-relaxed">{item.desc}</p>
                </div>
                <Link
                  to={item.to}
                  className="shrink-0 px-3 py-1.5 rounded-xl bg-white hover:bg-softbeige text-charcoal text-xs font-bold border border-bordergrey transition-colors"
                >
                  {item.actionLabel}
                </Link>
              </div>
            ))}
          </div>
        </Card>

        {/* Recent Activity */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-bordergrey">
            <div>
              <h2 className="text-base font-bold text-charcoal flex items-center gap-2">
                <Clock className="w-4 h-4 text-forest" />
                Recent Operations
              </h2>
              <p className="text-xs text-charcoal-muted">Product catalogue and publishing audit trail</p>
            </div>
            <Link to="/app/publishing" className="text-xs font-bold text-brand-600 hover:underline">
              Publishing Queue →
            </Link>
          </div>

          <div className="space-y-3">
            {publishingJobs.slice(0, 4).map((job) => (
              <div key={job.id} className="p-3 rounded-xl border border-bordergrey bg-warmwhite flex items-center justify-between text-xs">
                <div className="min-w-0 pr-3">
                  <span className="font-bold text-charcoal block truncate">{job.productTitle}</span>
                  <span className="text-[11px] text-charcoal-muted block truncate">
                    SKU: {job.productSku} • {job.channelType.toUpperCase()}
                  </span>
                </div>
                <Badge variant={job.status === 'published' ? 'success' : job.status === 'action_required' ? 'warning' : 'neutral'} size="sm">
                  {job.status === 'published' ? 'Live' : job.status}
                </Badge>
              </div>
            ))}
            {publishingJobs.length === 0 && (
              <div className="p-6 text-center text-xs text-charcoal-muted">
                No recent activity logged. Add your first product to begin.
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* 05. Quick Actions Grid */}
      <Card className="p-6">
        <h2 className="text-base font-bold text-charcoal mb-1">Quick Operational Actions</h2>
        <p className="text-xs text-charcoal-muted mb-4">Direct paths to daily commerce workflows</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <Link
            to="/app/products?create=true"
            className="p-3.5 rounded-2xl border border-bordergrey bg-warmwhite hover:bg-softbeige/50 hover:border-brand-300 transition-all flex flex-col items-center text-center gap-2 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Plus className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-charcoal">Add Product</span>
            <span className="text-[10px] text-charcoal-muted">Master catalogue</span>
          </Link>

          <Link
            to="/app/integrations"
            className="p-3.5 rounded-2xl border border-bordergrey bg-warmwhite hover:bg-softbeige/50 hover:border-brand-300 transition-all flex flex-col items-center text-center gap-2 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-brand-50 text-forest flex items-center justify-center group-hover:scale-105 transition-transform">
              <Link2 className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-charcoal">Connect Channel</span>
            <span className="text-[10px] text-charcoal-muted">Shopify & Marketplaces</span>
          </Link>

          <Link
            to="/app/ai-studio"
            className="p-3.5 rounded-2xl border border-bordergrey bg-warmwhite hover:bg-softbeige/50 hover:border-brand-300 transition-all flex flex-col items-center text-center gap-2 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-amberbrand-50 text-softorange flex items-center justify-center group-hover:scale-105 transition-transform">
              <Wand2 className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-charcoal">Create Content</span>
            <span className="text-[10px] text-charcoal-muted">Listing & Ad copy</span>
          </Link>

          <Link
            to="/app/orders"
            className="p-3.5 rounded-2xl border border-bordergrey bg-warmwhite hover:bg-softbeige/50 hover:border-brand-300 transition-all flex flex-col items-center text-center gap-2 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald flex items-center justify-center group-hover:scale-105 transition-transform">
              <ShoppingBag className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-charcoal">View Orders</span>
            <span className="text-[10px] text-charcoal-muted">Unified inventory</span>
          </Link>

          <Link
            to="/app/analytics"
            className="p-3.5 rounded-2xl border border-bordergrey bg-warmwhite hover:bg-softbeige/50 hover:border-brand-300 transition-all flex flex-col items-center text-center gap-2 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center group-hover:scale-105 transition-transform">
              <BarChart3 className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-charcoal">Growth Analytics</span>
            <span className="text-[10px] text-charcoal-muted">Sales & channels</span>
          </Link>
        </div>
      </Card>
    </div>
  );
};
