import React from 'react';
import { NavLink } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import {
  LayoutDashboard,
  Package,
  Wand2,
  Link2,
  Send,
  Calendar,
  Megaphone,
  BarChart3,
  CreditCard,
  Users,
  Settings,
  HelpCircle,
  Sparkles,
  Compass,
  ShoppingBag,
} from 'lucide-react';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

interface NavItem {
  name: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  highlight?: boolean;
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { products, channels, org } = useApp();

  const maxSkus = org?.maxSkus || 50;
  const maxChannels = org?.maxChannels || 5;

  const activeChannelsCount = channels.filter((c) => c.status === 'connected').length;

  const navigation: NavGroup[] = [
    {
      group: '01. WORKSPACE',
      items: [
        { name: 'Overview', to: '/app/dashboard', icon: LayoutDashboard },
      ],
    },
    {
      group: '02. BRAND & PRODUCTS',
      items: [
        { name: 'Brand Profile', to: '/app/brand', icon: Sparkles },
        {
          name: 'Product Catalogue',
          to: '/app/products',
          icon: Package,
          badge: products.length > 0 ? products.length : undefined,
        },
      ],
    },
    {
      group: '03. CHANNELS & SALES',
      items: [
        {
          name: 'Connected Channels',
          to: '/app/integrations',
          icon: Link2,
          badge: activeChannelsCount > 0 ? `${activeChannelsCount} Active` : undefined,
        },
        { name: 'Listings & Performance', to: '/app/publishing', icon: Send },
        { name: 'Orders & Inventory', to: '/app/orders', icon: ShoppingBag },
      ],
    },
    {
      group: '04. GROWTH',
      items: [
        { name: 'Content Studio', to: '/app/ai-studio', icon: Wand2, highlight: true },
        { name: 'Marketing & Ads', to: '/app/marketing', icon: Megaphone },
        { name: 'Growth Analytics', to: '/app/analytics', icon: BarChart3 },
      ],
    },
    {
      group: '05. PLANNING & PARTNERS',
      items: [
        { name: 'Business Calendar', to: '/app/calendar', icon: Calendar },
        { name: 'Agency Discovery', to: '/app/agency-connect', icon: Compass },
      ],
    },
    {
      group: '06. WORKSPACE SETTINGS',
      items: [
        { name: 'Team & Roles', to: '/app/team', icon: Users },
        { name: 'Billing & Plan', to: '/app/billing', icon: CreditCard },
        { name: 'Settings', to: '/app/settings', icon: Settings },
        { name: 'Help & Support', to: '/app/help', icon: HelpCircle },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-charcoal/40 z-40 lg:hidden backdrop-blur-xs"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 w-64 bg-white border-r border-bordergrey flex flex-col transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand Logo Header */}
        <div className="h-16 px-6 flex items-center border-b border-bordergrey">
          <NavLink to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-forest bg-gradient-to-tr from-[#075443] via-[#08765B] to-[#15966F] border border-[#15966F]/40 flex items-center justify-center text-white shadow-xs">
              <span className="font-extrabold text-sm tracking-tight">MP</span>
            </div>
            <div>
              <span className="text-base font-bold text-charcoal tracking-tight">
                MarketPath <span className="text-brand-600 font-bold">AI</span>
              </span>
              <span className="block text-[9px] text-charcoal-muted uppercase tracking-widest font-semibold">
                D2C Growth OS
              </span>
            </div>
          </NavLink>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navigation.map((group) => (
            <div key={group.group}>
              <div className="px-3 text-[10px] font-extrabold text-charcoal-muted uppercase tracking-wider mb-1.5">
                {group.group}
              </div>
              <ul className="space-y-0.5">
                {group.items.map((item) => (
                  <li key={item.name}>
                    <NavLink
                      to={item.to}
                      onClick={onClose}
                      className={({ isActive }) =>
                        `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                          isActive
                            ? 'bg-brand-50 text-forest font-bold shadow-2xs border border-brand-200/60'
                            : 'text-charcoal-muted hover:text-charcoal hover:bg-softbeige/50'
                        }`
                      }
                    >
                      <div className="flex items-center gap-2.5">
                        <item.icon className="w-4 h-4 shrink-0" />
                        <span>{item.name}</span>
                      </div>
                      {item.badge && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-softbeige text-forest font-bold border border-bordergrey">
                          {item.badge}
                        </span>
                      )}
                      {item.highlight && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-softorange-50 text-softorange-700 font-bold uppercase tracking-wider border border-softorange-200">
                          AI
                        </span>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Plan Usage Meter */}
        <div className="p-4 m-3 bg-softbeige/50 rounded-2xl border border-bordergrey">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-charcoal">Growth Plan</span>
            <span className="text-[10px] text-forest font-extrabold">₹2,499/mo</span>
          </div>

          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-[10px] text-charcoal-muted mb-1">
                <span>Active SKUs</span>
                <span className="font-bold text-charcoal">{products.length} / {maxSkus}</span>
              </div>
              <div className="w-full h-1.5 bg-bordergrey rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-600 rounded-full"
                  style={{ width: `${Math.min((products.length / maxSkus) * 100, 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[10px] text-charcoal-muted mb-1">
                <span>Channels</span>
                <span className="font-bold text-charcoal">{channels.filter(c => c.status === 'connected').length} / {maxChannels}</span>
              </div>
              <div className="w-full h-1.5 bg-bordergrey rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald rounded-full"
                  style={{ width: `${(channels.filter(c => c.status === 'connected').length / maxChannels) * 100}%` }}
                />
              </div>
            </div>
          </div>

          <NavLink
            to="/app/billing"
            className="block text-center mt-3 text-[11px] font-bold text-forest hover:text-brand-600 hover:underline"
          >
            Upgrade or Add Quota →
          </NavLink>
        </div>
      </aside>
    </>
  );
};
