import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { apiClient } from '../lib/api';
import {
  MasterProduct,
  ChannelConnection,
  PublishingJob,
  Campaign,
  BrandProfile,
  Organization,
} from '../types';
import {
  mockProducts,
  mockChannels,
  mockPublishingJobs,
  mockCampaigns,
  brandProfileMock,
  currentOrgMock,
} from '../data/mockData';

export interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message?: string;
}

interface AppContextType {
  isDemoMode: boolean;
  toggleDemoMode: () => void;
  org: Organization;
  brand: BrandProfile;
  updateBrand: (updated: Partial<BrandProfile>) => void;
  products: MasterProduct[];
  addProduct: (product: Omit<MasterProduct, 'id' | 'createdAt' | 'updatedAt'>) => MasterProduct;
  updateProduct: (id: string, updated: Partial<MasterProduct>) => void;
  deleteProduct: (id: string) => void;
  channels: ChannelConnection[];
  publishingJobs: PublishingJob[];
  retryPublishingJob: (jobId: string) => void;
  triggerPublish: (productId: string, channelType: 'shopify' | 'instagram') => void;
  campaigns: Campaign[];
  addCampaign: (campaign: Omit<Campaign, 'id'>) => Campaign;
  approveCampaignBudget: (campaignId: string) => void;
  pauseCampaign: (campaignId: string) => void;
  selectedProductIdForStudio: string | null;
  setSelectedProductIdForStudio: (id: string | null) => void;
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const auth = useAuth();
  const [isDemoMode, setIsDemoMode] = useState<boolean>(() => auth?.isDemoMode ?? true);
  const [org, setOrg] = useState<Organization>(currentOrgMock);
  const [brand, setBrand] = useState<BrandProfile>(brandProfileMock);
  const [products, setProducts] = useState<MasterProduct[]>(mockProducts);
  const [channels, setChannels] = useState<ChannelConnection[]>(mockChannels);
  const [publishingJobs, setPublishingJobs] = useState<PublishingJob[]>(mockPublishingJobs);
  const [campaigns, setCampaigns] = useState<Campaign[]>(mockCampaigns);
  const [selectedProductIdForStudio, setSelectedProductIdForStudio] = useState<string | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Synchronize state with authenticated session and organization
  useEffect(() => {
    if (!auth) return;
    setIsDemoMode(auth.isDemoMode);

    if (auth.activeOrg) {
      setOrg({
        ...currentOrgMock,
        id: auth.activeOrg.id,
        name: auth.activeOrg.name,
        slug: auth.activeOrg.slug,
      });

      // Synchronize brand name to match active organization
      setBrand((prev) => ({
        ...prev,
        name: auth.activeOrg ? auth.activeOrg.name : prev.name,
      }));

      // If in genuine live mode, fetch real products for this tenant
      if (!auth.isDemoMode) {
        apiClient<{ items: any[]; total: number }>(`/api/v1/products?page=1&page_size=50`, {
          token: auth.session?.access_token,
          organizationId: auth.activeOrg.id,
        })
          .then((res) => {
            if (res && Array.isArray(res.items)) {
              const mapped: MasterProduct[] = res.items.map((item: any) => ({
                id: item.id,
                title: item.title,
                sku: item.sku || `SKU-${item.id.slice(0, 6)}`,
                category: item.category || 'General',
                status: item.status || 'draft',
                basePrice: item.base_price || 0,
                compareAtPrice: item.compare_at_price,
                costPrice: item.cost_price,
                currency: item.currency || 'INR',
                stockQuantity: item.stock_quantity || 0,
                shortDescription: item.short_description || '',
                longDescription: item.long_description || '',
                materials: item.materials ? [item.materials] : [],
                tags: item.tags ? [item.tags] : [],
                dimensions: item.dimensions_json || { length: 0, width: 0, height: 0, unit: 'cm' },
                weight: item.weight_kg || 0,
                variants: [],
                overrides: {},
                media: item.media_json || [],
                createdAt: item.created_at,
                updatedAt: item.updated_at,
              }));
              setProducts(mapped);
              if (mapped.length > 0) {
                setSelectedProductIdForStudio(mapped[0].id);
              } else {
                setSelectedProductIdForStudio(null);
              }
            } else {
              setProducts([]);
              setSelectedProductIdForStudio(null);
            }
          })
          .catch(() => {
            setProducts([]);
            setSelectedProductIdForStudio(null);
          });
      } else {
        // Demo mode uses verified sample products
        setProducts(mockProducts);
        setSelectedProductIdForStudio(mockProducts[0]?.id || null);
      }
    }
  }, [auth?.activeOrg?.id, auth?.isDemoMode, auth?.session?.access_token]);

  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { ...toast, id }]);
    setTimeout(() => {
      removeToast(id);
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const toggleDemoMode = () => {
    setIsDemoMode((prev) => !prev);
    addToast({
      type: 'info',
      title: !isDemoMode ? 'Demo Mode Active' : 'Live Mode (Credentials Pending)',
      message: !isDemoMode
        ? 'Loaded verified sample D2C brand data.'
        : 'Connect accounts in Settings / Integrations to enable production sync.',
    });
  };

  const updateBrand = (updated: Partial<BrandProfile>) => {
    setBrand((prev) => ({ ...prev, ...updated }));
    addToast({ type: 'success', title: 'Brand Guidelines Updated', message: 'AI Studio will now use your latest tone settings.' });
  };

  const addProduct = (newProdData: Omit<MasterProduct, 'id' | 'createdAt' | 'updatedAt'>): MasterProduct => {
    const newProduct: MasterProduct = {
      ...newProdData,
      id: `prod_${Math.random().toString(36).substring(2, 9)}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setProducts((prev) => [newProduct, ...prev]);
    addToast({ type: 'success', title: 'Product Created', message: `${newProduct.title} added to Master Catalogue.` });
    return newProduct;
  };

  const updateProduct = (id: string, updated: Partial<MasterProduct>) => {
    setProducts((prev) =>
      prev.map((p) => (p.id === id ? { ...p, ...updated, updatedAt: new Date().toISOString() } : p))
    );
    addToast({ type: 'success', title: 'Product Updated', message: 'Master record and channel overrides saved.' });
  };

  const deleteProduct = (id: string) => {
    setProducts((prev) => prev.filter((p) => p.id !== id));
    addToast({ type: 'info', title: 'Product Archived', message: 'Removed from active catalogue.' });
  };

  const retryPublishingJob = (jobId: string) => {
    setPublishingJobs((prev) =>
      prev.map((job) =>
        job.id === jobId
          ? {
              ...job,
              status: 'processing',
              errorMessage: undefined,
              retryCount: job.retryCount + 1,
            }
          : job
      )
    );
    addToast({ type: 'info', title: 'Publish Job Retried', message: 'Worker is reprocessing with idempotency key.' });

    setTimeout(() => {
      setPublishingJobs((prev) =>
        prev.map((job) =>
          job.id === jobId
            ? {
                ...job,
                status: 'published',
                completedAt: new Date().toISOString(),
                remoteUrl: 'https://auraterra-living.myshopify.com/products/retried-listing',
              }
            : job
        )
      );
      addToast({ type: 'success', title: 'Publish Successful', message: 'Listing live on remote channel.' });
    }, 1800);
  };

  const triggerPublish = (productId: string, channelType: 'shopify' | 'instagram') => {
    const prod = products.find((p) => p.id === productId);
    if (!prod) return;

    const newJob: PublishingJob = {
      id: `job_pub_${Math.random().toString(36).substring(2, 8)}`,
      productId: prod.id,
      productTitle: prod.title,
      productSku: prod.sku,
      channelType,
      status: 'processing',
      idempotencyKey: `idemp_${channelType}_${prod.sku}_${Date.now()}`,
      createdAt: new Date().toISOString(),
      retryCount: 0,
    };

    setPublishingJobs((prev) => [newJob, ...prev]);
    addToast({ type: 'info', title: 'Publishing Job Queued', message: `Sending ${prod.title} to ${channelType.toUpperCase()}...` });

    setTimeout(() => {
      setPublishingJobs((prev) =>
        prev.map((j) =>
          j.id === newJob.id
            ? {
                ...j,
                status: 'published',
                completedAt: new Date().toISOString(),
                remoteUrl:
                  channelType === 'shopify'
                    ? `https://auraterra-living.myshopify.com/products/${prod.sku.toLowerCase()}`
                    : `https://instagram.com/p/${Math.random().toString(36).substring(2, 9)}`,
              }
            : j
        )
      );
      addToast({ type: 'success', title: 'Published Successfully', message: `Live on ${channelType.toUpperCase()}` });
    }, 1600);
  };

  const addCampaign = (campaignData: Omit<Campaign, 'id'>): Campaign => {
    const newCamp: Campaign = {
      ...campaignData,
      id: `camp_${Math.random().toString(36).substring(2, 8)}`,
    };
    setCampaigns((prev) => [newCamp, ...prev]);
    addToast({ type: 'success', title: 'Campaign Brief Created', message: `${newCamp.name} ready for review.` });
    return newCamp;
  };

  const approveCampaignBudget = (campaignId: string) => {
    setCampaigns((prev) =>
      prev.map((c) => (c.id === campaignId ? { ...c, status: 'approved' } : c))
    );
    addToast({ type: 'success', title: 'Budget Approved by Owner', message: 'Campaign is authorized for launch.' });
  };

  const pauseCampaign = (campaignId: string) => {
    setCampaigns((prev) =>
      prev.map((c) => (c.id === campaignId ? { ...c, status: 'paused' } : c))
    );
    addToast({ type: 'warning', title: 'Campaign Paused', message: 'Ad spend halted.' });
  };

  return (
    <AppContext.Provider
      value={{
        isDemoMode,
        toggleDemoMode,
        org,
        brand,
        updateBrand,
        products,
        addProduct,
        updateProduct,
        deleteProduct,
        channels,
        publishingJobs,
        retryPublishingJob,
        triggerPublish,
        campaigns,
        addCampaign,
        approveCampaignBudget,
        pauseCampaign,
        selectedProductIdForStudio,
        setSelectedProductIdForStudio,
        toasts,
        addToast,
        removeToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

