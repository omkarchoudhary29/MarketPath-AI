import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
}

export const Card: React.FC<CardProps> = ({ children, className = '', hoverable = false, onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl border border-bordergrey shadow-option-c ${
        hoverable ? 'hover:shadow-option-c-md hover:border-brand-300 transition-all duration-200' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}> = ({ title, subtitle, action, className = '' }) => {
  return (
    <div className={`p-5 sm:p-6 border-b border-bordergrey flex items-center justify-between ${className}`}>
      <div>
        <h3 className="text-base font-bold text-charcoal tracking-tight">{title}</h3>
        {subtitle && <p className="text-xs text-charcoal-muted mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};

export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return <div className={`p-5 sm:p-6 ${className}`}>{children}</div>;
};

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return (
    <div className={`px-5 py-3.5 sm:px-6 bg-softbeige/40 border-t border-bordergrey rounded-b-2xl flex items-center justify-between ${className}`}>
      {children}
    </div>
  );
};
