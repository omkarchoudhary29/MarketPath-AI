import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import {
  Link2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Trash2,
  HelpCircle,
  X,
  ShoppingBag,
  Store,
  Share2,
  Zap,
  Sparkles,
  Info,
  Lock,
  ArrowRight,
  Check,
} from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export interface BackendIntegrationItem {
  platform: string;
  display_name: string;
  description: string;
  channel_group?: string; // storefronts, marketplaces, social, quick_commerce
  connection_status: string; // Connected, Available, Partner Access Required, Setup Required, Awaiting Authorization, Coming Soon
  partner_status?: string | null;
  is_configured: boolean;
  connection_id?: string | null;
  account_identifier?: string | null;
  account_name?: string | null;
  last_synced_at?: string | null;
  granted_scopes: string[];
  required_env_vars: string[];
  setup_instructions?: string | null;
}

const CHANNEL_GROUPS = [
  { id: 'all', label: 'All Ecosystem', icon: Link2 },
  { id: 'storefronts', label: 'Storefronts', icon: Store },
  { id: 'marketplaces', label: 'Marketplaces', icon: ShoppingBag },
  { id: 'social', label: 'Social Platforms', icon: Share2 },
  { id: 'quick_commerce', label: 'Quick Commerce', icon: Zap },
];

export const IntegrationsPage: React.FC = () => {
  const { session, activeOrg, role } = useAuth();
  const { addToast } = useApp();

  const [activeTab, setActiveTab] = useState<string>('all');
  const [integrations, setIntegrations] = useState<BackendIntegrationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [shopifyShopDomain, setShopifyShopDomain] = useState('');
  const [shopifyModalOpen, setShopifyModalOpen] = useState(false);
  const [wooModalOpen, setWooModalOpen] = useState(false);
  const [wooStoreUrl, setWooStoreUrl] = useState('');
  const [wooKey, setWooKey] = useState('');
  const [wooSecret, setWooSecret] = useState('');

  const [amzModalOpen, setAmzModalOpen] = useState(false);
  const [amzClientId, setAmzClientId] = useState('');
  const [amzClientSecret, setAmzClientSecret] = useState('');
  const [amzRefreshToken, setAmzRefreshToken] = useState('');
  const [amzSellerId, setAmzSellerId] = useState('');

  const [flpModalOpen, setFlpModalOpen] = useState(false);
  const [flpAppId, setFlpAppId] = useState('');
  const [flpAppSecret, setFlpAppSecret] = useState('');

  const [channelDrawerItem, setChannelDrawerItem] = useState<BackendIntegrationItem | null>(null);
  const [disconnectModalItem, setDisconnectModalItem] = useState<BackendIntegrationItem | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchIntegrations = async () => {
    if (!activeOrg?.id || !session?.access_token) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const data = await apiClient<BackendIntegrationItem[]>('/api/v1/integrations', {
        token: session.access_token,
        organizationId: activeOrg.id,
      });
      setIntegrations(data);
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Failed to load integrations',
        message: err.message || 'Unable to fetch connected channels.',
      });
      setIntegrations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, [activeOrg?.id, session?.access_token]);

  const handleStartShopifyOAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shopifyShopDomain.trim()) return;

    try {
      setIsSubmitting(true);
      const res = await apiClient<{ authorization_url: string; state: string }>(
        '/api/v1/integrations/shopify/authorize',
        {
          method: 'POST',
          token: session?.access_token,
          organizationId: activeOrg?.id,
          body: JSON.stringify({ shop_domain: shopifyShopDomain.trim() }),
        }
      );
      addToast({
        type: 'info',
        title: 'Redirecting to Shopify',
        message: 'Opening Shopify Admin authorization dialog...',
      });
      setShopifyModalOpen(false);
      window.open(res.authorization_url, '_blank', 'noopener,noreferrer');
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Shopify Authorization Notice',
        message: err.message || 'Ensure backend OAuth credentials are configured.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConnectWooCommerce = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wooStoreUrl.trim() || !wooKey.trim() || !wooSecret.trim()) return;

    try {
      setIsSubmitting(true);
      await apiClient('/api/v1/integrations/woocommerce/connect', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          store_url: wooStoreUrl.trim(),
          consumer_key: wooKey.trim(),
          consumer_secret: wooSecret.trim(),
        }),
      });
      addToast({
        type: 'success',
        title: 'WooCommerce Connected',
        message: 'WooCommerce store successfully linked with AES-256 encrypted credentials.',
      });
      setWooModalOpen(false);
      setWooStoreUrl('');
      setWooKey('');
      setWooSecret('');
      fetchIntegrations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'WooCommerce Connection Failed',
        message: err.message || 'Unable to connect to WooCommerce store.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConnectAmazon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amzClientId.trim() || !amzClientSecret.trim() || !amzRefreshToken.trim() || !amzSellerId.trim()) return;

    try {
      setIsSubmitting(true);
      await apiClient('/api/v1/integrations/amazon/connect', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          client_id: amzClientId.trim(),
          client_secret: amzClientSecret.trim(),
          refresh_token: amzRefreshToken.trim(),
          seller_id: amzSellerId.trim(),
        }),
      });
      addToast({
        type: 'success',
        title: 'Amazon SP-API Connected',
        message: 'Amazon India Seller account successfully connected.',
      });
      setAmzModalOpen(false);
      setAmzClientId('');
      setAmzClientSecret('');
      setAmzRefreshToken('');
      setAmzSellerId('');
      fetchIntegrations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Amazon Connection Failed',
        message: err.message || 'Unable to verify Amazon SP-API credentials.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConnectFlipkart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flpAppId.trim() || !flpAppSecret.trim()) return;

    try {
      setIsSubmitting(true);
      await apiClient('/api/v1/integrations/flipkart/connect', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          app_id: flpAppId.trim(),
          app_secret: flpAppSecret.trim(),
        }),
      });
      addToast({
        type: 'success',
        title: 'Flipkart Hub Connected',
        message: 'Flipkart Seller Hub credentials verified and connected.',
      });
      setFlpModalOpen(false);
      setFlpAppId('');
      setFlpAppSecret('');
      fetchIntegrations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Flipkart Connection Failed',
        message: err.message || 'Unable to authenticate with Flipkart Seller Hub.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!disconnectModalItem?.connection_id) return;

    try {
      setIsSubmitting(true);
      await apiClient(`/api/v1/integrations/${disconnectModalItem.connection_id}`, {
        method: 'DELETE',
        token: session?.access_token,
        organizationId: activeOrg?.id,
      });
      addToast({
        type: 'info',
        title: 'Channel Disconnected',
        message: `${disconnectModalItem.display_name} was safely disconnected. Master Product Catalogue is preserved 100% intact.`,
      });
      setDisconnectModalItem(null);
      fetchIntegrations();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Disconnection Failed',
        message: err.message || 'Unable to disconnect channel.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredIntegrations = integrations.filter((item) => {
    if (activeTab === 'all') return true;
    return item.channel_group === activeTab;
  });

  return (
    <div className="space-y-8 max-w-6xl">
      {/* 01. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-bordergrey">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-forest bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
            4-Group Channel Ecosystem
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-2">
            Connected Channels
          </h1>
          <p className="text-xs sm:text-sm text-charcoal-muted mt-1">
            Manage your store connections across Storefronts, Marketplaces, Social Platforms, and Quick Commerce.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchIntegrations}
            disabled={loading}
            className="p-2 rounded-xl border border-bordergrey bg-purewhite hover:bg-softbeige text-charcoal-muted transition-colors cursor-pointer"
            title="Refresh status"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <div className="flex items-center gap-2 text-xs font-bold text-forest bg-softbeige border border-bordergrey px-3 py-1.5 rounded-xl">
            <ShieldCheck className="w-4 h-4 text-emerald" />
            <span>AES-256 Vaulted</span>
          </div>
        </div>
      </div>

      {/* 02. Four Directory Group Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-bordergrey text-xs font-bold">
        {CHANNEL_GROUPS.map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeTab === tab.id;
          const count =
            tab.id === 'all'
              ? integrations.length
              : integrations.filter((i) => i.channel_group === tab.id).length;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl border transition-all cursor-pointer whitespace-nowrap ${
                isSelected
                  ? 'bg-softbeige text-forest font-bold border-bordergrey shadow-xs'
                  : 'bg-white text-charcoal-muted hover:text-charcoal border-transparent hover:bg-softbeige/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${isSelected ? 'bg-forest text-white' : 'bg-warmwhite text-charcoal-muted'}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* 03. Channel Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredIntegrations.map((item) => (
          <Card
            key={item.platform}
            className="p-5 flex flex-col justify-between space-y-4 hover:border-brand-300 transition-all"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-2xl flex items-center justify-center font-bold text-xs ${
                      item.connection_status === 'Connected'
                        ? 'bg-emerald-50 text-emerald border border-emerald-200'
                        : item.connection_status === 'Partner Access Required'
                        ? 'bg-softorange/10 text-softorange border border-softorange/30'
                        : 'bg-softbeige text-forest border border-bordergrey'
                    }`}
                  >
                    {item.display_name.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-charcoal">{item.display_name}</h3>
                    <span className="text-[11px] text-charcoal-muted capitalize">
                      {item.channel_group?.replace('_', ' ') || 'Channel'}
                    </span>
                  </div>
                </div>

                {item.connection_status === 'Connected' ? (
                  <Badge variant="success" size="sm" dot>
                    Connected
                  </Badge>
                ) : item.connection_status === 'Partner Access Required' ? (
                  <Badge variant="warning" size="sm">
                    Partner Access
                  </Badge>
                ) : (
                  <Badge variant="neutral" size="sm">
                    {item.connection_status}
                  </Badge>
                )}
              </div>

              <p className="text-xs text-charcoal-muted leading-relaxed">{item.description}</p>

              {item.partner_status && (
                <div className="p-2.5 rounded-xl bg-softorange/10 border border-softorange/20 text-[11px] text-charcoal leading-snug">
                  <strong className="block text-softorange font-bold">Prerequisites:</strong>
                  {item.partner_status}
                </div>
              )}

              {item.account_name && (
                <div className="text-[11px] text-charcoal-muted bg-warmwhite p-2 rounded-xl border border-bordergrey truncate">
                  Account: <strong className="text-charcoal">{item.account_name}</strong>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-bordergrey flex items-center justify-between gap-2">
              <button
                onClick={() => setChannelDrawerItem(item)}
                className="text-xs font-bold text-forest hover:text-brand-600 flex items-center gap-1 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-softorange" />
                <span>Channel Details</span>
              </button>

              <div className="flex items-center gap-2">
                {item.connection_status === 'Connected' ? (
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-emerald flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Healthy
                    </span>
                    {role === 'owner' && item.connection_id && (
                      <button
                        onClick={() => setDisconnectModalItem(item)}
                        className="p-1.5 rounded-lg border border-bordergrey hover:bg-red-50 text-charcoal-muted hover:text-red-600 transition-colors cursor-pointer"
                        title="Disconnect channel"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ) : item.platform === 'shopify' ? (
                  <button
                    onClick={() => setShopifyModalOpen(true)}
                    className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-xs cursor-pointer transition-colors"
                  >
                    Connect
                  </button>
                ) : item.platform === 'woocommerce' ? (
                  <button
                    onClick={() => setWooModalOpen(true)}
                    className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-xs cursor-pointer transition-colors"
                  >
                    Connect
                  </button>
                ) : item.platform === 'amazon' ? (
                  <button
                    onClick={() => setAmzModalOpen(true)}
                    className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-xs cursor-pointer transition-colors"
                  >
                    Connect
                  </button>
                ) : item.platform === 'flipkart' ? (
                  <button
                    onClick={() => setFlpModalOpen(true)}
                    className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-xs cursor-pointer transition-colors"
                  >
                    Connect
                  </button>
                ) : (
                  <button
                    onClick={() => setChannelDrawerItem(item)}
                    className="px-3.5 py-1.5 rounded-xl border border-bordergrey hover:bg-softbeige text-charcoal text-xs font-bold cursor-pointer transition-colors"
                  >
                    Setup Guide
                  </button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Channel Detail Drawer / Modal (8 Items from Part 9.3) */}
      {channelDrawerItem && (
        <Modal
          isOpen={Boolean(channelDrawerItem)}
          onClose={() => setChannelDrawerItem(null)}
          title={`${channelDrawerItem.display_name} — Channel Details`}
          maxWidth="2xl"
        >
          <div className="space-y-4 text-xs">
            {/* 1. Overview */}
            <div className="p-3.5 rounded-xl bg-warmwhite border border-bordergrey space-y-1">
              <span className="font-bold text-forest text-[11px] uppercase">1. Overview</span>
              <p className="text-charcoal leading-relaxed">{channelDrawerItem.description}</p>
            </div>

            {/* 2. Capabilities */}
            <div className="space-y-1">
              <span className="font-bold text-charcoal text-xs">2. Capabilities Supported:</span>
              <ul className="list-disc pl-5 text-charcoal-muted space-y-0.5">
                <li>Automated catalogue syndication & field mapping</li>
                <li>Channel-specific price and inventory overrides</li>
                <li>Centralized order ingestion and inventory deduction</li>
              </ul>
            </div>

            {/* 3. Required Permissions */}
            <div className="space-y-1">
              <span className="font-bold text-charcoal text-xs">3. Required Scopes & Permissions:</span>
              <div className="flex flex-wrap gap-1.5">
                {channelDrawerItem.granted_scopes.map((s) => (
                  <span key={s} className="px-2 py-0.5 rounded-lg bg-softbeige font-mono text-[10px] text-forest font-bold">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            {/* 4. Prerequisites & 5. Setup Instructions */}
            <div className="p-3.5 rounded-xl bg-brand-50 border border-brand-200 space-y-1">
              <span className="font-bold text-forest text-xs">4. Setup Instructions & Prerequisites:</span>
              <p className="text-charcoal leading-relaxed">
                {channelDrawerItem.setup_instructions || 'Log in to your merchant console, grant MarketPath API permissions, and confirm store URL.'}
              </p>
            </div>

            {/* Actions */}
            <div className="pt-3 border-t border-bordergrey flex items-center justify-between">
              <button
                onClick={() => setChannelDrawerItem(null)}
                className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige cursor-pointer"
              >
                Close
              </button>

              {channelDrawerItem.platform === 'shopify' && (
                <button
                  onClick={() => {
                    setChannelDrawerItem(null);
                    setShopifyModalOpen(true);
                  }}
                  className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c cursor-pointer"
                >
                  Initiate Connection →
                </button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Connect Shopify Modal */}
      {shopifyModalOpen && (
        <Modal
          isOpen={shopifyModalOpen}
          onClose={() => setShopifyModalOpen(false)}
          title="Connect Shopify Storefront"
          maxWidth="md"
        >
          <form onSubmit={handleStartShopifyOAuth} className="space-y-4 text-xs">
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">
                Shopify Store Domain (.myshopify.com) *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. aura-terra-living.myshopify.com"
                value={shopifyShopDomain}
                onChange={(e) => setShopifyShopDomain(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
              <p className="text-[11px] text-charcoal-muted mt-1">
                You will be redirected to Shopify Admin to approve read/write product permissions.
              </p>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-bordergrey">
              <button
                type="button"
                onClick={() => setShopifyModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c disabled:opacity-50"
              >
                {isSubmitting ? 'Opening Shopify...' : 'Authorize Store →'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Connect WooCommerce Modal */}
      {wooModalOpen && (
        <Modal
          isOpen={wooModalOpen}
          onClose={() => setWooModalOpen(false)}
          title="Connect WooCommerce Storefront"
          maxWidth="md"
        >
          <form onSubmit={handleConnectWooCommerce} className="space-y-4 text-xs">
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Store URL *</label>
              <input
                type="url"
                required
                placeholder="https://mystore.com"
                value={wooStoreUrl}
                onChange={(e) => setWooStoreUrl(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Consumer Key (ck_...) *</label>
              <input
                type="text"
                required
                placeholder="ck_xxxxxxxxxxxxxxxxxxxxxxxx"
                value={wooKey}
                onChange={(e) => setWooKey(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Consumer Secret (cs_...) *</label>
              <input
                type="password"
                required
                placeholder="cs_xxxxxxxxxxxxxxxxxxxxxxxx"
                value={wooSecret}
                onChange={(e) => setWooSecret(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
              <p className="text-[11px] text-charcoal-muted mt-1">
                Keys are stored with AES-256-GCM encryption at rest in our secure credentials vault.
              </p>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-bordergrey">
              <button
                type="button"
                onClick={() => setWooModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c disabled:opacity-50"
              >
                {isSubmitting ? 'Verifying...' : 'Link WooCommerce Store →'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Connect Amazon India Modal */}
      {amzModalOpen && (
        <Modal
          isOpen={amzModalOpen}
          onClose={() => setAmzModalOpen(false)}
          title="Connect Amazon India Seller Central (SP-API)"
          maxWidth="md"
        >
          <form onSubmit={handleConnectAmazon} className="space-y-3 text-xs">
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">LWA Client ID *</label>
              <input
                type="text"
                required
                placeholder="amzn1.application-oa2-client.xxxxxxxx"
                value={amzClientId}
                onChange={(e) => setAmzClientId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">LWA Client Secret *</label>
              <input
                type="password"
                required
                placeholder="amzn1.oa2-cs.v1.xxxxxxxx"
                value={amzClientSecret}
                onChange={(e) => setAmzClientSecret(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">LWA Refresh Token *</label>
              <input
                type="password"
                required
                placeholder="Atzr|xxxxxxxx"
                value={amzRefreshToken}
                onChange={(e) => setAmzRefreshToken(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Merchant / Seller ID *</label>
              <input
                type="text"
                required
                placeholder="e.g. A21TJRUUN4KGV"
                value={amzSellerId}
                onChange={(e) => setAmzSellerId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-bordergrey">
              <button
                type="button"
                onClick={() => setAmzModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c disabled:opacity-50"
              >
                {isSubmitting ? 'Authenticating...' : 'Connect SP-API →'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Connect Flipkart Modal */}
      {flpModalOpen && (
        <Modal
          isOpen={flpModalOpen}
          onClose={() => setFlpModalOpen(false)}
          title="Connect Flipkart Seller Hub"
          maxWidth="md"
        >
          <form onSubmit={handleConnectFlipkart} className="space-y-4 text-xs">
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Application ID *</label>
              <input
                type="text"
                required
                placeholder="e.g. flipkart-app-id-12345"
                value={flpAppId}
                onChange={(e) => setFlpAppId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Application Secret *</label>
              <input
                type="password"
                required
                placeholder="App Secret from Flipkart Developer Console"
                value={flpAppSecret}
                onChange={(e) => setFlpAppSecret(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-bordergrey bg-warmwhite focus:outline-none focus:border-brand-500 font-mono text-xs text-charcoal"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-bordergrey">
              <button
                type="button"
                onClick={() => setFlpModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c disabled:opacity-50"
              >
                {isSubmitting ? 'Connecting...' : 'Authorize Flipkart Hub →'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Disconnect Confirmation Modal */}
      {disconnectModalItem && (
        <Modal
          isOpen={Boolean(disconnectModalItem)}
          onClose={() => setDisconnectModalItem(null)}
          title={`Disconnect ${disconnectModalItem.display_name}`}
          maxWidth="sm"
        >
          <div className="space-y-4 text-xs">
            <div className="p-3.5 rounded-xl bg-softorange/10 border border-softorange/20 text-charcoal space-y-1">
              <span className="font-bold text-softorange flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" /> Are you sure?
              </span>
              <p className="text-[11px] leading-relaxed">
                Disconnecting <strong>{disconnectModalItem.account_name || disconnectModalItem.display_name}</strong> will revoke API credentials and stop background synchronization.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-warmwhite border border-bordergrey text-[11px] text-charcoal-muted">
              <strong className="text-forest block">Master Catalogue Guarantee:</strong>
              Your Master Product Catalogue, variants, and AI content remain 100% intact and untouched.
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-bordergrey">
              <button
                type="button"
                onClick={() => setDisconnectModalItem(null)}
                className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige"
              >
                Keep Connected
              </button>
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-xs disabled:opacity-50"
              >
                {isSubmitting ? 'Revoking...' : 'Revoke & Disconnect'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
