import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { MessageSquare, X, Send, Sparkles, AlertCircle, ExternalLink, RefreshCw, Bot, ChevronDown, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  suggested_actions?: Array<{ label: string; action_url: string }>;
  diagnosed_issues?: string[];
  data_sources?: string[];
  timestamp: string;
}

export const FloatingAIChatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: "Hi there! I'm your MarketPath AI assistant. I can diagnose marketplace listing issues (Amazon, Flipkart), explain channel sync status, or help you navigate your catalogue. How can I help you today?",
      suggested_actions: [
        { label: "Why did my Amazon listing fail?", action_url: "" },
        { label: "Why is Flipkart missing attributes?", action_url: "" },
        { label: "How does inventory sync work?", action_url: "" },
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const location = useLocation();
  const navigate = useNavigate();
  const { user, session, activeOrg } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isPublicMode = !user || !activeOrg?.id || !location.pathname.startsWith('/app');

  useEffect(() => {
    let isCancelled = false;

    const loadHistory = async () => {
      if (isPublicMode) {
        setMessages([
          {
            id: 'welcome',
            sender: 'bot',
            text: "Hi there! I'm the MarketPath AI Assistant. I can help you learn about our commerce operating platform, supported channels (Shopify, Amazon, Flipkart, Instagram), or help you schedule a Free Consultation. What would you like to know?",
            suggested_actions: [
              { label: "What channels are supported?", action_url: "/#channels" },
              { label: "How does MarketPath work?", action_url: "/about#how-it-works" },
              { label: "How do I book a consultation?", action_url: "/free-consultation" },
            ],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
        return;
      }

      // Authenticated mode: Load persistent conversation history from backend database
      try {
        const authToken = session?.access_token || localStorage.getItem('marketpath_auth_token') || undefined;
        const authOrgId = activeOrg?.id || localStorage.getItem('marketpath_active_org_id') || undefined;
        const res = await apiClient<{ messages: Message[] }>('/api/v1/support/chat/history', {
          token: authToken,
          organizationId: authOrgId,
        });

        if (!isCancelled && res.messages && res.messages.length > 0) {
          setMessages(res.messages);
          return;
        }
      } catch (err) {
        // Fallback to initial prompt if no previous history
      }

      if (!isCancelled) {
        setMessages([
          {
            id: 'welcome',
            sender: 'bot',
            text: "Hi there! I'm your MarketPath AI operational assistant. I can diagnose marketplace listing issues (Amazon, Flipkart), explain channel sync status, or help you navigate your catalogue. How can I help you today?",
            suggested_actions: [
              { label: "Why did my Amazon listing fail?", action_url: "/app/publishing" },
              { label: "Why is Flipkart missing attributes?", action_url: "/app/products" },
              { label: "How does inventory sync work?", action_url: "/app/orders" },
            ],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    };

    loadHistory();

    return () => {
      isCancelled = true;
    };
  }, [user?.id, activeOrg?.id, isPublicMode, session?.access_token]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (userText?: string) => {
    const textToSend = (userText || input).trim();
    if (!textToSend || isLoading) return;

    const userMsg: Message = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!userText) setInput('');
    setIsLoading(true);

    try {
      const history = messages
        .filter((m) => m.id !== 'welcome')
        .slice(-6)
        .map((m) => ({
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.text,
        }));

      const endpoint = isPublicMode ? '/api/v1/support/public-chat' : '/api/v1/support/chat';
      const authToken = isPublicMode ? undefined : (session?.access_token || localStorage.getItem('marketpath_auth_token') || undefined);
      const authOrgId = isPublicMode ? undefined : (activeOrg?.id || localStorage.getItem('marketpath_active_org_id') || undefined);

      const res = await apiClient<any>(endpoint, {
        method: 'POST',
        token: authToken,
        organizationId: authOrgId,
        body: JSON.stringify({
          message: textToSend,
          current_page: location.pathname,
          history,
        }),
      });

      const botMsg: Message = {
        id: `bot_${Date.now()}`,
        sender: 'bot',
        text: res.answer,
        suggested_actions: res.suggested_actions || [],
        diagnosed_issues: res.diagnosed_issues || [],
        data_sources: res.data_sources_used || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errMsg: Message = {
        id: `err_${Date.now()}`,
        sender: 'bot',
        text: "I encountered an issue connecting to the MarketPath diagnostic engine. Please make sure you are signed in or try asking your question again in a moment.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionClick = (action: { label: string; action_url: string }) => {
    if (action.action_url) {
      navigate(action.action_url);
      setIsOpen(false);
    } else {
      handleSendMessage(action.label);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Floating Toggle Button (Option C Styled) */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2.5 px-4.5 py-3 rounded-full bg-brand-600 hover:bg-forest text-white shadow-option-c-lg hover:shadow-2xl transition-all hover:scale-105 cursor-pointer font-bold text-sm group"
          title="Open MarketPath AI Assistant"
        >
          <div className="relative">
            <Bot className="w-5 h-5 text-white" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-softorange rounded-full border-2 border-brand-600 animate-pulse"></span>
          </div>
          <span>AI Assistant</span>
        </button>
      )}

      {/* Chat Window Panel (Option C Styled) */}
      {isOpen && (
        <div className="w-[380px] sm:w-[420px] h-[550px] max-h-[85vh] bg-white rounded-3xl shadow-option-c-lg border border-bordergrey flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="p-4 bg-forest text-white flex items-center justify-between border-b border-forest-deep">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-emerald" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  MarketPath Assistant
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-emerald font-mono font-bold">
                    Context-Aware
                  </span>
                </h3>
                <p className="text-[11px] text-slate-300 truncate max-w-[220px]">
                  Scope: <span className="text-white font-mono">{isPublicMode ? 'Public Website' : location.pathname}</span>
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 text-sm bg-warmwhite">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                    m.sender === 'user'
                      ? 'bg-brand-600 text-white rounded-br-none shadow-xs'
                      : 'bg-white text-charcoal border border-bordergrey rounded-bl-none shadow-xs'
                  }`}
                >
                  <div className="whitespace-pre-line text-xs sm:text-[13px] leading-relaxed">
                    {m.text}
                  </div>

                  {/* Diagnosed Issues Box */}
                  {m.diagnosed_issues && m.diagnosed_issues.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-bordergrey text-[11px] text-softorange-800 bg-softorange-50 p-2.5 rounded-xl border border-softorange-200">
                      <div className="font-bold flex items-center gap-1 mb-1 text-softorange-700">
                        <AlertCircle className="w-3.5 h-3.5" /> Diagnosed Requirement:
                      </div>
                      <ul className="list-disc pl-4 space-y-0.5 text-charcoal">
                        {m.diagnosed_issues.map((issue, idx) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Action Link Buttons */}
                  {m.suggested_actions && m.suggested_actions.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-bordergrey flex flex-wrap gap-1.5">
                      {m.suggested_actions.map((act, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleActionClick(act)}
                          className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-softbeige hover:bg-brand-50 hover:text-forest text-charcoal border border-bordergrey transition-colors flex items-center gap-1 cursor-pointer"
                        >
                          {act.label}
                          {act.action_url && <ExternalLink className="w-2.5 h-2.5 opacity-60" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-[10px] text-charcoal-muted mt-1 px-1">
                  {m.timestamp}
                </span>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-charcoal bg-white border border-bordergrey px-3 py-2 rounded-xl w-fit shadow-xs">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-brand-600" />
                Analyzing platform state & diagnosing...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="p-3 bg-white border-t border-bordergrey">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about listings, Amazon, Shopify, sync..."
                className="flex-1 px-3.5 py-2 text-xs sm:text-sm bg-warmwhite border border-bordergrey rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 focus:bg-white transition-all text-charcoal"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="p-2 rounded-xl bg-brand-600 hover:bg-forest disabled:bg-softbeige disabled:text-charcoal-muted text-white transition-colors cursor-pointer shrink-0"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
