import React from 'react';
import { Outlet } from 'react-router-dom';
import { PublicNavbar } from '../components/common/PublicNavbar';
import { Footer } from '../components/common/Footer';
import { ToastContainer } from '../components/common/ToastContainer';
import { FloatingAIChatbot } from '../components/common/FloatingAIChatbot';

export const PublicLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-warmwhite text-charcoal relative">
      <PublicNavbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <FloatingAIChatbot />
      <ToastContainer />
    </div>
  );
};

