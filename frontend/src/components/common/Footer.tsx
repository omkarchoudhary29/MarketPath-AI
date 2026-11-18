import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Sparkles, ExternalLink } from 'lucide-react';
import { siteConfig } from '../../config/site';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-forest-deep bg-[#053F32] text-slate-200 border-t border-[#075443]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
          {/* Brand Manifesto */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-forest bg-gradient-to-tr from-[#075443] via-[#08765B] to-[#15966F] border border-[#15966F]/40 flex items-center justify-center text-white font-extrabold text-sm shadow-sm">
                MP
              </div>
              <span className="text-xl font-bold text-white tracking-tight">
                MarketPath <span className="text-emerald font-semibold">AI</span>
              </span>
            </Link>
            <p className="text-xs text-[#C1E0D4] max-w-sm leading-relaxed">
              The AI-assisted D2C commerce and growth operating platform for emerging Indian product brands. Run your product business across channels, effortlessly.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-[#E0EFE9] bg-[#075443]/80 px-3 py-2 rounded-xl border border-[#15966F]/30 max-w-xs">
              <Shield className="w-4 h-4 text-emerald shrink-0" />
              <span>Scoped API credentials & mandatory human approval gate.</span>
            </div>
            <div className="pt-1">
              <a
                href={siteConfig.githubRepoUrl}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="View MarketPath AI source code on GitHub"
                className="inline-flex items-center gap-2 text-xs font-semibold text-white bg-[#075443] hover:bg-forest px-3.5 py-1.5 rounded-xl border border-[#15966F]/40 transition-colors"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                <span>GitHub Source</span>
                <ExternalLink className="w-3 h-3 text-[#8CC5B0]" />
              </a>
            </div>
          </div>

          {/* Product Capabilities */}
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">Product Capabilities</h4>
            <ul className="space-y-2.5 text-xs text-[#C1E0D4]">
              <li><a href="/#catalogue" className="hover:text-white hover:underline transition-colors">Master Product Catalogue</a></li>
              <li><a href="/#ai-studio" className="hover:text-white hover:underline transition-colors">AI Content Studio</a></li>
              <li><a href="/#channels" className="hover:text-white hover:underline transition-colors">Connected Channel Ecosystem</a></li>
              <li><a href="/#publishing" className="hover:text-white hover:underline transition-colors">Publishing Engine</a></li>
              <li><a href="/#marketing" className="hover:text-white hover:underline transition-colors">Marketing & Ad Studio</a></li>
              <li><a href="/#agency-connect" className="hover:text-white hover:underline transition-colors">Agency Connect Directory</a></li>
            </ul>
          </div>

          {/* About & Trust */}
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">About & Trust</h4>
            <ul className="space-y-2.5 text-xs text-[#C1E0D4]">
              <li><Link to="/about" className="hover:text-white hover:underline transition-colors">About MarketPath AI</Link></li>
              <li><Link to="/about#how-it-works" className="hover:text-white hover:underline transition-colors">How It Works</Link></li>
              <li><Link to="/about#trust-security" className="hover:text-white hover:underline transition-colors">Trust, Security & RLS</Link></li>
              <li><Link to="/about#trust-security" className="hover:text-white hover:underline transition-colors">Data Integrity & Human Gates</Link></li>
              <li><Link to="/free-consultation" className="hover:text-white hover:underline transition-colors">Enterprise Custom Plans</Link></li>
            </ul>
          </div>

          {/* Consultation & Support */}
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">Growth Advisory</h4>
            <ul className="space-y-2.5 text-xs text-[#C1E0D4]">
              <li>
                <Link to="/free-consultation" className="hover:text-white transition-colors flex items-center gap-1.5 text-softorange font-bold">
                  <Sparkles className="w-3.5 h-3.5" /> Book Free Consultation
                </Link>
              </li>
              <li><Link to="/login" className="hover:text-white hover:underline transition-colors">Seller Sign In</Link></li>
              <li><Link to="/signup" className="hover:text-white hover:underline transition-colors">Start Free Workspace</Link></li>
              <li><a href="mailto:support@marketpath.ai" className="hover:text-white hover:underline transition-colors">support@marketpath.ai</a></li>
              <li className="pt-2 text-[11px] text-slate-400">Supporting emerging D2C product creators across Pune, Mumbai, Maharashtra and Pan-India.</li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-[#075443] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#8CC5B0]">
          <p>© {new Date().getFullYear()} MarketPath AI. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <a
              href={siteConfig.githubRepoUrl}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="View MarketPath AI source code on GitHub"
              className="hover:text-white transition-colors flex items-center gap-1.5 font-semibold text-emerald"
            >
              <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>GitHub</span>
            </a>
            <Link to="/about#trust-security" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link to="/about#trust-security" className="hover:text-white transition-colors">Terms of Service</Link>
            <Link to="/about#trust-security" className="hover:text-white transition-colors">Security Architecture</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};
