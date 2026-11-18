import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import {
  Plus,
  Search,
  Filter,
  Sparkles,
  Send,
  MoreVertical,
  CheckCircle2,
  AlertCircle,
  LayoutGrid,
  Table as TableIcon,
  Tag,
  Archive,
  Loader2,
  ExternalLink,
  Layers,
  ShoppingBag,
  Package,
  Mic,
  MicOff,
  FileText,
  ArrowRight,
  ArrowLeft,
  Check,
  X,
  Clock,
  Eye,
} from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { VoiceIntakeWidget } from '../../components/common/VoiceIntakeWidget';

export const ProductsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { session, activeOrg } = useAuth();
  const { products: contextProducts, addToast, setSelectedProductIdForStudio } = useApp();

  const [products, setProducts] = useState<any[]>(contextProducts);
  const [totalCount, setTotalCount] = useState(contextProducts.length);
  const [isLoading, setIsLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('table');

  // Product Creation Modal State (Part 7.1 & 7.5)
  const isCreateParam = searchParams.get('create') === 'true';
  const [isCreateOpen, setIsCreateOpen] = useState(isCreateParam);
  const [intakeMethod, setIntakeMethod] = useState<'form' | 'voice' | 'text'>('form');
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);

  // Form State
  const [newProd, setNewProd] = useState({
    title: '',
    sku: '',
    category: 'Home & Living / Decor',
    subcategory: '',
    brand: activeOrg?.name || 'Aura Terra Living',
    shortDescription: '',
    longDescription: '',
    materials: 'Natural Stoneware, Lead-free glaze',
    length: 15,
    width: 12,
    height: 10,
    unit: 'cm',
    weight: 0.5,
    careInstructions: 'Wipe with soft damp cloth. Avoid harsh chemicals.',
    basePrice: 999,
    compareAtPrice: 1299,
    costPrice: 350,
    stockQuantity: 25,
    packagingDimensions: '18 x 15 x 14 cm',
    packagedWeight: '0.65 kg',
    isFragile: true,
    mediaUrl: 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=400&q=80',
  });

  // Voice & Text Intake state
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [textNotes, setTextNotes] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const timerRef = useRef<any>(null);

  const categories = [
    'All',
    'Kitchen & Dining',
    'Home Fragrance & Decor',
    'Home & Living / Decor',
    'Artisanal Gifting',
    'Table Linen',
  ];

  const fetchProducts = async () => {
    if (!activeOrg?.id) return;
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: '1',
        page_size: '50',
      });
      if (search.trim()) params.append('search', search.trim());
      if (selectedCategory !== 'All') params.append('category', selectedCategory);
      if (selectedStatus !== 'All') params.append('status', selectedStatus.toLowerCase());

      const res = await apiClient(`/api/v1/products?${params.toString()}`, {
        token: session?.access_token,
        organizationId: activeOrg.id,
      });

      if (res && Array.isArray(res.items)) {
        setProducts(res.items);
        setTotalCount(res.total);
      } else {
        setProducts([]);
        setTotalCount(0);
      }
    } catch {
      setProducts(contextProducts);
      setTotalCount(contextProducts.length);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProducts();
    }, 200);
    return () => clearTimeout(timer);
  }, [search, selectedCategory, selectedStatus, activeOrg?.id]);

  useEffect(() => {
    if (searchParams.get('create') === 'true') {
      setIsCreateOpen(true);
    }
  }, [searchParams]);

  const handleOpenCreate = () => {
    setIsCreateOpen(true);
    setCurrentStep(1);
    setSearchParams({ create: 'true' });
  };

  const handleCloseCreate = () => {
    setIsCreateOpen(false);
    setSearchParams({});
  };

  // Launch AI Studio
  const handleLaunchAI = (productId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedProductIdForStudio(productId);
    navigate(`/app/ai-studio?product_id=${productId}`);
  };

  // Archive Product
  const handleArchive = async (productId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient(`/api/v1/products/${productId}`, {
        method: 'DELETE',
        token: session?.access_token,
        organizationId: activeOrg?.id,
      });
      addToast({ type: 'info', title: 'Product Archived', message: 'Product archived from active catalogue.' });
      fetchProducts();
    } catch (err: any) {
      addToast({ type: 'error', title: 'Archive Failed', message: err.message || 'Could not archive product.' });
    }
  };

  // Voice recording toggle
  const toggleRecording = async () => {
    if (isRecording) {
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setIsRecording(true);
        setRecordSeconds(0);
        timerRef.current = setInterval(() => setRecordSeconds((s) => s + 1), 1000);
      } catch {
        addToast({
          type: 'info',
          title: 'Microphone Permission Needed',
          message: 'Please allow microphone access or paste product notes below.',
        });
      }
    }
  };

  // Extract from Voice / Text with unit normalization and provenance
  const handleExtractSpecs = async (overrideText?: string) => {
    const inputContent = (overrideText || (intakeMethod === 'voice' ? voiceTranscript : textNotes)).trim();
    if (!inputContent) {
      addToast({ type: 'warning', title: 'Input Required', message: 'Please speak or paste notes first.' });
      return;
    }

    setIsExtracting(true);
    try {
      const res: any = await apiClient('/api/v1/voice/extract-product', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({ transcript: inputContent, category_hint: newProd.category }),
      });

      if (res && res.title) {
        setNewProd((prev) => ({
          ...prev,
          title: res.title || prev.title,
          sku: res.sku || prev.sku || `MP-${(res.category || 'GEN').slice(0, 3).toUpperCase()}-${Math.floor(1000 + Math.random() * 9000)}`,
          shortDescription: res.short_description || prev.shortDescription,
          longDescription: res.long_description || prev.longDescription,
          basePrice: res.base_price !== undefined ? res.base_price : prev.basePrice,
          compareAtPrice: res.compare_at_price !== undefined ? res.compare_at_price : Math.round((res.base_price || prev.basePrice) * 1.3),
          costPrice: res.cost_price !== undefined ? res.cost_price : prev.costPrice,
          category: res.category || prev.category,
          materials: Array.isArray(res.materials) ? res.materials.join(', ') : (res.materials || prev.materials),
          weight: res.weight_kg !== undefined ? res.weight_kg : prev.weight,
          length: res.dimensions_cm?.length !== undefined ? res.dimensions_cm.length : prev.length,
          width: res.dimensions_cm?.width !== undefined ? res.dimensions_cm.width : prev.width,
          height: res.dimensions_cm?.height !== undefined ? res.dimensions_cm.height : prev.height,
          packagingDimensions: res.packaging_specs?.box_length_cm
            ? `${res.packaging_specs.box_length_cm} x ${res.packaging_specs.box_width_cm} x ${res.packaging_specs.box_height_cm} cm`
            : prev.packagingDimensions,
          packagedWeight: res.packaging_specs?.dead_weight_kg
            ? `${res.packaging_specs.dead_weight_kg} kg`
            : prev.packagedWeight,
          isFragile: res.category_attributes?.fragile !== undefined ? res.category_attributes.fragile : prev.isFragile,
          careInstructions: res.category_attributes?.care_instructions || prev.careInstructions,
        }));
        addToast({
          type: 'success',
          title: 'Specifications Extracted',
          message: `Extracted specifications for "${res.title}" with normalized units and SKU.`,
        });
        setIntakeMethod('form');
        setCurrentStep(1);
      }
    } catch (err: any) {
      console.warn('Product extraction error:', err);
      // Fallback extraction
      setNewProd((prev) => ({
        ...prev,
        title: inputContent.slice(0, 50),
        shortDescription: inputContent.slice(0, 140),
        sku: `MP-GEN-${Math.floor(1000 + Math.random() * 9000)}`,
      }));
      setIntakeMethod('form');
      setCurrentStep(1);
    } finally {
      setIsExtracting(false);
    }
  };

  // Submit Product Creation
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProd.title.trim()) {
      addToast({ type: 'warning', title: 'Title Required', message: 'Please provide a product title.' });
      return;
    }

    setIsSubmitting(true);
    try {
      const masterSku = newProd.sku || `SKU-${Math.floor(100000 + Math.random() * 900000)}`;
      const payload = {
        title: newProd.title,
        sku: masterSku,
        category: newProd.category,
        short_description: newProd.shortDescription,
        long_description: newProd.longDescription,
        base_price: Number(newProd.basePrice),
        compare_at_price: Number(newProd.compareAtPrice),
        cost_price: Number(newProd.costPrice),
        currency: 'INR',
        stock_quantity: Number(newProd.stockQuantity),
        materials: newProd.materials ? [newProd.materials] : ['Natural Clay'],
        dimensions: {
          length: Number(newProd.length),
          width: Number(newProd.width),
          height: Number(newProd.height),
          unit: newProd.unit,
        },
        weight_kg: Number(newProd.weight),
        media: [{ media_url: newProd.mediaUrl, position: 0 }],
      };

      const res = await apiClient('/api/v1/products', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify(payload),
      });

      addToast({
        type: 'success',
        title: 'Master SKU Created',
        message: `${newProd.title} has been added to the master catalogue.`,
      });
      handleCloseCreate();
      fetchProducts();
      if (res?.id) {
        navigate(`/app/products/${res.id}`);
      }
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Creation Failed',
        message: err.message || 'Could not save master product.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Operational metrics
  const activeCount = products.filter((p) => p.status === 'active' || p.status === 'published').length;
  const draftCount = products.filter((p) => p.status === 'draft' || !p.status).length;
  const needsAttentionCount = products.filter((p) => !p.base_price || !p.primary_image_url || p.status === 'incomplete').length;

  return (
    <div className="space-y-6">
      {/* 01. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-bordergrey">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-forest bg-softbeige px-3 py-1 rounded-full border border-bordergrey">
            Master Truth
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-2">
            Master Product Catalogue
          </h1>
          <p className="text-xs sm:text-sm text-charcoal-muted mt-1">
            Single source of truth for products. Channel modifications and AI copy are kept separate from master truth.
          </p>
        </div>

        {/* Primary Add Action */}
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-forest text-white font-bold text-xs shadow-option-c transition-all self-start sm:self-auto cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Add Master SKU</span>
        </button>
      </div>

      {/* 02. Catalogue Summary KPI Chips */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl border border-bordergrey bg-purewhite shadow-xs">
          <span className="text-[11px] font-bold text-charcoal-muted uppercase">Total Products</span>
          <div className="text-xl font-extrabold text-charcoal mt-1">{totalCount}</div>
        </div>
        <div className="p-3.5 rounded-xl border border-bordergrey bg-purewhite shadow-xs">
          <span className="text-[11px] font-bold text-emerald uppercase">Active / Published</span>
          <div className="text-xl font-extrabold text-charcoal mt-1">{activeCount}</div>
        </div>
        <div className="p-3.5 rounded-xl border border-bordergrey bg-purewhite shadow-xs">
          <span className="text-[11px] font-bold text-charcoal-muted uppercase">Drafts</span>
          <div className="text-xl font-extrabold text-charcoal mt-1">{draftCount}</div>
        </div>
        <div className="p-3.5 rounded-xl border border-bordergrey bg-purewhite shadow-xs">
          <span className="text-[11px] font-bold text-softorange uppercase">Needs Attention</span>
          <div className="text-xl font-extrabold text-charcoal mt-1">{needsAttentionCount}</div>
        </div>
      </div>

      {/* 03. Search & Filters Bar */}
      <div className="p-4 rounded-2xl bg-purewhite border border-bordergrey shadow-option-c flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-charcoal-muted absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by title, master SKU, or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs pl-10 pr-4 py-2 rounded-xl border border-bordergrey focus:outline-none focus:border-brand-500 bg-warmwhite/50 text-charcoal placeholder:text-charcoal-muted"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs px-3 py-2 rounded-xl border border-bordergrey bg-purewhite text-charcoal font-medium focus:outline-none cursor-pointer"
          >
            {categories.map((c) => (
              <option key={c} value={c}>
                {c === 'All' ? 'All Categories' : c}
              </option>
            ))}
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs px-3 py-2 rounded-xl border border-bordergrey bg-purewhite text-charcoal font-medium focus:outline-none cursor-pointer"
          >
            <option value="All">All Statuses</option>
            <option value="active">Active / Published</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>

          <div className="border-l border-bordergrey h-6 mx-1 hidden sm:block" />

          {/* View Toggles */}
          <div className="flex items-center rounded-xl bg-softbeige p-1 border border-bordergrey">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                viewMode === 'table' ? 'bg-purewhite text-forest shadow-xs font-bold' : 'text-charcoal-muted hover:text-charcoal'
              }`}
              title="Table View"
            >
              <TableIcon className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                viewMode === 'grid' ? 'bg-purewhite text-forest shadow-xs font-bold' : 'text-charcoal-muted hover:text-charcoal'
              }`}
              title="Grid View"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 04. Product Catalogue Table / Grid / Empty States */}
      {isLoading ? (
        <div className="p-12 text-center bg-purewhite rounded-2xl border border-bordergrey">
          <Loader2 className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
          <p className="text-xs text-charcoal-muted">Loading master product catalogue...</p>
        </div>
      ) : products.length === 0 ? (
        <div className="p-12 text-center bg-purewhite rounded-3xl border border-dashed border-bordergrey space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-softbeige text-forest flex items-center justify-center mx-auto">
            <Package className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-charcoal">
            {totalCount === 0 ? 'Your master catalogue is empty' : 'No matching products found'}
          </h3>
          <p className="text-xs text-charcoal-muted max-w-sm mx-auto leading-relaxed">
            {totalCount === 0
              ? 'Add your first master SKU using structured form, voice intake, or by pasting your product notes.'
              : `No products match "${search || selectedCategory || selectedStatus}". Clear filters to view all products.`}
          </p>
          <div className="pt-2">
            <button
              onClick={handleOpenCreate}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-forest text-white font-bold text-xs shadow-option-c transition-colors cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              Add First Master SKU
            </button>
          </div>
        </div>
      ) : viewMode === 'table' ? (
        /* Table View */
        <div className="bg-purewhite rounded-2xl border border-bordergrey shadow-option-c overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-softbeige/60 border-b border-bordergrey text-[11px] font-bold uppercase tracking-wider text-charcoal-muted">
                  <th className="py-3 px-4">Product & Master SKU</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Base Price</th>
                  <th className="py-3 px-4">Stock</th>
                  <th className="py-3 px-4">Publishing Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-bordergrey/60 text-xs">
                {products.map((p) => {
                  const imageUrl =
                    p.primary_image_url ||
                    (p.media && p.media[0]?.media_url) ||
                    'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=150&q=80';

                  return (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/app/products/${p.id}`)}
                      className="hover:bg-warmwhite transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          <img
                            src={imageUrl}
                            alt={p.title}
                            className="w-10 h-10 rounded-xl object-cover border border-bordergrey shrink-0 bg-softbeige"
                          />
                          <div className="min-w-0">
                            <span className="font-bold text-charcoal block truncate group-hover:text-forest">
                              {p.title}
                            </span>
                            <span className="text-[11px] text-charcoal-muted font-mono block">
                              SKU: {p.sku || `SKU-${p.id.slice(0, 6)}`}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-charcoal-muted font-medium">
                        {p.category || 'General'}
                      </td>

                      <td className="py-3.5 px-4 font-bold text-charcoal">
                        ₹{(p.base_price || p.basePrice || 0).toLocaleString('en-IN')}
                      </td>

                      <td className="py-3.5 px-4">
                        <span className={`font-semibold ${Number(p.stock_quantity || p.stockQuantity || 0) < 10 ? 'text-softorange' : 'text-charcoal'}`}>
                          {p.stock_quantity ?? p.stockQuantity ?? 0} in stock
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        {p.status === 'published' || p.status === 'active' ? (
                          <Badge variant="success" size="sm" dot>
                            Published
                          </Badge>
                        ) : p.status === 'draft' ? (
                          <Badge variant="neutral" size="sm">
                            Draft
                          </Badge>
                        ) : (
                          <Badge variant="warning" size="sm">
                            {p.status || 'Ready'}
                          </Badge>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={(e) => handleLaunchAI(p.id, e)}
                            className="p-1.5 text-softorange hover:bg-softorange/10 rounded-lg transition-colors cursor-pointer"
                            title="Generate Listing Copy in Content Studio"
                          >
                            <Sparkles className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => navigate(`/app/products/${p.id}`)}
                            className="p-1.5 text-charcoal-muted hover:text-charcoal hover:bg-softbeige/50 rounded-lg transition-colors cursor-pointer"
                            title="View Product Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => handleArchive(p.id, e)}
                            className="p-1.5 text-charcoal-muted hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                            title="Archive"
                          >
                            <Archive className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Grid View */
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {products.map((p) => {
            const imageUrl =
              p.primary_image_url ||
              (p.media && p.media[0]?.media_url) ||
              'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=400&q=80';

            return (
              <Card
                key={p.id}
                onClick={() => navigate(`/app/products/${p.id}`)}
                className="overflow-hidden hover:border-brand-300 transition-all cursor-pointer group flex flex-col justify-between"
              >
                <div>
                  <div className="h-44 bg-softbeige overflow-hidden relative border-b border-bordergrey">
                    <img
                      src={imageUrl}
                      alt={p.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute top-2 right-2">
                      <Badge variant={p.status === 'published' ? 'success' : 'neutral'} size="sm">
                        {p.status || 'Draft'}
                      </Badge>
                    </div>
                  </div>

                  <div className="p-4 space-y-1.5">
                    <span className="text-[10px] font-bold text-forest uppercase tracking-wider block">
                      {p.category || 'General'}
                    </span>
                    <h3 className="text-xs font-bold text-charcoal truncate group-hover:text-forest">
                      {p.title}
                    </h3>
                    <p className="text-[11px] font-mono text-charcoal-muted truncate">
                      {p.sku || `SKU-${p.id.slice(0, 6)}`}
                    </p>
                    <div className="pt-2 flex items-baseline justify-between border-t border-bordergrey">
                      <span className="text-sm font-extrabold text-charcoal">
                        ₹{(p.base_price || p.basePrice || 0).toLocaleString('en-IN')}
                      </span>
                      <span className="text-[11px] text-charcoal-muted font-medium">
                        {p.stock_quantity ?? p.stockQuantity ?? 0} in stock
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-warmwhite border-t border-bordergrey flex items-center justify-between text-xs" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={(e) => handleLaunchAI(p.id, e)}
                    className="text-brand-600 hover:text-forest font-bold flex items-center gap-1 text-[11px]"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-softorange" /> Content Studio
                  </button>
                  <button
                    onClick={() => navigate(`/app/products/${p.id}`)}
                    className="text-charcoal-muted hover:text-charcoal font-semibold text-[11px]"
                  >
                    Details →
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* 05. Product Creation Modal (3 Steps & 3 Intake Methods) */}
      <Modal
        isOpen={isCreateOpen}
        onClose={handleCloseCreate}
        title="Add Master Product SKU"
        maxWidth="3xl"
      >
        <div className="space-y-5">
          {/* Intake Method Selector */}
          <div className="flex items-center gap-2 bg-softbeige p-1 rounded-xl border border-bordergrey text-xs font-bold">
            <button
              type="button"
              onClick={() => setIntakeMethod('form')}
              className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                intakeMethod === 'form' ? 'bg-purewhite text-forest shadow-xs' : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              <span>Structured Form</span>
            </button>
            <button
              type="button"
              onClick={() => setIntakeMethod('voice')}
              className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                intakeMethod === 'voice' ? 'bg-purewhite text-forest shadow-xs' : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Speak About Product</span>
            </button>
            <button
              type="button"
              onClick={() => setIntakeMethod('text')}
              className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                intakeMethod === 'text' ? 'bg-purewhite text-forest shadow-xs' : 'text-charcoal-muted hover:text-charcoal'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Paste Notes</span>
            </button>
          </div>

          {/* Voice Intake Flow */}
          {intakeMethod === 'voice' && (
            <div className="space-y-4">
              <VoiceIntakeWidget
                title="Voice Master Product Intake"
                subtitle="Speak naturally about your product name, materials, price, dimensions, and packaging."
                placeholder="Spoken product specifications will appear here verbatim. You can verify or edit your notes before extracting..."
                extractButtonLabel="Extract Specifications & Fill Form"
                initialTranscript={voiceTranscript}
                onTranscribeComplete={(t) => setVoiceTranscript(t)}
                onExtractClick={(t) => {
                  setVoiceTranscript(t);
                  handleExtractSpecs(t);
                }}
                isExtracting={isExtracting}
              />
            </div>
          )}

          {/* Text Intake Flow */}
          {intakeMethod === 'text' && (
            <div className="space-y-4 p-4 rounded-2xl bg-warmwhite border border-bordergrey">
              <div>
                <label className="block text-xs font-bold text-charcoal mb-1">Paste Raw Product Notes</label>
                <textarea
                  rows={5}
                  value={textNotes}
                  onChange={(e) => setTextNotes(e.target.value)}
                  placeholder="Paste catalogue specs, supplier WhatsApp messages, or product copy. For example:
Handmade ceramic coffee mug in terracotta wash, 350ml capacity, 12cm height, weight 450g. MRP ₹999, selling price ₹799, cost ₹250. 50 units in stock. Microwave safe."
                  className="w-full px-3.5 py-2 rounded-xl border border-bordergrey bg-purewhite text-xs text-charcoal focus:outline-none focus:border-brand-500 leading-relaxed"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => handleExtractSpecs()}
                  disabled={isExtracting}
                  className="px-4 py-2 rounded-xl bg-forest hover:bg-brand-600 text-white text-xs font-bold shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {isExtracting ? 'Extracting Specs...' : 'Extract & Populate Form →'}
                </button>
              </div>
            </div>
          )}

          {/* 3-Step Stepper Header */}
          <div className="flex items-center justify-between pb-2 border-b border-bordergrey text-xs font-bold">
            {[
              { num: 1, label: '1. Identity & Specs' },
              { num: 2, label: '2. Variants & Stock' },
              { num: 3, label: '3. Packaging & Review' },
            ].map((st) => (
              <button
                key={st.num}
                type="button"
                onClick={() => setCurrentStep(st.num)}
                className={`flex items-center gap-1.5 pb-1 border-b-2 transition-all cursor-pointer ${
                  currentStep === st.num
                    ? 'border-forest text-forest font-bold'
                    : currentStep > st.num
                    ? 'border-emerald text-emerald font-semibold'
                    : 'border-transparent text-charcoal-muted'
                }`}
              >
                <span>{st.label}</span>
              </button>
            ))}
          </div>

          {/* Form Form Submission */}
          <form onSubmit={handleCreateSubmit} className="space-y-4">
            {/* STEP 1: Identity & Specifications */}
            {currentStep === 1 && (
              <div className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Product Title *</label>
                    <input
                      type="text"
                      value={newProd.title}
                      onChange={(e) => setNewProd({ ...newProd, title: e.target.value })}
                      placeholder="e.g. Handcrafted Terracotta Coffee Mug"
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Master SKU *</label>
                    <input
                      type="text"
                      value={newProd.sku}
                      onChange={(e) => setNewProd({ ...newProd, sku: e.target.value })}
                      placeholder="e.g. ATM-MUG-01"
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500 font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Category *</label>
                    <select
                      value={newProd.category}
                      onChange={(e) => setNewProd({ ...newProd, category: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500 cursor-pointer"
                    >
                      {categories.filter((c) => c !== 'All').map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Materials / Craft</label>
                    <input
                      type="text"
                      value={newProd.materials}
                      onChange={(e) => setNewProd({ ...newProd, materials: e.target.value })}
                      placeholder="e.g. Stoneware Clay, Mineral Glaze"
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Short Description</label>
                  <textarea
                    rows={2}
                    value={newProd.shortDescription}
                    onChange={(e) => setNewProd({ ...newProd, shortDescription: e.target.value })}
                    placeholder="Brief 1-2 sentence overview for channel storefronts."
                    className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div className="grid grid-cols-4 gap-2">
                  <div>
                    <label className="block text-[11px] font-bold text-charcoal mb-1">Length (cm)</label>
                    <input
                      type="number"
                      value={newProd.length}
                      onChange={(e) => setNewProd({ ...newProd, length: Number(e.target.value) })}
                      className="w-full px-2.5 py-1.5 rounded-xl border border-bordergrey bg-warmwhite text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-charcoal mb-1">Width (cm)</label>
                    <input
                      type="number"
                      value={newProd.width}
                      onChange={(e) => setNewProd({ ...newProd, width: Number(e.target.value) })}
                      className="w-full px-2.5 py-1.5 rounded-xl border border-bordergrey bg-warmwhite text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-charcoal mb-1">Height (cm)</label>
                    <input
                      type="number"
                      value={newProd.height}
                      onChange={(e) => setNewProd({ ...newProd, height: Number(e.target.value) })}
                      className="w-full px-2.5 py-1.5 rounded-xl border border-bordergrey bg-warmwhite text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-charcoal mb-1">Weight (kg)</label>
                    <input
                      type="number"
                      step="0.05"
                      value={newProd.weight}
                      onChange={(e) => setNewProd({ ...newProd, weight: Number(e.target.value) })}
                      className="w-full px-2.5 py-1.5 rounded-xl border border-bordergrey bg-warmwhite text-xs"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(2)}
                    className="px-4 py-2 rounded-xl bg-forest hover:bg-brand-600 text-white text-xs font-bold shadow-xs cursor-pointer flex items-center gap-1"
                  >
                    <span>Next: Variants & Stock</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: Variants & Stock */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Selling Price (₹) *</label>
                    <input
                      type="number"
                      value={newProd.basePrice}
                      onChange={(e) => setNewProd({ ...newProd, basePrice: Number(e.target.value) })}
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500 font-bold"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">MRP / Compare Price (₹)</label>
                    <input
                      type="number"
                      value={newProd.compareAtPrice}
                      onChange={(e) => setNewProd({ ...newProd, compareAtPrice: Number(e.target.value) })}
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Production Cost (₹)</label>
                    <input
                      type="number"
                      value={newProd.costPrice}
                      onChange={(e) => setNewProd({ ...newProd, costPrice: Number(e.target.value) })}
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Initial Physical Stock</label>
                  <input
                    type="number"
                    value={newProd.stockQuantity}
                    onChange={(e) => setNewProd({ ...newProd, stockQuantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500 font-semibold"
                  />
                  <span className="text-[10px] text-charcoal-muted mt-1 block">
                    Available-to-sell inventory will be synchronized to connected channels upon publishing.
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(1)}
                    className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige/50 cursor-pointer flex items-center gap-1"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(3)}
                    className="px-4 py-2 rounded-xl bg-forest hover:bg-brand-600 text-white text-xs font-bold shadow-xs cursor-pointer flex items-center gap-1"
                  >
                    <span>Next: Packaging & Review</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: Packaging & Review */}
            {currentStep === 3 && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Packaging Box Specs</label>
                    <input
                      type="text"
                      value={newProd.packagingDimensions}
                      onChange={(e) => setNewProd({ ...newProd, packagingDimensions: e.target.value })}
                      placeholder="e.g. 18 x 15 x 14 cm"
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-charcoal mb-1">Packaged Shipping Weight</label>
                    <input
                      type="text"
                      value={newProd.packagedWeight}
                      onChange={(e) => setNewProd({ ...newProd, packagedWeight: e.target.value })}
                      placeholder="e.g. 0.65 kg"
                      className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-charcoal mb-1">Primary Image URL</label>
                  <input
                    type="url"
                    value={newProd.mediaUrl}
                    onChange={(e) => setNewProd({ ...newProd, mediaUrl: e.target.value })}
                    placeholder="https://..."
                    className="w-full px-3 py-2 rounded-xl border border-bordergrey bg-warmwhite text-xs text-charcoal focus:outline-none focus:border-brand-500"
                  />
                </div>

                {/* Review Card */}
                <div className="p-3.5 rounded-2xl bg-brand-50 border border-brand-200 text-xs space-y-1.5">
                  <div className="font-bold text-forest flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald" />
                    Review Master SKU Summary
                  </div>
                  <div className="text-charcoal grid grid-cols-2 gap-1 text-[11px]">
                    <div><strong>Title:</strong> {newProd.title || 'Untitled'}</div>
                    <div><strong>SKU:</strong> {newProd.sku || 'Auto-generated'}</div>
                    <div><strong>Price:</strong> ₹{newProd.basePrice}</div>
                    <div><strong>Stock:</strong> {newProd.stockQuantity} units</div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(2)}
                    className="px-4 py-2 rounded-xl border border-bordergrey text-xs font-bold text-charcoal hover:bg-softbeige/50 cursor-pointer flex items-center gap-1"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back</span>
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-forest text-white text-xs font-bold shadow-option-c transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                  >
                    <Check className="w-4 h-4" />
                    <span>{isSubmitting ? 'Saving Master SKU...' : 'Save Master Product'}</span>
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
      </Modal>
    </div>
  );
};
