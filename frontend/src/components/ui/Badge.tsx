import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'info' | 'danger' | 'neutral' | 'brand' | 'amber';
  size?: 'sm' | 'md';
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
  dot = false,
}) => {
  const variants = {
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    warning: 'bg-softorange-50 text-softorange-700 border-softorange-200',
    info: 'bg-brand-50 text-brand-800 border-brand-200',
    danger: 'bg-rose-50 text-rose-700 border-rose-200',
    neutral: 'bg-softbeige text-charcoal border-bordergrey',
    brand: 'bg-brand-50 text-brand-700 border-brand-200',
    amber: 'bg-softorange-50 text-softorange-700 border-softorange-200',
  };

  const dots = {
    success: 'bg-emerald-500',
    warning: 'bg-softorange-500',
    info: 'bg-brand-500',
    danger: 'bg-rose-500',
    neutral: 'bg-charcoal-muted',
    brand: 'bg-brand-600',
    amber: 'bg-softorange-500',
  };

  const sizes = {
    sm: 'text-[11px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  };

  return (
    <span
      className={`inline-flex items-center font-semibold rounded-full border ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${dots[variant]}`} />}
      {children}
    </span>
  );
};
