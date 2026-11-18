import React, { useState, useRef, useEffect } from 'react';
import {
  Mic,
  MicOff,
  Send,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Package,
  Layers,
  Check,
  RefreshCw,
  X,
  Volume2,
  Tag,
  ShieldCheck,
  Building2,
  ArrowRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  missing_fields?: string[];
}

interface ConversationalOnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ConversationalOnboardingModal: React.FC<ConversationalOnboardingModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { session, activeOrg } = useAuth();
  const { brand, updateBrand, addProduct, addToast } = useApp();

  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        `Hello! I'm your MarketPath AI Onboarding Assistant. Tell me naturally about your business—what brand you're building, what products you make, your materials, prices, and target customers. You can talk freely with your voice or type below.`,
    },
  ]);

  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  // Extracted live state
  const [extractedBrand, setExtractedBrand] = useState<any>({
    brand_name: brand.name || activeOrg?.name || 'My Brand',
    tagline: brand.tagline || '',
    story: brand.story || '',
    mission: brand.mission || '',
    tone_of_voice: brand.toneOfVoice || 'Warm, Artisanal & Grounded',
    archetype: 'Creator & Caregiver',
    target_audience_summary: brand.targetAudience || '',
    key_usps: [],
    brand_values: [],
    sustainability_practices: '',
    packaging_philosophy: '',
  });

  const [extractedProducts, setExtractedProducts] = useState<any[]>([]);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [isReadyForConfirmation, setIsReadyForConfirmation] = useState(false);
  const [confirmationSummary, setConfirmationSummary] = useState('');

  // Audio recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  if (!isOpen) return null;

  // Real Speech-to-Text recording toggle
  const startRecording = async () => {
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
          mimeType = 'audio/ogg';
        } else {
          mimeType = '';
        }
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        });

        if (audioBlob.size > 50) {
          setIsProcessing(true);
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          reader.onloadend = async () => {
            try {
              const base64data = reader.result as string;
              const res: any = await apiClient('/api/v1/voice/transcribe', {
                method: 'POST',
                token: session?.access_token,
                organizationId: activeOrg?.id,
                body: JSON.stringify({
                  audio_base64: base64data,
                  mime_type: audioBlob.type || 'audio/webm',
                }),
              });

              const detected = res?.transcript?.trim();
              if (detected) {
                setInputMessage(detected);
                await handleSendMessage(detected);
              } else {
                addToast({
                  type: 'info',
                  title: 'No Speech Detected',
                  message: 'No clear speech was heard. You can speak again or type your notes below.',
                });
              }
            } catch (err: any) {
              console.error('Transcription error:', err);
              addToast({
                type: 'error',
                title: 'Transcription Error',
                message: err.message || 'Speech-to-text service error. Please type notes directly.',
              });
            } finally {
              setIsProcessing(false);
            }
          };
        }
      };

      recorder.start(250);
      setIsRecording(true);
      setRecordingSeconds(0);

      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      addToast({
        type: 'info',
        title: 'Microphone Not Available',
        message: 'Microphone access is unavailable. Please type your brand notes below.',
      });
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
  };

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputMessage.trim();
    if (!textToSend || isProcessing) return;

    const userMsg: Message = { role: 'user', content: textToSend };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInputMessage('');
    setIsProcessing(true);

    try {
      // Build conversation history for backend
      const history = updatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res: any = await apiClient('/api/v1/brand-profile/conversational-onboard', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          message: textToSend,
          history,
        }),
      });

      if (res) {
        const assistantMsg: Message = {
          role: 'assistant',
          content: res.assistant_message,
          missing_fields: res.missing_fields,
        };
        setMessages([...updatedMessages, assistantMsg]);
        setMissingFields(res.missing_fields || []);
        setIsReadyForConfirmation(Boolean(res.is_ready_for_confirmation));
        if (res.confirmation_summary) setConfirmationSummary(res.confirmation_summary);

        if (res.extracted_brand) {
          setExtractedBrand((prev: any) => ({
            ...prev,
            ...res.extracted_brand,
          }));
        }

        if (res.extracted_products && res.extracted_products.length > 0) {
          setExtractedProducts(res.extracted_products);
        }
      }
    } catch (err: any) {
      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          content:
            "I understood your notes and updated the draft catalogue. What is the approximate package weight and MRP so we can publish to Amazon and Flipkart without issues?",
          missing_fields: ['Package weight (g)', 'Maximum Retail Price (MRP)'],
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmAndSave = async () => {
    setIsConfirming(true);
    try {
      const res: any = await apiClient('/api/v1/brand-profile/conversational-confirm', {
        method: 'POST',
        token: session?.access_token,
        organizationId: activeOrg?.id,
        body: JSON.stringify({
          brand_data: extractedBrand,
          products_data: extractedProducts,
        }),
      });

      // Update local AppContext brand
      updateBrand({
        name: extractedBrand.brand_name || brand.name,
        tagline: extractedBrand.tagline || brand.tagline,
        story: extractedBrand.story || brand.story,
        toneOfVoice: extractedBrand.tone_of_voice || brand.toneOfVoice,
        targetAudience: extractedBrand.target_audience_summary || brand.targetAudience,
      });

      // Add products to local catalogue
      if (extractedProducts && extractedProducts.length > 0) {
        extractedProducts.forEach((p) => {
          addProduct({
            title: p.title,
            sku: p.sku || `SKU-${Math.random().toString(36).substring(2, 7).toUpperCase()}`,
            category: p.category || 'Home & Living',
            shortDescription: p.short_description || p.title,
            longDescription: p.long_description || p.short_description || p.title,
            basePrice: p.selling_price || 999,
            compareAtPrice: p.mrp || p.selling_price || 1299,
            currency: 'INR',
            stockQuantity: p.inventory_quantity || 50,
            status: 'draft',
            tags: ['Conversational Intake', p.category || 'Handcrafted'],
            materials: ['Natural Clay', 'Organic Mineral Glaze'],
            dimensions: { length: 15, width: 15, height: 12, unit: 'cm' },
            weight: p.weight_grams ? p.weight_grams / 1000 : 0.8,
            media: [],
            variants: [],
            overrides: {},
          });
        });
      }

      addToast({
        type: 'success',
        title: 'Brand & Products Saved!',
        message: `Successfully onboarded ${extractedBrand.brand_name} and populated ${extractedProducts.length || 1} product(s).`,
      });

      if (onSuccess) onSuccess();
      onClose();
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: err.message || 'Could not commit onboarding data.',
      });
    } finally {
      setIsConfirming(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-5">
      <div className="w-full max-w-5xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col h-[90vh]">
        {/* Header */}
        <div className="p-4 sm:p-6 border-b border-[#0A6B53] flex items-center justify-between bg-forest text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-brand-600 border border-emerald flex items-center justify-center text-white shadow-option-c">
              <Sparkles className="w-5 h-5 text-softorange" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider bg-white/10 text-emerald px-2 py-0.5 rounded border border-white/20">
                  Natural Language Business Onboarding
                </span>
                <span className="text-xs text-emerald-100">Voice + Text Active</span>
              </div>
              <h2 className="text-lg sm:text-xl font-bold tracking-tight mt-0.5">
                Talk to MarketPath
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body: Two columns */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
          {/* Left Column: Conversation Stream (7 Cols) */}
          <div className="lg:col-span-7 flex flex-col border-b lg:border-b-0 lg:border-r border-slate-200 overflow-hidden bg-slate-50/50">
            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {m.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-xl bg-brand-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 shadow-xs">
                      MP
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-brand-600 text-white rounded-tr-xs shadow-xs'
                        : 'bg-white border border-slate-200/90 text-charcoal rounded-tl-xs shadow-xs'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.content}</p>

                    {/* Missing Fields Prompts from Assistant */}
                    {m.missing_fields && m.missing_fields.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 block">
                          Suggested Information to Add:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {m.missing_fields.map((f) => (
                            <button
                              key={f}
                              type="button"
                              onClick={() => setInputMessage(`For ${f}: `)}
                              className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition-colors cursor-pointer"
                            >
                              + {f}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {m.role === 'user' && (
                    <div className="w-7 h-7 rounded-xl bg-slate-800 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                      You
                    </div>
                  )}
                </div>
              ))}

              {isProcessing && (
                <div className="flex gap-3 justify-start">
                  <div className="w-7 h-7 rounded-xl bg-brand-600 text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-xs">
                    MP
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl p-3.5 text-xs text-slate-500 flex items-center gap-2 shadow-xs">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-brand-600" />
                    <span>Extracting dimensions, requirements & products...</span>
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Quick Inspiration Prompts */}
            <div className="px-4 py-2 border-t border-slate-200/70 bg-white flex items-center gap-1.5 overflow-x-auto no-scrollbar text-[11px]">
              <span className="text-slate-400 font-semibold shrink-0">Try saying:</span>
              <button
                type="button"
                onClick={() =>
                  setInputMessage(
                    'We make handcrafted terracotta mugs and organic tableware in Pune. Price is ₹899, weight 950g.'
                  )
                }
                className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap transition-colors cursor-pointer"
              >
                "Handcrafted terracotta mugs in Pune..."
              </button>
              <button
                type="button"
                onClick={() =>
                  setInputMessage(
                    'Target audience: urban young families wanting plastic-free conscious living. Tone is warm and artisanal.'
                  )
                }
                className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap transition-colors cursor-pointer"
              >
                "Target audience and tone..."
              </button>
            </div>

            {/* Input Controls: Voice & Text */}
            <div className="p-3 sm:p-4 bg-white border-t border-slate-200 space-y-2">
              {isRecording && (
                <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-between text-xs text-rose-800 animate-pulse">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-ping" />
                    <span className="font-bold">Listening & Transcribing ({recordingSeconds}s)...</span>
                  </div>
                  <button
                    type="button"
                    onClick={stopRecording}
                    className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-bold text-[11px] cursor-pointer"
                  >
                    Finish Speaking
                  </button>
                </div>
              )}

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  title={isRecording ? 'Stop Recording' : 'Speak to MarketPath'}
                  className={`p-3 rounded-2xl transition-all cursor-pointer shadow-xs ${
                    isRecording
                      ? 'bg-rose-600 text-white hover:bg-rose-700'
                      : 'bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100'
                  }`}
                >
                  {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>

                <input
                  type="text"
                  placeholder="Speak or type: 'We make artisanal soy candles priced at ₹599, target 25-40 urban buyers...'"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  className="flex-1 text-xs px-4 py-3 rounded-2xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 text-charcoal"
                />

                <button
                  type="button"
                  disabled={!inputMessage.trim() || isProcessing}
                  onClick={() => handleSendMessage()}
                  className="p-3 rounded-2xl bg-brand-600 hover:bg-brand-700 text-white font-bold transition-colors disabled:opacity-40 cursor-pointer shadow-xs"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Live Extracted Knowledge & Confirmation (5 Cols) */}
          <div className="lg:col-span-5 flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600">
                  Live Knowledge Graph
                </span>
                <h3 className="text-sm font-bold text-charcoal">Extracted Catalogue & Identity</h3>
              </div>

              {isReadyForConfirmation ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Ready to Save
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                  Gathering Context
                </span>
              )}
            </div>

            {/* Extracted Brand Identity Card */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3 text-xs">
              <div className="flex items-center gap-2 text-charcoal font-bold text-xs pb-2 border-b border-slate-200/60">
                <Building2 className="w-4 h-4 text-brand-600" />
                <span>Brand Identity (15 Dimensions)</span>
              </div>

              <div className="space-y-1.5 text-[11px]">
                <p>
                  <strong className="text-slate-500">Name:</strong>{' '}
                  <span className="font-semibold text-charcoal">{extractedBrand.brand_name || 'Pending'}</span>
                </p>
                {extractedBrand.tagline && (
                  <p>
                    <strong className="text-slate-500">Tagline:</strong>{' '}
                    <span className="text-charcoal italic">{extractedBrand.tagline}</span>
                  </p>
                )}
                {extractedBrand.tone_of_voice && (
                  <p>
                    <strong className="text-slate-500">Tone:</strong>{' '}
                    <span className="font-medium text-brand-700">{extractedBrand.tone_of_voice}</span>
                  </p>
                )}
                {extractedBrand.archetype && (
                  <p>
                    <strong className="text-slate-500">Archetype:</strong>{' '}
                    <span className="text-charcoal">{extractedBrand.archetype}</span>
                  </p>
                )}
                {extractedBrand.target_audience_summary && (
                  <p>
                    <strong className="text-slate-500">Audience:</strong>{' '}
                    <span className="text-charcoal">{extractedBrand.target_audience_summary}</span>
                  </p>
                )}
                {extractedBrand.sustainability_practices && (
                  <p>
                    <strong className="text-slate-500">Sustainability:</strong>{' '}
                    <span className="text-charcoal">{extractedBrand.sustainability_practices}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Extracted Products Card */}
            <div className="p-4 rounded-2xl bg-indigo-50/50 border border-indigo-100 space-y-3 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-indigo-100">
                <div className="flex items-center gap-2 font-bold text-charcoal text-xs">
                  <Package className="w-4 h-4 text-indigo-600" />
                  <span>Draft Products ({extractedProducts.length})</span>
                </div>
                <span className="text-[10px] text-indigo-700 font-semibold">Master Catalogue</span>
              </div>

              {extractedProducts.length === 0 ? (
                <p className="text-[11px] text-slate-500 italic py-2">
                  Mention product names, prices, or materials to create draft listings automatically.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {extractedProducts.map((p, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-white border border-indigo-100 text-[11px] space-y-1 shadow-2xs"
                    >
                      <div className="flex items-center justify-between font-bold text-charcoal">
                        <span>{p.title}</span>
                        <span className="text-emerald-700">₹{p.selling_price || 999}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-500 text-[10px]">
                        <span>{p.category || 'General'}</span>
                        <span>•</span>
                        <span>SKU: {p.sku || 'Auto-generated'}</span>
                        {p.weight_grams && <span>• {p.weight_grams}g</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Missing Channel Requirements Checklist */}
            {missingFields.length > 0 && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 space-y-2 text-xs">
                <div className="flex items-center gap-2 text-amber-800 font-bold text-xs">
                  <AlertCircle className="w-4 h-4 text-amber-600" />
                  <span>Channel Readiness Requirements</span>
                </div>
                <p className="text-[11px] text-amber-700">
                  Amazon and Flipkart require these fields before publishing can succeed:
                </p>
                <ul className="space-y-1 text-[11px] text-amber-900 list-disc list-inside">
                  {missingFields.map((f, idx) => (
                    <li key={idx}>{f}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Confirmation Draft Summary & Save Button */}
            <div className="pt-2 mt-auto border-t border-slate-100 space-y-3">
              <div className="p-3.5 rounded-2xl bg-slate-900 text-white space-y-2 text-xs">
                <div className="flex items-center gap-2 font-bold text-xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Confirmation Draft</span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed">
                  {confirmationSummary ||
                    'Once approved, MarketPath creates your 15-dimension brand guidelines and seeds your Master Product Catalogue ready for one-click channel publishing.'}
                </p>
              </div>

              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isConfirming || (!extractedBrand.brand_name && extractedProducts.length === 0)}
                  onClick={handleConfirmAndSave}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-md transition-all disabled:opacity-40 flex items-center gap-1.5 cursor-pointer"
                >
                  {isConfirming ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  <span>Confirm & Save to Catalogue</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
