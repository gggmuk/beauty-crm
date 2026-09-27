import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  Sparkles,
  Clock,
  Users,
  Bot,
  ShieldAlert,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const navigation = [
  { name: 'Дашборд', to: '/', icon: LayoutDashboard },
  { name: 'Журнал записей', to: '/appointments', icon: Calendar },
  { name: 'Услуги и цены', to: '/services', icon: Sparkles },
  { name: 'График работы', to: '/schedule', icon: Clock },
  { name: 'Клиентская база', to: '/clients', icon: Users },
  { name: 'Конструктор Бота', to: '/bot-settings', icon: Bot },
  { name: 'Суперадмин SaaS', to: '/superadmin', icon: ShieldAlert },
];

export const Sidebar = () => {
  const { logout, tenant } = useAuth();

  return (
    <aside className="w-64 glass-panel flex flex-col h-screen fixed left-0 top-0 border-r border-slate-800 z-30">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-pink-500/20">
          ✨
        </div>
        <div>
          <h1 className="font-bold text-lg text-gradient">BeautyCRM</h1>
          <p className="text-xs text-slate-400">BotBuilder SaaS Platform</p>
        </div>
      </div>

      {/* Tenant info pill */}
      {tenant && (
        <div className="mx-4 my-4 p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-pink-500/20 text-pink-400 flex items-center justify-center font-semibold text-sm">
            {tenant.name?.[0] || 'M'}
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-medium text-slate-200 truncate">{tenant.name}</p>
            <span className="inline-block px-1.5 py-0.5 text-[10px] uppercase tracking-wider font-semibold rounded bg-emerald-500/20 text-emerald-400">
              {tenant.subscription_status}
            </span>
          </div>
        </div>
      )}

      {/* Nav items */}
      <nav className="flex-1 px-4 space-y-1 overflow-y-auto py-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg shadow-pink-500/20'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer logout */}
      <div className="p-4 border-t border-slate-800">
        <button
          onClick={logout}
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl font-medium text-sm text-rose-400 hover:bg-rose-500/10 transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span>Выйти из кабинета</span>
        </button>
      </div>
    </aside>
  );
};
