import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
  Trash2,
  Plus,
  Loader2,
  AlertCircle,
  Image as ImageIcon,
  Truck,
  ShieldCheck,
  Scale,
  Mic,
  MicOff,
  FileText,
  HelpCircle,
} from 'lucide-react';
import { D2C_CATEGORIES } from '../public/SignupPage';
import { VoiceIntakeWidget } from '../../components/common/VoiceIntakeWidget';

type IntakeMode = 'voice' | 'text' | 'form';

interface VariantForm {
  sku: string;
  title: string;
  price: number;
  stockQuantity: number;
  optionKey: string;
  optionValue: string;
}

export const AddProductPage: React.FC = () => {
  const navigate = useNavigate();
  const { session, activeOrg, role } = useAuth();
  const { addToast } = useApp();

  // Mode Selection
  const [intakeMode, setIntakeMode] = useState<IntakeMode>('form');
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Voice Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [rawTranscript, setRawTranscript] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<any>(null);

  // Text Intake State
  const [rawTextInput, setRawTextInput] = useState('');

  // AI Extraction Feedback
  const [extractionAlert, setExtractionAlert] = useState<{
    confidence: number;
    missing: string[];
  } | null>(null);

  // Master Form State
  const [formData, setFormData] = useState({
    title: '',
    sku: '',
    category: 'Home & Living / Decor',
    shortDescription: '',
    longDescription: '',
    basePrice: 999,
    compareAtPrice: 1299,
    costPrice: 350,
    currency: 'INR',
    stockQuantity: 25,
    materialsText: 'Terracotta Clay, Food-Safe Glaze',
    length: 15,
    width: 12,
    height: 10,
    unit: 'cm',
    weight: 0.5,
    tagsText: 'artisanal, handmade, sustainable',
    mediaUrl: 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=800&auto=format&fit=crop&q=80',
    mediaPublicId: 'sample_product_01',
  });

  // Category attributes
  const [categorySpecs, setCategorySpecs] = useState({
    materialFinish: 'Raw Terracotta & Mineral Glaze',
    roomPlacement: 'Living & Dining',
    fragile: true,
    careInstructions: 'Wipe with soft damp cloth. Avoid harsh chemical cleaners.',
  });

  // Packaging and Shipping specs
  const [packagingData, setPackagingData] = useState({
    boxLength: 18,
    boxWidth: 15,
    boxHeight: 14,
    boxUnit: 'cm',
    deadWeightGrams: 650,
    packagingMaterial: '5-Ply Recycled Corrugated Box',
    protectivePackaging: 'Biodegradable Honeycomb Paper Wrap',
    moq: 1,
    hsnCode: '69120010',
    complianceCertificates: ['Lead-Free Food Safe', 'Plastic-Free Packaging'],
  });

  const [variants, setVariants] = useState<VariantForm[]>([
    {
      sku: '',
      title: 'Standard',
      price: 999,
      stockQuantity: 25,
      optionKey: 'Finish',
      optionValue: 'Natural',
    },
  ]);

  // Compute volumetric weight in kg: (L * W * H) / 5000
  const volumetricWeightKg = (
    (packagingData.boxLength * packagingData.boxWidth * packagingData.boxHeight) /
    5000
  ).toFixed(3);

  // Voice recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordDuration(0);

      timerRef.current = setInterval(() => {
        setRecordDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      addToast({
        type: 'info',
        title: 'Microphone Simulation Active',
        message: 'You can speak or type your product details directly into the transcript box.',
      });
      setIsRecording(true);
      timerRef.current = setInterval(() => {
        setRecordDuration((prev) => prev + 1);
      }, 1000);
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  // Process voice audio / transcript
  const handleExtractFromVoice = async (customText?: string) => {
    const textToExtract = (customText || rawTranscript).trim();
    if (!textToExtract) return;
    setIsExtracting(true);
    setErrorMessage(null);

    try {
      const res = await apiClient('/api/v1/voice/extract-product', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          transcript: textToExtract,
          category_hint: formData.category,
        }),
      });

      populateFromDraft(res);
      addToast({
        type: 'success',
        title: 'Voice Specifications Extracted!',
        message: `Extracted ${res.title} and populated specifications table.`,
      });
      setIntakeMode('form');
      setCurrentStep(1);
    } catch (err: any) {
      setErrorMessage(err.message || 'Voice extraction failed.');
      addToast({ type: 'error', title: 'Extraction Error', message: err.message });
    } finally {
      setIsExtracting(false);
    }
  };

  // Process text input
  const handleExtractFromText = async () => {
    if (!rawTextInput.trim()) return;
    setIsExtracting(true);
    setErrorMessage(null);

    try {
      const res = await apiClient('/api/v1/products/extract-from-text', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          text: rawTextInput.trim(),
          category_hint: formData.category,
        }),
      });

      populateFromDraft(res);
      addToast({
        type: 'success',
        title: 'Product Notes Extracted!',
        message: `Extracted specifications for ${res.title}.`,
      });
      setIntakeMode('form');
      setCurrentStep(1);
    } catch (err: any) {
      setErrorMessage(err.message || 'Text extraction failed.');
      addToast({ type: 'error', title: 'Extraction Error', message: err.message });
    } finally {
      setIsExtracting(false);
    }
  };

  const populateFromDraft = (draft: any) => {
    const generatedSku = formData.sku || `SKU-${(draft.title || 'PRD').substring(0, 3).toUpperCase()}-${Math.floor(100 + Math.random() * 900)}`;

    setFormData((prev) => ({
      ...prev,
      title: draft.title || prev.title,
      sku: generatedSku,
      category: draft.category || prev.category,
      shortDescription: draft.short_description || prev.shortDescription,
      longDescription: draft.long_description || prev.longDescription,
      basePrice: draft.base_price || prev.basePrice,
      compareAtPrice: draft.compare_at_price || prev.compareAtPrice,
      costPrice: draft.cost_price || prev.costPrice,
      materialsText: draft.materials?.length ? draft.materials.join(', ') : prev.materialsText,
      tagsText: draft.tags?.length ? draft.tags.join(', ') : prev.tagsText,
      weight: draft.weight_kg || prev.weight,
      length: draft.dimensions_cm?.length || prev.length,
      width: draft.dimensions_cm?.width || prev.width,
      height: draft.dimensions_cm?.height || prev.height,
    }));

    if (draft.category_attributes) {
      setCategorySpecs((prev) => ({
        ...prev,
        materialFinish: draft.category_attributes.material_finish || prev.materialFinish,
        careInstructions: draft.category_attributes.care_instructions || prev.careInstructions,
        fragile: draft.category_attributes.fragile ?? prev.fragile,
      }));
    }

    if (draft.packaging_specs) {
      setPackagingData((prev) => ({
        ...prev,
        boxLength: draft.packaging_specs.box_length || prev.boxLength,
        boxWidth: draft.packaging_specs.box_width || prev.boxWidth,
        boxHeight: draft.packaging_specs.box_height || prev.boxHeight,
        deadWeightGrams: draft.packaging_specs.dead_weight_grams || prev.deadWeightGrams,
        packagingMaterial: draft.packaging_specs.packaging_material || prev.packagingMaterial,
      }));
    }

    if (draft.suggested_variants && draft.suggested_variants.length > 0) {
      setVariants(
        draft.suggested_variants.map((v: any, idx: number) => ({
          sku: `${generatedSku}-V${idx + 1}`,
          title: v.title || `Variant ${idx + 1}`,
          price: v.price || draft.base_price || 999,
          stockQuantity: v.stock_quantity || 20,
          optionKey: v.option_key || 'Option',
          optionValue: v.option_value || 'Default',
        }))
      );
    }

    setExtractionAlert({
      confidence: draft.confidence_score || 0.92,
      missing: draft.missing_marketplace_fields || [],
    });
  };

  const handleAddVariant = () => {
    setVariants([
      ...variants,
      {
        sku: `${formData.sku || 'SKU'}-V${variants.length + 1}`,
        title: `Variant ${variants.length + 1}`,
        price: formData.basePrice,
        stockQuantity: 10,
        optionKey: 'Color',
        optionValue: 'Natural',
      },
    ]);
  };

  const handleRemoveVariant = (index: number) => {
    setVariants(variants.filter((_, i) => i !== index));
  };

  const toggleCertificate = (cert: string) => {
    if (packagingData.complianceCertificates.includes(cert)) {
      setPackagingData({
        ...packagingData,
        complianceCertificates: packagingData.complianceCertificates.filter((c) => c !== cert),
      });
    } else {
      setPackagingData({
        ...packagingData,
        complianceCertificates: [...packagingData.complianceCertificates, cert],
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
      return;
    }

    if (!formData.title || !formData.sku) {
      setErrorMessage('Product title and SKU are required.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const payload = {
      sku: formData.sku.trim(),
      title: formData.title.trim(),
      category: formData.category,
      short_description: formData.shortDescription.trim(),
      long_description: formData.longDescription.trim(),
      status: 'active',
      base_price: Number(formData.basePrice),
      compare_at_price: formData.compareAtPrice ? Number(formData.compareAtPrice) : null,
      cost_price: formData.costPrice ? Number(formData.costPrice) : null,
      currency: formData.currency,
      stock_quantity: Number(formData.stockQuantity),
      materials: formData.materialsText.split(',').map((m) => m.trim()).filter(Boolean),
      dimensions: {
        length: Number(formData.length),
        width: Number(formData.width),
        height: Number(formData.height),
        unit: formData.unit,
      },
      weight: formData.weight ? Number(formData.weight) : null,
      tags: formData.tagsText.split(',').map((t) => t.trim()).filter(Boolean),
      category_attributes: {
        ...categorySpecs,
        hsn_code: packagingData.hsnCode,
      },
      packaging_specs: {
        box_length: Number(packagingData.boxLength),
        box_width: Number(packagingData.boxWidth),
        box_height: Number(packagingData.boxHeight),
        box_unit: packagingData.boxUnit,
        dead_weight_grams: Number(packagingData.deadWeightGrams),
        volumetric_weight_grams: Math.round(Number(volumetricWeightKg) * 1000),
        packaging_material: packagingData.packagingMaterial,
        protective_packaging: packagingData.protectivePackaging,
      },
      shipping_specs: {
        fragile: categorySpecs.fragile,
        stackable: true,
      },
      moq: Number(packagingData.moq) || 1,
      compliance_certificates: packagingData.complianceCertificates,
      media: formData.mediaUrl
        ? [
            {
              cloudinary_public_id: formData.mediaPublicId || 'product_img_01',
              media_url: formData.mediaUrl,
              media_type: 'image',
              alt_text: formData.title,
              display_order: 0,
            },
          ]
        : [],
      variants: variants.map((v, idx) => ({
        sku: v.sku.trim() || `${formData.sku}-V${idx + 1}`,
        title: v.title.trim() || 'Standard',
        price: Number(v.price),
        stock_quantity: Number(v.stockQuantity),
        options: { [v.optionKey]: v.optionValue },
      })),
    };

    try {
      const created = await apiClient('/api/v1/products', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify(payload),
      });

      addToast({
        type: 'success',
        title: 'Master SKU Initialized!',
        message: `${created.sku} created with category specs & packaging dimensions.`,
      });
      navigate(`/app/products/${created.id}`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save master product record.');
      addToast({
        type: 'error',
        title: 'Product Creation Failed',
        message: err.message || 'Could not save product.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
        <Link
          to="/app/products"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-charcoal transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Master Catalogue</span>
        </Link>
        <span className="text-xs font-bold text-brand-600 uppercase tracking-wider">
          Master Product Intake
        </span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight">
          Create Master Product & SKUs
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Define physical specifications, packaging compliance, and variant options once.
        </p>
      </div>

      {/* Intake Mode Switcher */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-1.5 bg-softbeige rounded-2xl border border-bordergrey">
        <button
          type="button"
          onClick={() => setIntakeMode('voice')}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            intakeMode === 'voice'
              ? 'bg-purewhite text-forest shadow-xs ring-1 ring-bordergrey'
              : 'text-mutedgrey hover:text-charcoal hover:bg-warmwhite'
          }`}
        >
          <Mic className="w-4 h-4 text-brand-600" />
          <span>Speak (Voice Intake)</span>
        </button>

        <button
          type="button"
          onClick={() => setIntakeMode('text')}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            intakeMode === 'text'
              ? 'bg-purewhite text-forest shadow-xs ring-1 ring-bordergrey'
              : 'text-mutedgrey hover:text-charcoal hover:bg-warmwhite'
          }`}
        >
          <FileText className="w-4 h-4 text-brand-600" />
          <span>Paste Notes (Text Intake)</span>
        </button>

        <button
          type="button"
          onClick={() => setIntakeMode('form')}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            intakeMode === 'form'
              ? 'bg-purewhite text-forest shadow-xs ring-1 ring-bordergrey'
              : 'text-mutedgrey hover:text-charcoal hover:bg-warmwhite'
          }`}
        >
          <Package className="w-4 h-4 text-brand-600" />
          <span>Structured Form</span>
        </button>
      </div>

      {/* Voice Mode Panel */}
      {intakeMode === 'voice' && (
        <div className="space-y-4">
          <VoiceIntakeWidget
            title="Speak Your Product Specifications"
            subtitle="Tell us about the item's title, materials, dimensions, packed weight, prices (selling & MRP), and available colors or sizes. AI will listen and structure your catalogue record."
            placeholder="Spoken words will appear here verbatim. You can review or edit before extracting into your master catalogue..."
            extractButtonLabel="Extract to Master Draft"
            initialTranscript={rawTranscript}
            onTranscribeComplete={(t) => setRawTranscript(t)}
            onExtractClick={(t) => {
              setRawTranscript(t);
              handleExtractFromVoice(t);
            }}
            isExtracting={isExtracting}
          />
        </div>
      )}

      {/* Text Mode Panel */}
      {intakeMode === 'text' && (
        <div className="p-6 rounded-3xl bg-forest text-white space-y-5 shadow-option-c border border-[#0A6B53]">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald" />
            <h2 className="text-base font-bold">Paste Raw Notes or WhatsApp Descriptions</h2>
          </div>
          <p className="text-xs text-emerald-100">
            Paste raw text from supplier invoices, notebook notes, or maker messages. AI extracts dimensions, weights, prices, and variant matrix.
          </p>

          <div>
            <textarea
              rows={5}
              placeholder="e.g. Scented Soy Candle Set in amber jar. 8x8x10 cm, 400g weight. ₹749 selling price, ₹999 MRP. Fragrances: Himalayan Cedar and Madurai Jasmine. Packed in recycled kraft cylinder box..."
              value={rawTextInput}
              onChange={(e) => setRawTextInput(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 rounded-xl bg-[#042D24] border border-[#0A6B53] text-white focus:outline-none focus:ring-2 focus:ring-brand-500 leading-relaxed font-sans"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setIntakeMode('form')}
              className="px-4 py-2.5 rounded-xl border border-[#0A6B53] text-xs font-semibold text-emerald-100 hover:text-white cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={isExtracting || !rawTextInput.trim()}
              onClick={handleExtractFromText}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-emerald text-white font-bold text-xs disabled:opacity-50 inline-flex items-center gap-2 cursor-pointer transition-colors"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Extracting Specifications...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Extract to Master Draft</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Extraction Warning / Confidence Banner */}
      {extractionAlert && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Extracted into Master Draft (Confidence: {(extractionAlert.confidence * 100).toFixed(0)}%)</span>
            </div>
            <span className="text-[11px] text-amber-800">
              {extractionAlert.missing.length === 0 ? 'Marketplace Ready' : 'Attention Needed'}
            </span>
          </div>

          {extractionAlert.missing.length > 0 && (
            <div className="text-[11px] space-y-1 text-amber-800">
              <span className="font-semibold">Missing Marketplace Requirements:</span>
              <ul className="list-disc list-inside space-y-0.5 text-[10px]">
                {extractionAlert.missing.map((m, idx) => (
                  <li key={idx}>{m}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Form Wizard Navigation */}
      <div className="flex items-center justify-between p-4 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {[
          { step: 1, title: 'Identity & Specs', desc: 'Title, category & dimensions' },
          { step: 2, title: 'Variants & Stock', desc: 'SKU matrix & pricing' },
          { step: 3, title: 'Packaging & Review', desc: 'Logistics & compliance' },
        ].map((s) => (
          <button
            key={s.step}
            type="button"
            onClick={() => setCurrentStep(s.step)}
            className={`flex items-center gap-3 text-left transition-all cursor-pointer ${
              currentStep === s.step ? 'opacity-100' : 'opacity-60 hover:opacity-90'
            }`}
          >
            <div
              className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold ${
                currentStep === s.step
                  ? 'bg-brand-600 text-white'
                  : currentStep > s.step
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {currentStep > s.step ? <CheckCircle2 className="w-4 h-4" /> : s.step}
            </div>
            <div className="hidden sm:block">
              <div className="text-xs font-bold text-charcoal">{s.title}</div>
              <div className="text-[10px] text-slate-500">{s.desc}</div>
            </div>
          </button>
        ))}
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Multi-Step Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* STEP 1: Basic Details & Physical Specs */}
        {currentStep === 1 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-6">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Package className="w-5 h-5 text-brand-600" />
              <div>
                <h3 className="text-sm font-bold text-charcoal">1. Master Product Identity & Physical Specifications</h3>
                <p className="text-xs text-slate-500">Immutable product source of truth.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-charcoal mb-1">Product Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Artisanal Terracotta Vase"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Master SKU *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ATL-VASE-01"
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono uppercase"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Category *</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {D2C_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                  <option value="Home & Living / Decor">Home & Living / Decor</option>
                  <option value="Kitchen & Dining">Kitchen & Dining</option>
                  <option value="Home Fragrance & Living">Home Fragrance & Living</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Materials (Comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g. Terracotta Clay, Mineral Glaze"
                  value={formData.materialsText}
                  onChange={(e) => setFormData({ ...formData, materialsText: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Short Description (Punchy summary)</label>
              <input
                type="text"
                placeholder="Hand-thrown terracotta vase with natural mineral wash finish."
                value={formData.shortDescription}
                onChange={(e) => setFormData({ ...formData, shortDescription: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-charcoal mb-1">Long Description & Story</label>
              <textarea
                rows={3}
                placeholder="Detailed craftsmanship narrative and origin..."
                value={formData.longDescription}
                onChange={(e) => setFormData({ ...formData, longDescription: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 leading-relaxed"
              />
            </div>

            {/* Physical Dimensions */}
            <div className="pt-2 border-t border-slate-100">
              <label className="block text-xs font-semibold text-charcoal mb-2">
                Unpacked Unit Dimensions & Weight
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <span className="text-[10px] text-slate-500">Length (cm)</span>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.length}
                    onChange={(e) => setFormData({ ...formData, length: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Width (cm)</span>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.width}
                    onChange={(e) => setFormData({ ...formData, width: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Height (cm)</span>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.height}
                    onChange={(e) => setFormData({ ...formData, height: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Weight (kg)</span>
                  <input
                    type="number"
                    step="0.05"
                    value={formData.weight}
                    onChange={(e) => setFormData({ ...formData, weight: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
              </div>
            </div>

            {/* Media URL */}
            <div className="pt-2 border-t border-slate-100">
              <label className="block text-xs font-semibold text-charcoal mb-1">Primary Product Image URL</label>
              <div className="flex items-center gap-3">
                <input
                  type="url"
                  placeholder="https://..."
                  value={formData.mediaUrl}
                  onChange={(e) => setFormData({ ...formData, mediaUrl: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                {formData.mediaUrl && (
                  <img
                    src={formData.mediaUrl}
                    alt="Preview"
                    className="w-10 h-10 rounded-xl object-cover border border-slate-200 shrink-0"
                  />
                )}
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: Variants, Pricing & Stock */}
        {currentStep === 2 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-6">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Layers className="w-5 h-5 text-brand-600" />
              <div>
                <h3 className="text-sm font-bold text-charcoal">2. Pricing, Inventory & Variant Options</h3>
                <p className="text-xs text-slate-500">Configure base price, MRP, and SKU variations.</p>
              </div>
            </div>

            {/* Pricing Section */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Selling Price (₹) *</label>
                <input
                  type="number"
                  required
                  value={formData.basePrice}
                  onChange={(e) => setFormData({ ...formData, basePrice: Number(e.target.value) })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">MRP (₹) *</label>
                <input
                  type="number"
                  required
                  value={formData.compareAtPrice}
                  onChange={(e) => setFormData({ ...formData, compareAtPrice: Number(e.target.value) })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                <span className="text-[10px] text-slate-400">Mandatory for Amazon & Flipkart</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">
                  Cost Price (₹) {role === 'viewer' && '(Hidden)'}
                </label>
                <input
                  type="number"
                  disabled={role === 'viewer'}
                  value={formData.costPrice}
                  onChange={(e) => setFormData({ ...formData, costPrice: Number(e.target.value) })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-100"
                />
                <span className="text-[10px] text-slate-400">Restricted to Admin & Owner</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Master Stock Quantity</label>
                <input
                  type="number"
                  value={formData.stockQuantity}
                  onChange={(e) => setFormData({ ...formData, stockQuantity: Number(e.target.value) })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            {/* Variants Table */}
            <div className="pt-4 border-t border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-charcoal">Product Variants & Child SKUs</h4>
                  <p className="text-[11px] text-slate-500">Each variant combination generates an individual barcode / SKU.</p>
                </div>
                <button
                  type="button"
                  onClick={handleAddVariant}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-charcoal text-xs font-semibold transition-colors cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Variant</span>
                </button>
              </div>

              <div className="space-y-2">
                {variants.map((v, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row items-stretch sm:items-center gap-3"
                  >
                    <div className="flex-1">
                      <span className="text-[10px] text-slate-500">Variant Title</span>
                      <input
                        type="text"
                        placeholder="e.g. Matte Ochre"
                        value={v.title}
                        onChange={(e) => {
                          const updated = [...variants];
                          updated[idx].title = e.target.value;
                          setVariants(updated);
                        }}
                        className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                      />
                    </div>

                    <div className="w-36">
                      <span className="text-[10px] text-slate-500">SKU</span>
                      <input
                        type="text"
                        placeholder={`${formData.sku}-V${idx + 1}`}
                        value={v.sku}
                        onChange={(e) => {
                          const updated = [...variants];
                          updated[idx].sku = e.target.value;
                          setVariants(updated);
                        }}
                        className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white font-mono uppercase"
                      />
                    </div>

                    <div className="w-24">
                      <span className="text-[10px] text-slate-500">Option Key</span>
                      <input
                        type="text"
                        placeholder="Finish"
                        value={v.optionKey}
                        onChange={(e) => {
                          const updated = [...variants];
                          updated[idx].optionKey = e.target.value;
                          setVariants(updated);
                        }}
                        className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                      />
                    </div>

                    <div className="w-24">
                      <span className="text-[10px] text-slate-500">Option Value</span>
                      <input
                        type="text"
                        placeholder="Ochre"
                        value={v.optionValue}
                        onChange={(e) => {
                          const updated = [...variants];
                          updated[idx].optionValue = e.target.value;
                          setVariants(updated);
                        }}
                        className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                      />
                    </div>

                    <div className="w-20">
                      <span className="text-[10px] text-slate-500">Price (₹)</span>
                      <input
                        type="number"
                        value={v.price}
                        onChange={(e) => {
                          const updated = [...variants];
                          updated[idx].price = Number(e.target.value);
                          setVariants(updated);
                        }}
                        className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                      />
                    </div>

                    <div className="w-16">
                      <span className="text-[10px] text-slate-500">Stock</span>
                      <input
                        type="number"
                        value={v.stockQuantity}
                        onChange={(e) => {
                          const updated = [...variants];
                          updated[idx].stockQuantity = Number(e.target.value);
                          setVariants(updated);
                        }}
                        className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                      />
                    </div>

                    {variants.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveVariant(idx)}
                        className="p-2 text-slate-400 hover:text-rose-600 transition-colors self-end sm:self-center cursor-pointer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Packaging & Compliance */}
        {currentStep === 3 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-6">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Truck className="w-5 h-5 text-brand-600" />
              <div>
                <h3 className="text-sm font-bold text-charcoal">3. Packaging Dimensions, Logistics & Compliance</h3>
                <p className="text-xs text-slate-500">Mandatory attributes required by Amazon Easy Ship, Flipkart & Delhivery.</p>
              </div>
            </div>

            {/* Packaging Box Dimensions */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-charcoal">
                  Packed Shipping Box Dimensions (Outer Carton)
                </label>
                <span className="text-[11px] font-bold text-forest">
                  Volumetric Weight: {volumetricWeightKg} kg
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <span className="text-[10px] text-slate-500">Box Length (cm) *</span>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={packagingData.boxLength}
                    onChange={(e) => setPackagingData({ ...packagingData, boxLength: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Box Width (cm) *</span>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={packagingData.boxWidth}
                    onChange={(e) => setPackagingData({ ...packagingData, boxWidth: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Box Height (cm) *</span>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={packagingData.boxHeight}
                    onChange={(e) => setPackagingData({ ...packagingData, boxHeight: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500">Dead Weight (Grams) *</span>
                  <input
                    type="number"
                    required
                    value={packagingData.deadWeightGrams}
                    onChange={(e) => setPackagingData({ ...packagingData, deadWeightGrams: Number(e.target.value) })}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Packaging Material</label>
                <input
                  type="text"
                  value={packagingData.packagingMaterial}
                  onChange={(e) => setPackagingData({ ...packagingData, packagingMaterial: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">HSN Tax Code</label>
                <input
                  type="text"
                  placeholder="e.g. 69120010"
                  value={packagingData.hsnCode}
                  onChange={(e) => setPackagingData({ ...packagingData, hsnCode: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-mono"
                />
              </div>
            </div>

            {/* Fragile & Compliance */}
            <div className="pt-2 border-t border-slate-100 space-y-3">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="fragileCheck"
                  checked={categorySpecs.fragile}
                  onChange={(e) => setCategorySpecs({ ...categorySpecs, fragile: e.target.checked })}
                  className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="fragileCheck" className="text-xs font-semibold text-charcoal cursor-pointer">
                  Item is fragile and requires special handling labels & air cushioning
                </label>
              </div>

              <div>
                <span className="block text-xs font-semibold text-charcoal mb-2">Compliance & Certifications</span>
                <div className="flex items-center gap-2 flex-wrap">
                  {[
                    'Lead-Free Food Safe',
                    'Zero-Plastic Packaging',
                    'OEKO-TEX Certified Linen',
                    'FSSAI Food Tested',
                    '100% Vegan & Phthalate Free',
                  ].map((cert) => {
                    const isChecked = packagingData.complianceCertificates.includes(cert);
                    return (
                      <button
                        key={cert}
                        type="button"
                        onClick={() => toggleCertificate(cert)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                          isChecked
                            ? 'bg-brand-50 text-brand-700 border-brand-300 ring-1 ring-brand-200'
                            : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        {cert}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Wizard Controls */}
        <div className="flex items-center justify-between pt-2">
          {currentStep > 1 ? (
            <button
              type="button"
              onClick={() => setCurrentStep(currentStep - 1)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-200 text-charcoal font-semibold text-xs hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Previous Step</span>
            </button>
          ) : (
            <div />
          )}

          {currentStep < 3 ? (
            <button
              type="button"
              onClick={() => setCurrentStep(currentStep + 1)}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-md transition-colors cursor-pointer"
            >
              <span>Continue</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-7 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-extrabold text-xs shadow-md transition-all disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving to Master Catalogue...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Create Master Product</span>
                </>
              )}
            </button>
          )}
        </div>
      </form>
    </div>
  );
};
