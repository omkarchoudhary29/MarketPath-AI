import React, { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight, ChevronDown, ShieldCheck, Sparkles, HelpCircle, Info, ExternalLink, Play } from 'lucide-react';
import { siteConfig } from '../../config/site';

export const PublicNavbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [aboutDropdownOpen, setAboutDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setAboutDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close menus on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setAboutDropdownOpen(false);
  }, [location.pathname]);

  const aboutDropdownItems = [
    {
      name: 'About MarketPath',
      to: '/about',
      description: 'Our origin story, mission, and the D2C fragmentation problem we solve.',
      icon: Info,
    },
    {
      name: 'How It Works',
      to: '/about#how-it-works',
      description: 'The approved workflow: Describe, Adapt, Validate, Approve, Publish.',
      icon: HelpCircle,
    },
    {
      name: 'Trust & Security',
      to: '/about#trust-security',
      description: 'Tenant isolation, scoped API credentials, and mandatory human approval.',
      icon: ShieldCheck,
    },
  ];

  return (
    <header className="sticky top-0 z-50 bg-warmwhite/95 backdrop-blur-md border-b border-bordergrey">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo -> Always navigates to Home */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-forest bg-gradient-to-tr from-[#075443] via-[#08765B] to-[#15966F] border border-[#15966F]/40 flex items-center justify-center text-white shadow-sm group-hover:shadow transition-all">
            <span className="font-extrabold text-base tracking-tight">MP</span>
          </div>
          <div>
            <span className="text-xl font-bold text-charcoal tracking-tight">
              MarketPath <span className="text-brand-600 font-bold">AI</span>
            </span>
            <span className="block text-[10px] text-charcoal-muted uppercase tracking-widest font-semibold">
              D2C Growth Operating Platform
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-1.5">
          {/* Home Link */}
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `px-3.5 py-2 text-sm font-semibold rounded-xl transition-colors ${
                isActive
                  ? 'text-forest bg-brand-50 font-bold'
                  : 'text-charcoal-muted hover:text-charcoal hover:bg-softbeige/50'
              }`
            }
          >
            Home
          </NavLink>

          {/* About Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setAboutDropdownOpen(!aboutDropdownOpen)}
              onMouseEnter={() => setAboutDropdownOpen(true)}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold rounded-xl transition-colors cursor-pointer ${
                location.pathname.startsWith('/about') || aboutDropdownOpen
                  ? 'text-forest bg-brand-50 font-bold'
                  : 'text-charcoal-muted hover:text-charcoal hover:bg-softbeige/50'
              }` }
            >
              <span>About</span>
              <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${aboutDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {aboutDropdownOpen && (
              <div
                onMouseLeave={() => setAboutDropdownOpen(false)}
                className="absolute left-0 mt-1 w-80 rounded-2xl bg-white shadow-option-c-lg border border-bordergrey py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150"
              >
                {aboutDropdownItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.to}
                      onClick={() => setAboutDropdownOpen(false)}
                      className="flex items-start gap-3 px-4 py-3 hover:bg-softbeige/40 transition-colors group"
                    >
                      <div className="w-8 h-8 rounded-lg bg-softbeige text-forest flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-brand-600 group-hover:text-white transition-colors">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-charcoal group-hover:text-forest transition-colors">
                          {item.name}
                        </div>
                        <div className="text-xs text-charcoal-muted leading-relaxed mt-0.5">
                          {item.description}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Free Consultation NavLink */}
          <NavLink
            to="/free-consultation"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold rounded-xl transition-colors ${
                isActive
                  ? 'text-forest bg-brand-50 font-bold'
                  : 'text-charcoal-muted hover:text-charcoal hover:bg-softbeige/50'
              }`
            }
          >
            <Sparkles className="w-3.5 h-3.5 text-softorange" />
            <span>Free Consultation</span>
          </NavLink>

          {/* Explore Demo NavLink */}
          <NavLink
            to="/login?type=company"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3.5 py-2 text-sm font-bold rounded-xl transition-colors ${
                isActive
                  ? 'text-forest bg-brand-50 font-bold'
                  : 'text-forest bg-softorange/10 hover:bg-softorange/20 border border-softorange/30'
              }`
            }
          >
            <Play className="w-3.5 h-3.5 text-softorange fill-softorange" />
            <span>Explore Demo</span>
          </NavLink>
        </nav>

        {/* CTA Buttons & GitHub */}
        <div className="hidden sm:flex items-center gap-2.5">
          <a
            href={siteConfig.githubRepoUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View MarketPath AI source code on GitHub"
            title="View MarketPath AI on GitHub"
            className="p-2 text-charcoal-muted hover:text-charcoal hover:bg-softbeige/50 rounded-xl transition-colors flex items-center justify-center cursor-pointer border border-bordergrey"
          >
            <svg
              className="w-5 h-5 fill-current"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
          </a>

          <Link
            to="/login"
            className="text-sm font-semibold text-charcoal hover:text-forest px-3.5 py-2 rounded-xl hover:bg-softbeige/50 transition-colors"
          >
            Sign In
          </Link>
          <Link
            to="/signup"
            className="inline-flex items-center gap-1.5 text-sm font-bold text-white bg-brand-600 hover:bg-forest px-4.5 py-2.5 rounded-xl shadow-sm hover:shadow transition-all"
          >
            <span>Start Free Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Mobile Hamburger */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-charcoal-muted hover:text-charcoal rounded-xl hover:bg-softbeige/50 lg:hidden cursor-pointer"
          aria-label="Toggle Navigation"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-bordergrey bg-white px-4 pt-3 pb-6 space-y-2 animate-in slide-in-from-top-2 duration-150 shadow-option-c-lg">
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 text-base font-semibold rounded-xl text-charcoal hover:bg-softbeige/40"
          >
            Home
          </Link>

          <div className="px-3 py-1 text-xs font-bold uppercase tracking-wider text-charcoal-muted">
            About MarketPath
          </div>
          {aboutDropdownItems.map((item) => (
            <Link
              key={item.name}
              to={item.to}
              onClick={() => setMobileMenuOpen(false)}
              className="block pl-6 pr-3 py-2 text-sm font-medium text-charcoal-muted hover:text-charcoal hover:bg-softbeige/40 rounded-xl"
            >
              {item.name}
            </Link>
          ))}

          <Link
            to="/free-consultation"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-base font-bold text-forest bg-brand-50 rounded-xl"
          >
            <Sparkles className="w-4 h-4 text-softorange" />
            <span>Free Consultation</span>
          </Link>

          <Link
            to="/login?type=company"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-base font-bold text-forest bg-softorange/10 border border-softorange/30 rounded-xl"
          >
            <Play className="w-4 h-4 text-softorange fill-softorange" />
            <span>Explore Demo</span>
          </Link>

          <a
            href={siteConfig.githubRepoUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View MarketPath AI source code on GitHub"
            className="flex items-center justify-between px-3 py-2 text-sm font-semibold text-charcoal hover:bg-softbeige/40 rounded-xl"
          >
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>GitHub Repository</span>
            </span>
            <ExternalLink className="w-3.5 h-3.5 text-charcoal-muted" />
          </a>

          <div className="pt-4 border-t border-bordergrey flex flex-col gap-2">
            <Link
              to="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="text-center py-2.5 text-sm font-bold text-charcoal hover:bg-softbeige/40 rounded-xl border border-bordergrey"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              onClick={() => setMobileMenuOpen(false)}
              className="text-center py-2.5 text-sm font-bold text-white bg-brand-600 hover:bg-forest rounded-xl shadow-sm"
            >
              Start Free Workspace
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
