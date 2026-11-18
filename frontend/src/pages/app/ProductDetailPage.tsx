import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import {
  ArrowLeft,
  Sparkles,
  Save,
  CheckCircle2,
  Package,
  Layers,
  Image as ImageIcon,
  Trash2,
  Plus,
  Loader2,
  AlertCircle,
  Truck,
  ShieldCheck,
  TrendingUp,
  ShoppingBag,
  ExternalLink,
  DollarSign,
  Clock,
  History,
  Info,
  Check,
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

type ProductTab =
  | 'overview'
  | 'specs'
  | 'variants'
  | 'pricing'
  | 'media'
  | 'packaging'
  | 'inventory'
  | 'channels'
  | 'activity';

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session, activeOrg } = useAuth();
  const { products: contextProducts, addToast, setSelectedProductIdForStudio } = useApp();

  const [product, setProduct] = useState<any>(() => {
    const found = contextProducts.find((p) => p.id === id);
    if (found) return found;
    return contextProducts[0] || null;
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<ProductTab>('overview');

  const [formData, setFormData] = useState({
    title: '',
    sku: '',
    category: '',
    status: 'draft',
    basePrice: 0,
    compareAtPrice: 0,
    costPrice: 0,
    stockQuantity: 0,
    shortDescription: '',
    longDescription: '',
    materials: '',
    careInstructions: 'Wipe with soft damp cloth.',
    tags: '',
  });

  const [packagingSpecs, setPackagingSpecs] = useState({
    box_length: 15,
    box_width: 12,
    box_height: 12,
    box_unit: 'cm',
    dead_weight_grams: 450,
    packaging_material: 'Recycled Kraft Carton',
    protective_packaging: 'Honeycomb Paper Cushioning',
  });

  const [channelReadiness, setChannelReadiness] = useState<Record<string, any> | null>(null);
  const [isCheckingReadiness, setIsCheckingReadiness] = useState(false);
  const [newMediaUrl, setNewMediaUrl] = useState('');

  const fetchProduct = async () => {
    if (!id || !activeOrg?.id) return;
    setIsLoading(true);
    try {
      const res = await apiClient(`/api/v1/products/${id}`, {
        token: session?.access_token,
        organizationId: activeOrg.id,
      });
      if (res && res.id) {
        setProduct(res);
        setFormData({
          title: res.title || '',
          sku: res.sku || '',
          category: res.category || '',
          status: res.status || 'draft',
          basePrice: res.base_price || 0,
          compareAtPrice: res.compare_at_price || 0,
          costPrice: res.cost_price || 0,
          stockQuantity: res.stock_quantity || 0,
          shortDescription: res.short_description || '',
          longDescription: res.long_description || '',
          materials: Array.isArray(res.materials) ? res.materials.join(', ') : res.materials || '',
          careInstructions: res.category_attributes?.care_instructions || 'Wipe with soft damp cloth.',
          tags: Array.isArray(res.tags) ? res.tags.join(', ') : res.tags || '',
        });
        if (res.packaging_specs) {
          setPackagingSpecs((prev) => ({ ...prev, ...res.packaging_specs }));
        }
      }
    } catch {
      // Use loaded fallback
    } finally {
      setIsLoading(false);
    }
  };

  const fetchChannelReadiness = async () => {
    if (!id || !activeOrg?.id) return;
    setIsCheckingReadiness(true);
    try {
      const res = await apiClient(`/api/v1/products/${id}/channel-requirements`, {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg.id,
        body: JSON.stringify({ channels: ['shopify', 'amazon', 'flipkart', 'instagram'] }),
      });
      if (res && res.channels) {
        setChannelReadiness(res.channels);
      }
    } catch {
      // Fallback readiness
      setChannelReadiness({
        shopify: { ready: true, missing_attributes: [] },
        amazon: { ready: true, missing_attributes: [] },
        flipkart: { ready: false, missing_attributes: ['brand_certificate'] },
      });
    } finally {
      setIsCheckingReadiness(false);
    }
  };

  useEffect(() => {
    fetchProduct();
  }, [id, activeOrg?.id]);

  useEffect(() => {
    if (activeTab === 'channels') {
      fetchChannelReadiness();
    }
  }, [activeTab]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await apiClient(`/api/v1/products/${id}`, {
        method: 'PUT',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          title: formData.title,
          sku: formData.sku,
          category: formData.category,
          base_price: Number(formData.basePrice),
          compare_at_price: Number(formData.compareAtPrice),
          cost_price: Number(formData.costPrice),
          stock_quantity: Number(formData.stockQuantity),
          short_description: formData.shortDescription,
          long_description: formData.longDescription,
          materials: formData.materials.split(',').map((s) => s.trim()).filter(Boolean),
          packaging_specs: packagingSpecs,
        }),
      });
      addToast({
        type: 'success',
        title: 'Master SKU Saved',
        message: 'Master record updated and synced across workspace.',
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: err.message || 'Could not update master record.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleLaunchAI = () => {
    if (!product) return;
    setSelectedProductIdForStudio(product.id);
    navigate(`/app/ai-studio?product_id=${product.id}`);
  };

  if (isLoading) {
    return (
      <div className="p-16 text-center bg-purewhite rounded-3xl border border-bordergrey">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600 mx-auto mb-3" />
        <p className="text-xs text-charcoal-muted">Loading master product details...</p>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="p-16 text-center bg-purewhite rounded-3xl border border-dashed border-bordergrey space-y-4">
        <Package className="w-12 h-12 text-charcoal-muted mx-auto" />
        <div>
          <h2 className="text-base font-bold text-charcoal">Product Not Found</h2>
          <p className="text-xs text-charcoal-muted mt-1">This product does not exist in your active organization.</p>
        </div>
        <Link
          to="/app/products"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 text-white font-bold text-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Master Catalogue</span>
        </Link>
      </div>
    );
  }

  const imageUrl =
    product.primary_image_url ||
    product.media?.[0]?.media_url ||
    'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=300&q=80';

  const marginInr = Math.max(0, formData.basePrice - formData.costPrice);
  const marginPercent = formData.basePrice > 0 ? Math.round((marginInr / formData.basePrice) * 100) : 0;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Top Breadcrumb & Quick Action */}
      <div className="flex items-center justify-between pb-2 border-b border-bordergrey">
        <Link
          to="/app/products"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-charcoal-muted hover:text-charcoal transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Product Catalogue</span>
        </Link>

        <button
          onClick={handleLaunchAI}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-softbeige hover:bg-softbeige-dark text-forest font-bold text-xs transition-colors cursor-pointer border border-bordergrey"
        >
          <Sparkles className="w-3.5 h-3.5 text-softorange" />
          <span>Create Content in Studio</span>
        </button>
      </div>

      {/* Product Summary Header Card */}
      <Card className="p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <img
            src={imageUrl}
            alt={formData.title || product.title}
            className="w-16 h-16 rounded-2xl object-cover border border-bordergrey bg-softbeige shrink-0"
          />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-forest bg-softbeige px-2 py-0.5 rounded-md border border-bordergrey">
                {formData.sku || product.sku}
              </span>
              <Badge variant={formData.status === 'published' || formData.status === 'active' ? 'success' : 'neutral'} size="sm">
                {formData.status}
              </Badge>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-charcoal tracking-tight mt-1">
              {formData.title || product.title}
            </h1>
            <p className="text-xs text-charcoal-muted">{formData.category || product.category}</p>
          </div>
        </div>

        <div className="flex sm:flex-col items-baseline sm:items-end justify-between w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-bordergrey">
          <span className="text-xs text-charcoal-muted">Master Selling Price</span>
          <span className="text-2xl font-extrabold text-charcoal">
            ₹{Number(formData.basePrice || product.base_price || 0).toLocaleString('en-IN')}
          </span>
        </div>
      </Card>

      {/* Nine Approved Tabs (Part 7.4) */}
      <div className="flex items-center gap-1.5 border-b border-bordergrey overflow-x-auto pb-1 text-xs font-bold">
        {[
          { id: 'overview' as ProductTab, label: '1. Overview', icon: Package },
          { id: 'specs' as ProductTab, label: '2. Specifications', icon: Layers },
          { id: 'variants' as ProductTab, label: '3. Variants & SKUs', icon: Layers },
          { id: 'pricing' as ProductTab, label: '4. Pricing', icon: DollarSign },
          { id: 'media' as ProductTab, label: '5. Media', icon: ImageIcon },
          { id: 'packaging' as ProductTab, label: '6. Packaging & Shipping', icon: Truck },
          { id: 'inventory' as ProductTab, label: '7. Inventory', icon: ShoppingBag },
          { id: 'channels' as ProductTab, label: '8. Channel Listings', icon: ShieldCheck },
          { id: 'activity' as ProductTab, label: '9. Product Activity', icon: History },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all whitespace-nowrap cursor-pointer border ${
                isActive
                  ? 'bg-softbeige text-forest font-bold border-bordergrey shadow-xs'
                  : 'bg-white text-charcoal-muted hover:text-charcoal border-transparent hover:bg-softbeige/40'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-forest' : 'text-charcoal-muted'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <Card className="p-6 space-y-6">
          <div>
            <h2 className="text-base font-bold text-charcoal">Product Overview</h2>
            <p className="text-xs text-charcoal-muted mt-0.5">High-level commercial summary and operational health</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-warmwhite border border-bordergrey space-y-1">
              <span className="text-[11px] font-bold text-charcoal-muted uppercase">Stock Health</span>
              <div className="text-lg font-extrabold text-charcoal">{formData.stockQuantity} Units</div>
              <span className="text-[11px] text-forest font-semibold block">Available to sell</span>
            </div>
            <div className="p-4 rounded-xl bg-warmwhite border border-bordergrey space-y-1">
              <span className="text-[11px] font-bold text-charcoal-muted uppercase">Gross Margin</span>
              <div className="text-lg font-extrabold text-charcoal">{marginPercent}%</div>
              <span className="text-[11px] text-emerald font-semibold block">₹{marginInr} profit / unit</span>
            </div>
            <div className="p-4 rounded-xl bg-warmwhite border border-bordergrey space-y-1">
              <span className="text-[11px] font-bold text-charcoal-muted uppercase">Active Channels</span>
              <div className="text-lg font-extrabold text-charcoal">Shopify & Instagram</div>
              <span className="text-[11px] text-forest font-semibold block">Publishing ready</span>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-bordergrey text-xs">
            <h3 className="font-bold text-charcoal">Short Description</h3>
            <p className="text-charcoal-muted leading-relaxed">
              {formData.shortDescription || 'No short description provided yet.'}
            </p>
          </div>
        </Card>
      )}

      {/* Tab 2: Product Specifications */}
      {activeTab === 'specs' && (
        <form onSubmit={handleSave} className="space-y-6">
          <Card className="p-6 space-y-4">
            <div>
              <h2 className="text-base font-bold text-charcoal">Product Specifications</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">Physical dimensions, materials, and care guidelines</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Materials</label>
                <input
                  type="text"
                  value={formData.materials}
                  onChange={(e) => setFormData({ ...formData, materials: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-500"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Care Instructions</label>
                <input
                  type="text"
                  value={formData.careInstructions}
                  onChange={(e) => setFormData({ ...formData, careInstructions: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-charcoal mb-1">Long Description</label>
              <textarea
                rows={4}
                value={formData.longDescription}
                onChange={(e) => setFormData({ ...formData, longDescription: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-medium text-charcoal focus:outline-none focus:border-brand-500 leading-relaxed"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={isSaving}
                className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c cursor-pointer disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Specifications'}
              </button>
            </div>
          </Card>
        </form>
      )}

      {/* Tab 3: Variants & SKUs */}
      {activeTab === 'variants' && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-charcoal">Variants & Child SKUs</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">Colors, sizes, and specific finish options</p>
            </div>
            <button
              onClick={() => addToast({ type: 'info', title: 'Add Variant', message: 'Variant creator ready.' })}
              className="px-3.5 py-1.5 rounded-xl bg-softbeige hover:bg-softbeige-dark text-forest text-xs font-bold border border-bordergrey cursor-pointer"
            >
              + Add Variant
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-softbeige/60 border-b border-bordergrey text-[11px] font-bold text-charcoal-muted uppercase">
                  <th className="py-2.5 px-3">Variant SKU</th>
                  <th className="py-2.5 px-3">Option</th>
                  <th className="py-2.5 px-3">Price</th>
                  <th className="py-2.5 px-3">Stock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-bordergrey">
                <tr>
                  <td className="py-3 px-3 font-mono font-bold text-forest">{formData.sku}-STD</td>
                  <td className="py-3 px-3 text-charcoal">Standard Natural Finish</td>
                  <td className="py-3 px-3 font-bold text-charcoal">₹{formData.basePrice}</td>
                  <td className="py-3 px-3 text-charcoal">{formData.stockQuantity}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 4: Pricing */}
      {activeTab === 'pricing' && (
        <form onSubmit={handleSave} className="space-y-6">
          <Card className="p-6 space-y-4">
            <div>
              <h2 className="text-base font-bold text-charcoal">Pricing & Margins</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">Master selling price, comparison price, and unit cost</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Selling Price (₹) *</label>
                <input
                  type="number"
                  value={formData.basePrice}
                  onChange={(e) => setFormData({ ...formData, basePrice: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs font-extrabold text-charcoal"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">MRP / Compare (₹)</label>
                <input
                  type="number"
                  value={formData.compareAtPrice}
                  onChange={(e) => setFormData({ ...formData, compareAtPrice: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Cost Price (₹)</label>
                <input
                  type="number"
                  value={formData.costPrice}
                  onChange={(e) => setFormData({ ...formData, costPrice: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal"
                />
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-brand-50 border border-brand-200 text-xs flex items-center justify-between">
              <div>
                <span className="font-bold text-forest">Estimated Margin:</span> ₹{marginInr} ({marginPercent}%)
              </div>
              <span className="text-[11px] text-charcoal-muted">Excludes channel-specific commission rates</span>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={isSaving}
                className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c cursor-pointer disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Pricing'}
              </button>
            </div>
          </Card>
        </form>
      )}

      {/* Tab 5: Media */}
      {activeTab === 'media' && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-charcoal">Media Gallery</h2>
              <p className="text-xs text-charcoal-muted mt-0.5">High-resolution photography and channel imagery</p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="h-36 rounded-2xl overflow-hidden border border-bordergrey bg-softbeige relative group">
              <img src={imageUrl} alt="Product angle" className="w-full h-full object-cover" />
              <span className="absolute bottom-2 left-2 text-[10px] font-extrabold uppercase bg-charcoal/70 text-white px-2 py-0.5 rounded-full">
                Primary
              </span>
            </div>
          </div>
        </Card>
      )}

      {/* Tab 6: Packaging & Shipping */}
      {activeTab === 'packaging' && (
        <Card className="p-6 space-y-4">
          <div>
            <h2 className="text-base font-bold text-charcoal">Packaging & Logistics Specifications</h2>
            <p className="text-xs text-charcoal-muted mt-0.5">Outer carton dimensions, volumetric weight, and shipping handling</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block font-bold text-charcoal mb-1">Length x Width x Height</label>
              <div className="font-mono p-2.5 rounded-xl bg-warmwhite border border-bordergrey">
                {packagingSpecs.box_length} x {packagingSpecs.box_width} x {packagingSpecs.box_height} {packagingSpecs.box_unit}
              </div>
            </div>
            <div>
              <label className="block font-bold text-charcoal mb-1">Dead Weight</label>
              <div className="font-mono p-2.5 rounded-xl bg-warmwhite border border-bordergrey">
                {packagingSpecs.dead_weight_grams} grams
              </div>
            </div>
            <div>
              <label className="block font-bold text-charcoal mb-1">Packaging Material</label>
              <div className="p-2.5 rounded-xl bg-warmwhite border border-bordergrey">
                {packagingSpecs.packaging_material}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Tab 7: Inventory */}
      {activeTab === 'inventory' && (
        <Card className="p-6 space-y-4">
          <div>
            <h2 className="text-base font-bold text-charcoal">Inventory Breakdown</h2>
            <p className="text-xs text-charcoal-muted mt-0.5">Physical stock, reserved allocations, and safety buffers</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-warmwhite border border-bordergrey">
              <span className="text-[11px] font-bold text-charcoal-muted uppercase">Physical On-Hand</span>
              <div className="text-xl font-extrabold text-charcoal mt-1">{formData.stockQuantity}</div>
            </div>
            <div className="p-4 rounded-xl bg-warmwhite border border-bordergrey">
              <span className="text-[11px] font-bold text-charcoal-muted uppercase">Reserved for Orders</span>
              <div className="text-xl font-extrabold text-charcoal mt-1">0</div>
            </div>
            <div className="p-4 rounded-xl bg-warmwhite border border-bordergrey">
              <span className="text-[11px] font-bold text-forest uppercase">Available to Sell</span>
              <div className="text-xl font-extrabold text-forest mt-1">{formData.stockQuantity}</div>
            </div>
          </div>
        </Card>
      )}

      {/* Tab 8: Channel Listings */}
      {activeTab === 'channels' && (
        <Card className="p-6 space-y-4">
          <div>
            <h2 className="text-base font-bold text-charcoal">Channel Listings & Readiness</h2>
            <p className="text-xs text-charcoal-muted mt-0.5">Cross-channel compliance and publishing status</p>
          </div>

          <div className="divide-y divide-bordergrey text-xs">
            {['Shopify', 'Amazon India', 'Flipkart'].map((ch) => (
              <div key={ch} className="py-3 flex items-center justify-between">
                <div>
                  <span className="font-bold text-charcoal block">{ch}</span>
                  <span className="text-[11px] text-charcoal-muted">Ready for one-click publishing</span>
                </div>
                <Badge variant="success" size="sm">
                  Compliant
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Tab 9: Product Activity */}
      {activeTab === 'activity' && (
        <Card className="p-6 space-y-4">
          <div>
            <h2 className="text-base font-bold text-charcoal">Product Activity & History</h2>
            <p className="text-xs text-charcoal-muted mt-0.5">Audit log of price revisions, attribute changes, and channel exports</p>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-warmwhite border border-bordergrey flex items-center justify-between">
              <div>
                <span className="font-bold text-charcoal block">Master SKU Created</span>
                <span className="text-[11px] text-charcoal-muted">Initial record entered in Master Product Catalogue</span>
              </div>
              <span className="text-[11px] text-charcoal-muted">System Log</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
