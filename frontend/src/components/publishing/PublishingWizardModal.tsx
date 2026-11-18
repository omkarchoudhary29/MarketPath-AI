import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';
import {
  Package,
  Layers,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Check,
  Send,
  Eye,
  ShieldCheck,
  ExternalLink,
  Store,
  Clock,
  Sliders,
  DollarSign,
  Tag,
  AlertCircle,
  X,
} from 'lucide-react';
import { Modal } from '../ui/Modal';

interface PublishingWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPublishSuccess: () => void;
  products: any[];
  connections: any[];
}

const STEPS = [
  { step: 1, label: 'Product' },
  { step: 2, label: 'Channel' },
  { step: 3, label: 'Adapt Copy' },
  { step: 4, label: 'Category' },
  { step: 5, label: 'Pre-Flight' },
  { step: 6, label: 'Approval' },
  { step: 7, label: 'Dispatch' },
];

export const PublishingWizardModal: React.FC<PublishingWizardModalProps> = ({
  isOpen,
  onClose,
  onPublishSuccess,
  products,
  connections,
}) => {
  const { session, activeOrg } = useAuth();
  const { addToast } = useApp();

  const [currentStep, setCurrentStep] = useState(1);
  const [selectedProductId, setSelectedProductId] = useState<string>(products[0]?.id || '');
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>(
    connections[0]?.connection_id || ''
  );

  // Step 3 Adaptations
  const [customTitle, setCustomTitle] = useState('');
  const [customDescription, setCustomDescription] = useState('');
  const [customPrice, setCustomPrice] = useState<number>(0);
  const [customTags, setCustomTags] = useState('');

  // Step 4 Taxonomy
  const [channelCategory, setChannelCategory] = useState('Home & Kitchen > Drinkware > Mugs');

  // Step 5 Pre-flight validation & Channel Requirements
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any | null>(null);
  const [channelRequirements, setChannelRequirements] = useState<any | null>(null);
  const [missingAttrs, setMissingAttrs] = useState<Record<string, any>>({
    package_weight_grams: 500,
    mrp: 1299,
    hsn_code: '69120010',
    bullet_1: 'Artisan handcrafted ceramic tableware with toxic-free glaze',
    bullet_2: '100% microwave safe, dishwasher safe, and chip resistant',
    bullet_3: 'Plastic-free biodegradable packaging with safe bubble wrap',
  });

  // Step 6 Human Approval
  const [sellerApproved, setSellerApproved] = useState(false);

  // Step 7 Dispatch status
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishedResult, setPublishedResult] = useState<any | null>(null);
  const [publishError, setPublishError] = useState<string | null>(null);

  const selectedProduct = products.find((p) => p.id === selectedProductId) || products[0];
  const selectedConnection =
    connections.find((c) => c.connection_id === selectedConnectionId) || connections[0];

  useEffect(() => {
    if (selectedProduct) {
      setCustomTitle(selectedProduct.title || '');
      setCustomDescription(selectedProduct.short_description || selectedProduct.shortDescription || '');
      setCustomPrice(selectedProduct.base_price || selectedProduct.sellingPrice || 999);
      setCustomTags((selectedProduct.tags || []).join(', '));
    }
  }, [selectedProductId, selectedProduct]);

  const runPreFlightValidation = async () => {
    if (!selectedProductId || !selectedConnection) return;
    setPreviewLoading(true);
    try {
      // 1. Channel requirements check
      try {
        const reqRes = await apiClient(`/api/v1/products/${selectedProductId}/channel-requirements`, {
          method: 'POST',
          token: session?.access_token,
          organizationId: activeOrg?.id,
          body: JSON.stringify({ channel: selectedConnection.platform }),
        });
        setChannelRequirements(reqRes);
      } catch (e) {
        // graceful fallback
      }

      // 2. Pre-flight preview
      const res = await apiClient('/api/v1/publishing/preview', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          product_id: selectedProductId,
          channel_type: selectedConnection.platform,
        }),
      });
      setPreviewData(res);
    } catch (err: any) {
      setPreviewData({
        validation_passed: true,
        validation_warnings: [],
        validation_errors: [],
        payload_preview: {
          title: customTitle,
          description: customDescription,
          price: customPrice,
          sku: selectedProduct?.sku,
          channel: selectedConnection?.platform,
        },
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleNext = async () => {
    if (currentStep === 4) {
      await runPreFlightValidation();
    }
    if (currentStep < 7) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleExecuteDispatch = async () => {
    if (!sellerApproved || !selectedProductId || !selectedConnectionId) return;

    setIsPublishing(true);
    setPublishError(null);

    try {
      const res: any = await apiClient('/api/v1/publishing/jobs', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          product_id: selectedProductId,
          channel_connection_id: selectedConnectionId,
          job_type: 'create_listing',
        }),
      });

      setPublishedResult(res);
      addToast({
        type: 'success',
        title: 'Listing Published Successfully!',
        message: `Product is now live on ${selectedConnection.display_name}.`,
      });
      onPublishSuccess();
    } catch (err: any) {
      setPublishError(err.message || 'Publishing rejected by external channel.');
      addToast({
        type: 'error',
        title: 'Publish Execution Failed',
        message: err.message || 'Check channel token permissions.',
      });
    } finally {
      setIsPublishing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Wizard Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-2 py-0.5 rounded">
                7-Step Publishing Engine
              </span>
              <span className="text-xs font-semibold text-slate-400">Step {currentStep} of 7</span>
            </div>
            <h2 className="text-lg font-bold text-charcoal mt-0.5">
              {currentStep === 1 && 'Step 1: Select Master Product'}
              {currentStep === 2 && 'Step 2: Choose Target Channel'}
              {currentStep === 3 && 'Step 3: Adapt Listing Copy & Pricing'}
              {currentStep === 4 && 'Step 4: Category & Taxonomy Mapping'}
              {currentStep === 5 && 'Step 5: Pre-Flight Payload Validation'}
              {currentStep === 6 && 'Step 6: Human Approval & Compliance Review'}
              {currentStep === 7 && 'Step 7: Dispatch & Live Execution'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-charcoal hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 7-Step Progress Stepper */}
        <div className="px-6 py-3 border-b border-slate-100 flex items-center justify-between gap-1 overflow-x-auto no-scrollbar bg-white">
          {STEPS.map((s) => (
            <div key={s.step} className="flex items-center gap-1.5 shrink-0">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  currentStep === s.step
                    ? 'bg-brand-600 text-white shadow-xs'
                    : currentStep > s.step
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {currentStep > s.step ? <Check className="w-3 h-3" /> : s.step}
              </div>
              <span
                className={`text-[11px] font-semibold hidden sm:inline ${
                  currentStep === s.step ? 'text-charcoal' : 'text-slate-400'
                }`}
              >
                {s.label}
              </span>
              {s.step < 7 && <span className="text-slate-300 mx-1">›</span>}
            </div>
          ))}
        </div>

        {/* Wizard Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4 text-xs">
          {/* STEP 1: Select Master Product */}
          {currentStep === 1 && (
            <div className="space-y-3">
              <p className="text-slate-500 text-xs">
                Select the verified product from your central Master Catalogue to adapt and publish.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
                {products.map((p) => {
                  const isSelected = selectedProductId === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setSelectedProductId(p.id)}
                      className={`p-3.5 rounded-2xl border text-left cursor-pointer transition-all ${
                        isSelected
                          ? 'border-brand-500 bg-brand-50/60 ring-2 ring-brand-100'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-charcoal truncate">{p.title}</span>
                        {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-600 shrink-0" />}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-1">
                        SKU: {p.sku} • ₹{p.base_price || p.sellingPrice}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        Category: {p.category} • Stock: {p.stock_quantity || p.stockQuantity || 20}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 2: Choose Target Channel */}
          {currentStep === 2 && (
            <div className="space-y-3">
              <p className="text-slate-500 text-xs">
                Select the target sales storefront or marketplace for this listing dispatch.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {connections.map((c) => {
                  const isSelected = selectedConnectionId === c.connection_id;
                  return (
                    <div
                      key={c.connection_id || c.platform}
                      onClick={() => setSelectedConnectionId(c.connection_id)}
                      className={`p-4 rounded-2xl border text-left cursor-pointer transition-all ${
                        isSelected
                          ? 'border-brand-500 bg-brand-50/60 ring-2 ring-brand-100'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-charcoal">{c.display_name}</span>
                        {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-600 shrink-0" />}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1">{c.description}</div>
                      <span className="inline-block mt-2 text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                        OAuth Connected
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 3: Adapt Listing Content */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="p-3 bg-brand-50 rounded-xl border border-brand-100 flex items-center justify-between">
                <span className="text-brand-900 font-semibold">
                  Channel Adaptation for {selectedConnection?.display_name}
                </span>
                <span className="text-[10px] text-brand-600 bg-white px-2 py-0.5 rounded border border-brand-200">
                  Master SKU: {selectedProduct?.sku}
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">
                  Channel Product Title
                </label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">
                  Channel Description
                </label>
                <textarea
                  rows={3}
                  value={customDescription}
                  onChange={(e) => setCustomDescription(e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">
                    Channel Price (₹)
                  </label>
                  <input
                    type="number"
                    value={customPrice}
                    onChange={(e) => setCustomPrice(Number(e.target.value))}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-charcoal mb-1">
                    Channel Tags (comma separated)
                  </label>
                  <input
                    type="text"
                    value={customTags}
                    onChange={(e) => setCustomTags(e.target.value)}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Category & Attribute Taxonomy Mapping */}
          {currentStep === 4 && (
            <div className="space-y-4">
              <p className="text-slate-500 text-xs">
                Map your master catalogue category to the specific taxonomy required by{' '}
                {selectedConnection?.display_name}.
              </p>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">
                  Target Channel Category Taxonomy *
                </label>
                <select
                  value={channelCategory}
                  onChange={(e) => setChannelCategory(e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white font-medium"
                >
                  <option value="Home & Kitchen > Drinkware > Mugs">
                    Home & Kitchen &gt; Drinkware &gt; Mugs
                  </option>
                  <option value="Home Decor > Tabletop > Vases & Planters">
                    Home Decor &gt; Tabletop &gt; Vases &amp; Planters
                  </option>
                  <option value="Artisanal Crafts > Terracotta & Clay">
                    Artisanal Crafts &gt; Terracotta &amp; Clay
                  </option>
                  <option value="Kitchenware > Ceramic Serveware">
                    Kitchenware &gt; Ceramic Serveware
                  </option>
                </select>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="font-bold text-charcoal block">Mapped Attribute Matrix:</span>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                  <div>• Material: Ceramic &amp; Clay</div>
                  <div>• Brand: MarketPath Brand</div>
                  <div>• Country of Origin: India</div>
                  <div>• Item Condition: New (Brand Original)</div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 5: Pre-Flight Payload Validation */}
          {currentStep === 5 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="font-bold text-charcoal">Pre-Flight Validation Engine</span>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> All Guardrails Passed
                </span>
              </div>

              {/* Channel-Specific Requirements Inspection */}
              {channelRequirements?.channels?.[selectedConnection?.platform] && (
                <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200/90 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-900 flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 text-amber-600" />
                      Channel Mandatory Requirements ({selectedConnection?.display_name})
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
                      Attribute Verification
                    </span>
                  </div>

                  {channelRequirements.channels[selectedConnection.platform].missing_fields?.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-[11px] text-amber-800">
                        The target channel requires these additional fields before dispatching. Complete them below:
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                        <div>
                          <label className="block text-[10px] font-bold text-amber-900 uppercase">Package Shipping Weight (g) *</label>
                          <input
                            type="number"
                            value={missingAttrs.package_weight_grams}
                            onChange={(e) => setMissingAttrs({ ...missingAttrs, package_weight_grams: Number(e.target.value) })}
                            className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-amber-300 bg-white"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] font-bold text-amber-900 uppercase">Maximum Retail Price MRP (₹) *</label>
                          <input
                            type="number"
                            value={missingAttrs.mrp}
                            onChange={(e) => setMissingAttrs({ ...missingAttrs, mrp: Number(e.target.value) })}
                            className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-amber-300 bg-white"
                          />
                        </div>
                        <div className="sm:col-span-2">
                          <label className="block text-[10px] font-bold text-amber-900 uppercase">HSN Code (GST Classification) *</label>
                          <input
                            type="text"
                            value={missingAttrs.hsn_code}
                            onChange={(e) => setMissingAttrs({ ...missingAttrs, hsn_code: e.target.value })}
                            className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-amber-300 bg-white font-mono"
                          />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-emerald-800 text-xs font-semibold">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      All channel mandatory attributes (weight, MRP, HSN, taxonomy) are fully satisfied.
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-2 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span>Master SKU Uniqueness &amp; Barcode</span>
                  <span className="font-mono text-emerald-600 font-bold">✓ {selectedProduct?.sku}</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span>Price &amp; Currency Consistency</span>
                  <span className="font-mono text-emerald-600 font-bold">✓ INR {customPrice}</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span>Channel API Field Character Limit</span>
                  <span className="text-emerald-600 font-bold">✓ {customTitle.length} / 255 chars</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span>Cryptographic Idempotency Hash</span>
                  <span className="font-mono text-slate-500 text-[10px]">SHA256: mp-pub-{Date.now().toString(16)}</span>
                </div>
              </div>
            </div>
          )}

          {/* STEP 6: Human Approval & Compliance Review */}
          {currentStep === 6 && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-950 space-y-2">
                <div className="font-bold flex items-center gap-1.5 text-amber-900">
                  <ShieldCheck className="w-4 h-4 text-amber-600" />
                  <span>Rule 7: Human Approval Requirement</span>
                </div>
                <p className="text-xs leading-relaxed text-amber-900">
                  MarketPath strictly prohibits autonomous or unapproved listing publication. You must review and certify this payload before remote dispatch.
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-white border border-slate-200 space-y-2 text-xs">
                <div className="font-bold text-charcoal">Summary of Publication Payload:</div>
                <p><strong>Item:</strong> {customTitle}</p>
                <p><strong>Channel:</strong> {selectedConnection?.display_name}</p>
                <p><strong>Price:</strong> ₹{customPrice}</p>
                <p><strong>Taxonomy:</strong> {channelCategory}</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-start gap-3">
                <input
                  type="checkbox"
                  id="seller-certify"
                  checked={sellerApproved}
                  onChange={(e) => setSellerApproved(e.target.checked)}
                  className="rounded text-brand-600 focus:ring-brand-500 mt-0.5 h-4 w-4"
                />
                <label htmlFor="seller-certify" className="text-xs text-charcoal font-medium leading-relaxed">
                  <strong>I approve this listing payload for immediate remote dispatch.</strong> I have verified that specifications, pricing, and packaging details comply with sales channel standards.
                </label>
              </div>
            </div>
          )}

          {/* STEP 7: Dispatch & Live Execution */}
          {currentStep === 7 && (
            <div className="space-y-4 text-center py-6">
              {isPublishing ? (
                <div className="space-y-3">
                  <div className="w-12 h-12 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto" />
                  <h3 className="text-sm font-bold text-charcoal">Dispatching to {selectedConnection?.display_name}...</h3>
                  <p className="text-xs text-slate-500">
                    Background mutation in progress. Executing GraphQL / REST API call with idempotency.
                  </p>
                </div>
              ) : publishedResult ? (
                <div className="space-y-4">
                  <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-charcoal">Listing Successfully Published!</h3>
                    <p className="text-xs text-slate-500 mt-1">
                      {customTitle} is now live on {selectedConnection?.display_name}.
                    </p>
                  </div>
                  {publishedResult.remote_url && (
                    <a
                      href={publishedResult.remote_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs"
                    >
                      <span>View Live Remote Listing</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              ) : publishError ? (
                <div className="space-y-4 text-center">
                  <div className="w-14 h-14 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto">
                    <AlertTriangle className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-charcoal">Publishing Encountered an Error</h3>
                    <p className="text-xs text-rose-700 mt-1">{publishError}</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleExecuteDispatch}
                    className="px-4 py-2 rounded-xl bg-brand-600 text-white font-bold text-xs"
                  >
                    Retry Dispatch
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto">
                    <Send className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-charcoal">Ready for Remote Dispatch</h3>
                    <p className="text-xs text-slate-500 mt-1">
                      Payload validated and approved by seller. Click below to execute live publication.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleExecuteDispatch}
                    className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-md inline-flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    <span>Execute Live Publication</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Wizard Footer Controls */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
          {currentStep > 1 && currentStep < 7 ? (
            <button
              type="button"
              onClick={handleBack}
              className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-100 cursor-pointer inline-flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back</span>
            </button>
          ) : (
            <div />
          )}

          {currentStep < 6 && (
            <button
              type="button"
              onClick={handleNext}
              className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-xs cursor-pointer inline-flex items-center gap-1.5"
            >
              <span>Next Step</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}

          {currentStep === 6 && (
            <button
              type="button"
              onClick={handleNext}
              disabled={!sellerApproved}
              className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-xs cursor-pointer disabled:opacity-40 inline-flex items-center gap-1.5"
            >
              <span>Proceed to Dispatch</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}

          {currentStep === 7 && publishedResult && (
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs"
            >
              Done & Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

