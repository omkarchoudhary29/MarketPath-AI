/**
 * MarketPath AI — Centralized Site & Project Configuration
 *
 * Configures global project metadata, canonical repository URLs,
 * demo endpoints, and documentation links.
 */

export const siteConfig = {
  name: 'MarketPath AI',
  shortName: 'MarketPath',
  tagline: 'AI-Powered Omnichannel D2C Operating Platform',
  description:
    'Single master product catalogue, grounded Gemini content studio, 7-step verified publishing, unified orders, and omnichannel growth operating system for Indian D2C brands.',
  author: {
    name: 'Omkar Choudhary',
    email: 'omkarchoudhary2904@gmail.com',
    githubUsername: 'omkarchoudhary29',
  },
  // Canonical GitHub repository URL with fallback to developer profile
  githubRepoUrl:
    (import.meta.env.VITE_GITHUB_REPO_URL as string) ||
    'https://github.com/omkarchoudhary29/marketpath-ai',
  documentationUrl: '/about',
  demo: {
    brandName: 'Aura Terra Living',
    location: 'Pune, Maharashtra',
    category: 'Home & Living',
    companyLoginUrl: '/login?type=company',
    agencyLoginUrl: '/login?type=agency',
    consultantLoginUrl: '/login?type=consultant',
    adminLoginUrl: '/login?type=admin',
  },
  branding: {
    primaryGreen: '#08765B',
    deepForest: '#075443',
    emerald: '#15966F',
    warmWhite: '#FCFBF7',
    charcoal: '#18231F',
    mutedGrey: '#64716C',
    softOrange: '#D99143',
    borderGrey: '#E5EAE6',
  },
};

export default siteConfig;
