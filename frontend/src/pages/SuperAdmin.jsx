import React, { useEffect, useState } from 'react';
import { Shield, Users, DollarSign, Ban, CheckCircle } from 'lucide-react';
import api from '../api/client';

export const SuperAdmin = () => {
  const [tenants, setTenants] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [tenantsRes, analyticsRes] = await Promise.all([
        api.get('/superadmin/tenants'),
        api.get('/superadmin/analytics'),
      ]);
      setTenants(tenantsRes.data);
      setAnalytics(analyticsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleBlock = async (id, currentStatus) => {
    const shouldBlock = currentStatus !== 'blocked';
    try {
      await api.patch(`/superadmin/tenants/${id}/block?blocked=${shouldBlock}`);
      fetchData();
    } catch (err) {
      alert('Ошибка изменения статуса');
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-panel p-6 rounded-2xl border border-purple-500/20">
        <h1 className="text-2xl font-bold text-gradient flex items-center space-x-2">
          <Shield className="w-6 h-6 text-purple-400" />
          <span>Суперадмин Платформы (SaaS Owner)</span>
        </h1>
        <p className="text-sm text-slate-400">Управление подписками мастеров и общая аналитика оборота</p>
      </div>

      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <p className="text-xs text-slate-400">Всего мастеров (Tenants)</p>
            <p className="text-3xl font-bold text-white mt-1">{analytics.total_tenants}</p>
          </div>
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <p className="text-xs text-slate-400">Всего онлайн-записей</p>
            <p className="text-3xl font-bold text-white mt-1">{analytics.total_appointments}</p>
          </div>
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <p className="text-xs text-slate-400">Оборот предоплат</p>
            <p className="text-3xl font-bold text-emerald-400 mt-1">{analytics.total_platform_prepayments_turnover} ₽</p>
          </div>
        </div>
      )}

      {/* Tenants Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <h2 className="text-lg font-bold text-white p-6 border-b border-slate-800">Мастера и Студии</h2>

        {loading ? (
          <div className="py-12 text-center text-slate-400">Загрузка...</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Мастер / Студия</th>
                <th className="px-6 py-4">Telegram ID</th>
                <th className="px-6 py-4">Тариф</th>
                <th className="px-6 py-4">Статус</th>
                <th className="px-6 py-4 text-right">Действие</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {tenants.map((t) => (
                <tr key={t.id} className="hover:bg-slate-900/50">
                  <td className="px-6 py-4 font-semibold text-white">{t.name}</td>
                  <td className="px-6 py-4 text-slate-400">{t.telegram_user_id}</td>
                  <td className="px-6 py-4 font-medium text-pink-400 uppercase text-xs">{t.subscription_status}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                        t.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {t.is_active ? 'Активен' : 'Заблокирован'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleToggleBlock(t.id, t.subscription_status)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                        t.is_active
                          ? 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20'
                          : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                      }`}
                    >
                      {t.is_active ? 'Заблокировать' : 'Разблокировать'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
