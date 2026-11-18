export type Role = 'owner' | 'admin' | 'marketer' | 'viewer';

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  avatarUrl?: string;
  isPlatformAdmin: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  currency: string;
  timezone: string;
  planId: string;
  activeSkus: number;
  maxSkus: number;
  connectedChannels: number;
  maxChannels: number;
}

export interface BrandProfile {
  id: string;
  name: string;
  tagline: string;
  story: string;
  mission?: string;
  toneOfVoice: string;
  archetype?: string;
  primaryColor: string;
  secondaryColor: string;
  targetAudience: string;
  logoUrl?: string;
}

export interface ProductVariant {
  id: string;
  sku: string;
  title: string;
  price: number;
  stockQuantity: number;
  options: Record<string, string>;
}

export interface ProductMedia {
  id: string;
  url: string;
  publicId: string;
  altText: string;
  isPrimary: boolean;
}

export interface ChannelOverride {
  channel: 'shopify' | 'instagram';
  title?: string;
  description?: string;
  price?: number;
  tags?: string[];
  isApproved: boolean;
}

export interface MasterProduct {
  id: string;
  sku: string;
  title: string;
  category: string;
  shortDescription: string;
  longDescription: string;
  basePrice: number;
  compareAtPrice?: number;
  costPrice?: number;
  currency: string;
  stockQuantity: number;
  materials: string[];
  dimensions: { length: number; width: number; height: number; unit: string };
  weight: number;
  tags: string[];
  status: 'draft' | 'active' | 'archived';
  media: ProductMedia[];
  variants: ProductVariant[];
  overrides: Record<string, ChannelOverride>;
  category_attributes?: Record<string, any>;
  packaging_specs?: {
    box_length?: number;
    box_width?: number;
    box_height?: number;
    box_unit?: string;
    dead_weight_grams?: number;
    volumetric_weight_grams?: number;
    packaging_material?: string;
    protective_packaging?: string;
  };
  shipping_specs?: Record<string, any>;
  moq?: number;
  compliance_certificates?: string[];
  createdAt: string;
  updatedAt: string;
}

export type ChannelType = 'shopify' | 'instagram' | 'meta_ads' | 'google_ads' | 'amazon';

export interface ChannelConnection {
  id: string;
  type: ChannelType;
  name: string;
  identifier: string;
  status: 'connected' | 'setup_required' | 'approval_pending' | 'expired';
  lastSyncAt?: string;
  itemsPublished: number;
  details?: string;
}

export interface PublishingJob {
  id: string;
  productId: string;
  productTitle: string;
  productSku: string;
  channelType: ChannelType;
  status: 'queued' | 'processing' | 'published' | 'failed' | 'action_required';
  idempotencyKey: string;
  remoteUrl?: string;
  remoteId?: string;
  errorMessage?: string;
  createdAt: string;
  completedAt?: string;
  retryCount: number;
}

export interface AIGenerationOption {
  versionNumber: number;
  title?: string;
  caption?: string;
  bulletPoints?: string[];
  hashtags?: string[];
  callToAction: string;
  approved: boolean;
}

export interface CampaignCreative {
  id: string;
  headline: string;
  primaryText: string;
  descriptionText?: string;
  ctaText: string;
  mediaUrl: string;
  destinationUrl: string;
  format?: string;
  versionNumber?: number;
  isSelected?: boolean;
  isApproved?: boolean;
}

export interface Campaign {
  id: string;
  name: string;
  objective: 'awareness' | 'traffic' | 'engagement' | 'leads' | 'sales';
  totalBudget: number;
  dailyBudgetLimit: number;
  currency: string;
  startDate: string;
  endDate?: string;
  status: 'draft' | 'pending_approval' | 'approved' | 'ready_for_manual_setup' | 'active' | 'paused' | 'completed' | 'archived';
  channel: ChannelType | 'meta_ads' | 'google_ads';
  productIds?: string[];
  productId?: string;
  product?: {
    id: string;
    title: string;
    sku: string;
    category: string;
    base_price: number;
    currency: string;
    thumbnail_url?: string;
  };
  targetGeography?: string;
  targetAudienceBrief?: string;
  landingPageUrl?: string;
  callToAction?: string;
  creativeFormat?: string;
  description?: string;
  utmParams?: Record<string, any>;
  aiProposal?: any;
  manualSetupInstructions?: any;
  rejectionReason?: string;
  approvedByUserId?: string;
  approvedAt?: string;
  creatives: CampaignCreative[];
  metrics?: {
    spend: number;
    impressions: number;
    clicks: number;
    conversions: number;
    roas?: number;
  };
  performanceSummary?: {
    total_spend: number;
    total_budget: number;
    remaining_budget: number;
    daily_budget_limit: number;
    total_impressions: number;
    total_clicks: number;
    total_conversions: number;
    total_conversion_value: number;
    average_ctr: number;
    average_cpc: number;
    blended_roas?: number;
    data_source: string;
    attribution_window: string;
    last_synced_at?: string;
    daily_breakdown?: Array<{
      date: string;
      spend: number;
      impressions: number;
      clicks: number;
      conversions: number;
      conversion_value: number;
      ctr: number;
      cpc: number;
      roas?: number;
    }>;
  };
}

export interface PlanTier {
  id: string;
  name: string;
  priceInr: number;
  interval: 'month' | 'year';
  description: string;
  features: string[];
  skuLimit: number;
  channelLimit: number;
  isPopular?: boolean;
}

export interface ManagedServiceItem {
  id: string;
  title: string;
  priceInr: number;
  description: string;
  turnaround: string;
  deliverables: string[];
}

