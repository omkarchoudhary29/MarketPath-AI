import React from 'react';

/**
 * Option C: Clean + Illustrative (Friendly) Local Vector SVGs
 * Visual language tailored to Indian D2C entrepreneurs, artisanal products,
 * packaging, omnichannel connections, and business growth.
 * Palette: #08765B (Primary green), #075443 (Deep forest), #15966F (Emerald),
 * #FCFBF7 (Warm white), #F4EDE2 (Soft beige), #18231F (Charcoal), #D99143 (Soft orange).
 */

export const HeroD2CIllustration: React.FC<{ className?: string }> = ({ className = 'w-full h-auto' }) => (
  <svg
    viewBox="0 0 520 400"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    role="img"
    aria-label="Friendly Indian D2C Entrepreneur managing multichannel operations"
  >
    {/* Soft background glow circles */}
    <ellipse cx="260" cy="220" rx="220" ry="140" fill="#F4EDE2" opacity="0.8" />
    <circle cx="410" cy="110" r="45" fill="#E0EFE9" />
    <circle cx="100" cy="280" r="30" fill="#FDF8F2" />

    {/* Ground shelf / desk */}
    <rect x="60" y="320" width="400" height="14" rx="7" fill="#E5EAE6" />
    <rect x="100" y="334" width="320" height="6" rx="3" fill="#C1E0D4" opacity="0.6" />

    {/* Product Jars & Handcrafted Goods on Left */}
    <g transform="translate(80, 210)">
      {/* Ceramic vase */}
      <path
        d="M25 110 C25 85, 10 70, 15 45 C17 35, 33 35, 35 45 C40 70, 25 85, 25 110 Z"
        fill="#D99143"
      />
      <ellipse cx="25" cy="40" rx="10" ry="4" fill="#C47D32" />
      {/* Artisanal candle jar */}
      <rect x="45" y="65" width="40" height="45" rx="6" fill="#08765B" />
      <rect x="50" y="58" width="30" height="7" rx="3" fill="#075443" />
      <rect x="52" y="75" width="26" height="22" rx="2" fill="#FCFBF7" />
      <line x1="56" y1="82" x2="74" y2="82" stroke="#64716C" strokeWidth="2" strokeLinecap="round" />
      <line x1="56" y1="88" x2="68" y2="88" stroke="#64716C" strokeWidth="2" strokeLinecap="round" />
    </g>

    {/* Shipping Box with Tape */}
    <g transform="translate(145, 235)">
      <rect x="0" y="15" width="75" height="70" rx="6" fill="#F4EDE2" stroke="#E5EAE6" strokeWidth="2" />
      <rect x="25" y="15" width="25" height="70" fill="#ECC798" opacity="0.6" />
      {/* Shipping label */}
      <rect x="10" y="40" width="30" height="22" rx="3" fill="#FFFFFF" />
      <rect x="14" y="46" width="16" height="3" fill="#18231F" rx="1" />
      <rect x="14" y="52" width="22" height="2" fill="#64716C" rx="1" />
      {/* Fragile stamp */}
      <circle cx="58" cy="55" r="8" fill="#D99143" opacity="0.2" />
      <path d="M55 52 L61 58 M61 52 L55 58" stroke="#D99143" strokeWidth="1.5" strokeLinecap="round" />
    </g>

    {/* Founder Character (Central, Warm & Friendly) */}
    <g transform="translate(240, 110)">
      {/* Body / Kurta */}
      <path
        d="M25 150 C5 150, -10 200, -15 210 L65 210 C60 200, 45 150, 25 150 Z"
        fill="#08765B"
      />
      {/* Collar accent */}
      <path d="M20 150 L25 175 L30 150 Z" fill="#D99143" />

      {/* Head & Neck */}
      <rect x="18" y="125" width="14" height="25" fill="#EADBCA" rx="4" />
      <circle cx="25" cy="100" r="32" fill="#FAF5ED" />
      {/* Face features */}
      <circle cx="18" cy="98" r="3" fill="#18231F" />
      <circle cx="32" cy="98" r="3" fill="#18231F" />
      {/* Warm smile */}
      <path d="M19 110 Q25 118 31 110" stroke="#075443" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      {/* Hair / Bun */}
      <path d="M -5 95 C-5 60, 55 60, 55 95 C55 80, -5 80, -5 95 Z" fill="#18231F" />
      <circle cx="25" cy="62" r="14" fill="#18231F" />

      {/* Arm holding tablet */}
      <path d="M-10 185 Q-5 210 20 200" stroke="#075443" strokeWidth="12" strokeLinecap="round" fill="none" />
      {/* Tablet */}
      <rect x="15" y="165" width="55" height="42" rx="5" fill="#18231F" stroke="#E5EAE6" strokeWidth="2" />
      <rect x="18" y="168" width="49" height="36" rx="3" fill="#FFFFFF" />
      {/* Screen graphs */}
      <line x1="22" y1="185" x2="35" y2="175" stroke="#08765B" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="35" y1="175" x2="48" y2="182" stroke="#08765B" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="48" y1="182" x2="60" y2="172" stroke="#15966F" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="60" cy="172" r="2.5" fill="#D99143" />
    </g>

    {/* Floating Omnichannel Badges around Founder */}
    {/* Shopify Badge */}
    <g transform="translate(350, 80)">
      <rect x="0" y="0" width="110" height="38" rx="10" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.04))" />
      <circle cx="20" cy="19" r="10" fill="#E0EFE9" />
      <text x="20" y="23" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#08765B">S</text>
      <text x="38" y="18" fontSize="11" fontWeight="bold" fill="#18231F">Shopify</text>
      <text x="38" y="28" fontSize="9" fill="#15966F">Live Synced</text>
    </g>

    {/* Amazon SP-API Badge */}
    <g transform="translate(370, 140)">
      <rect x="0" y="0" width="115" height="38" rx="10" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.04))" />
      <circle cx="20" cy="19" r="10" fill="#FDF8F2" />
      <text x="20" y="23" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#D99143">a</text>
      <text x="38" y="18" fontSize="11" fontWeight="bold" fill="#18231F">Amazon IN</text>
      <text x="38" y="28" fontSize="9" fill="#D99143">Ready to Publish</text>
    </g>

    {/* AI Studio Floating Sparkle Badge */}
    <g transform="translate(60, 80)">
      <rect x="0" y="0" width="125" height="42" rx="12" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" filter="drop-shadow(0 4px 8px rgba(7,84,67,0.06))" />
      <circle cx="22" cy="21" r="12" fill="#F4EDE2" />
      <path d="M22 13 L24 19 L30 21 L24 23 L22 29 L20 23 L14 21 L20 19 Z" fill="#D99143" />
      <text x="42" y="18" fontSize="11" fontWeight="bold" fill="#18231F">AI Studio</text>
      <text x="42" y="30" fontSize="9" fill="#08765B">100% Grounded Copy</text>
    </g>

    {/* Revenue Growth Floating Card */}
    <g transform="translate(340, 240)">
      <rect x="0" y="0" width="140" height="50" rx="12" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" filter="drop-shadow(0 4px 10px rgba(0,0,0,0.05))" />
      <text x="14" y="20" fontSize="10" fontWeight="bold" fill="#64716C">UNIFIED REVENUE</text>
      <text x="14" y="38" fontSize="15" fontWeight="extrabold" fill="#075443">₹1,84,500</text>
      <rect x="95" y="14" width="35" height="18" rx="6" fill="#E0EFE9" />
      <text x="112" y="26" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#08765B">+34%</text>
    </g>
  </svg>
);

export const CatalogueIllustration: React.FC<{ className?: string }> = ({ className = 'w-full h-auto' }) => (
  <svg viewBox="0 0 400 280" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} role="img" aria-label="Master Product Catalogue">
    <rect width="400" height="280" rx="16" fill="#FCFBF7" />
    <rect x="30" y="30" width="340" height="220" rx="12" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" />
    {/* Header bar */}
    <rect x="30" y="30" width="340" height="42" rx="12" fill="#F4EDE2" />
    <circle cx="54" cy="51" r="5" fill="#D99143" />
    <circle cx="68" cy="51" r="5" fill="#15966F" />
    <circle cx="82" cy="51" r="5" fill="#08765B" />
    <text x="105" y="55" fontSize="12" fontWeight="bold" fill="#18231F">Master Product Truth (Aura Terra Living)</text>
    {/* Product Row 1 */}
    <rect x="45" y="85" width="40" height="40" rx="8" fill="#E0EFE9" />
    <rect x="53" y="93" width="24" height="24" rx="4" fill="#08765B" />
    <text x="95" y="100" fontSize="12" fontWeight="bold" fill="#18231F">Terracotta Hand-Poured Candle (350g)</text>
    <text x="95" y="115" fontSize="10" fill="#64716C">SKU: AT-TERRA-350 | Volumetric: 0.42 kg | FSSAI/Legal Metrology Compliant</text>
    <rect x="300" y="92" width="55" height="22" rx="6" fill="#E0EFE9" />
    <text x="327" y="106" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#08765B">Published</text>
    <line x1="45" y1="135" x2="355" y2="135" stroke="#E5EAE6" strokeWidth="1" />
    {/* Product Row 2 */}
    <rect x="45" y="145" width="40" height="40" rx="8" fill="#FDF8F2" />
    <rect x="53" y="153" width="24" height="24" rx="4" fill="#D99143" />
    <text x="95" y="160" fontSize="12" fontWeight="bold" fill="#18231F">Handloom Linen Table Runner (6-Seater)</text>
    <text x="95" y="175" fontSize="10" fill="#64716C">SKU: AT-LINEN-RUN-06 | 3 Variants (Oatmeal, Sage, Terracotta)</text>
    <rect x="300" y="152" width="55" height="22" rx="6" fill="#F9EEDD" />
    <text x="327" y="166" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#D99143">Ready</text>
    <line x1="45" y1="195" x2="355" y2="195" stroke="#E5EAE6" strokeWidth="1" />
    {/* Product Row 3 */}
    <rect x="45" y="205" width="40" height="35" rx="8" fill="#F4EDE2" />
    <text x="95" y="222" fontSize="12" fontWeight="bold" fill="#18231F">Ceramic Ribbed Serving Bowl (850ml)</text>
    <text x="95" y="235" fontSize="10" fill="#64716C">Outer carton: 24x24x18 cm | Fragile Box</text>
  </svg>
);

export const OmnichannelHubIllustration: React.FC<{ className?: string }> = ({ className = 'w-full h-auto' }) => (
  <svg viewBox="0 0 440 260" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} role="img" aria-label="Omnichannel Publishing Hub">
    {/* Center Hub */}
    <circle cx="220" cy="130" r="48" fill="#075443" />
    <circle cx="220" cy="130" r="38" fill="#08765B" />
    <text x="220" y="128" textAnchor="middle" fontSize="13" fontWeight="bold" fill="#FFFFFF">MarketPath</text>
    <text x="220" y="142" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#D99143">Control Core</text>

    {/* Connection lines */}
    <path d="M 180 100 L 95 65" stroke="#08765B" strokeWidth="2" strokeDasharray="4 4" />
    <path d="M 260 100 L 345 65" stroke="#08765B" strokeWidth="2" strokeDasharray="4 4" />
    <path d="M 180 160 L 95 195" stroke="#08765B" strokeWidth="2" strokeDasharray="4 4" />
    <path d="M 260 160 L 345 195" stroke="#08765B" strokeWidth="2" strokeDasharray="4 4" />

    {/* Satellite 1: Storefronts */}
    <g transform="translate(25, 35)">
      <rect width="110" height="52" rx="10" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" />
      <rect x="8" y="8" width="18" height="18" rx="4" fill="#08765B" />
      <text x="17" y="21" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#FFFFFF">S</text>
      <text x="32" y="20" fontSize="11" fontWeight="bold" fill="#18231F">Shopify</text>
      <text x="8" y="38" fontSize="9" fill="#15966F">GraphQL 2025-01</text>
    </g>

    {/* Satellite 2: Marketplaces */}
    <g transform="translate(305, 35)">
      <rect width="115" height="52" rx="10" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" />
      <rect x="8" y="8" width="18" height="18" rx="4" fill="#D99143" />
      <text x="17" y="21" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#FFFFFF">a</text>
      <text x="32" y="20" fontSize="11" fontWeight="bold" fill="#18231F">Amazon India</text>
      <text x="8" y="38" fontSize="9" fill="#D99143">SP-API Approved</text>
    </g>

    {/* Satellite 3: Social & Ads */}
    <g transform="translate(25, 175)">
      <rect width="110" height="52" rx="10" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" />
      <rect x="8" y="8" width="18" height="18" rx="4" fill="#7C3AED" />
      <text x="17" y="21" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#FFFFFF">IG</text>
      <text x="32" y="20" fontSize="11" fontWeight="bold" fill="#18231F">Instagram</text>
      <text x="8" y="38" fontSize="9" fill="#64716C">Graph API Ready</text>
    </g>

    {/* Satellite 4: Quick Commerce */}
    <g transform="translate(305, 175)">
      <rect width="115" height="52" rx="10" fill="#FFFFFF" stroke="#E5EAE6" strokeWidth="1.5" />
      <rect x="8" y="8" width="18" height="18" rx="4" fill="#D99143" />
      <text x="17" y="21" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#FFFFFF">Z</text>
      <text x="32" y="20" fontSize="11" fontWeight="bold" fill="#18231F">Zepto & Blinkit</text>
      <text x="8" y="38" fontSize="9" fill="#D99143">Partner Access</text>
    </g>
  </svg>
);
