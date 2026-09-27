import React from 'react';
import { Sidebar } from './Sidebar';

export const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-950 flex">
      <Sidebar />
      <main className="flex-1 ml-64 p-8 overflow-y-auto min-h-screen">
        <div className="max-w-7xl mx-auto space-y-8">
          {children}
        </div>
      </main>
    </div>
  );
};
