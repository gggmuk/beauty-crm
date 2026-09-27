import React, { useEffect, useState } from 'react';
import { Search, UserCheck, AlertTriangle, UserX, Award } from 'lucide-react';
import api from '../api/client';

export const Clients = () => {
  const [clients, setClients] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchClients = async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;

      const res = await api.get('/clients', { params });
      setClients(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, [search, statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gradient">Клиентская База (CRM)</h1>
          <p className="text-sm text-slate-400">История визитов, общие затраты LTV и статус удержания</p>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Поиск по имени или телефону..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-pink-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {['', 'regular', 'at_risk', 'lost'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-colors ${
                statusFilter === st
                  ? 'bg-pink-500 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {st === '' ? 'Все' : st === 'regular' ? 'Постоянный' : st === 'at_risk' ? 'В зоне риска' : 'Потерян'}
            </button>
          ))}
        </div>
      </div>

      {/* CRM Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-400">Загрузка клиентов...</div>
        ) : clients.length === 0 ? (
          <div className="py-12 text-center text-slate-400">Клиенты не найдены.</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Клиент</th>
                <th className="px-6 py-4">Телефон</th>
                <th className="px-6 py-4">Визиты</th>
                <th className="px-6 py-4">Выручка (LTV)</th>
                <th className="px-6 py-4">Статус</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {clients.map((c) => (
                <tr key={c.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="px-6 py-4 font-semibold text-white flex items-center space-x-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-pink-500/20 to-purple-500/20 text-pink-400 font-bold flex items-center justify-center">
                      {c.name?.[0] || 'C'}
                    </div>
                    <span>{c.name || 'Гость'}</span>
                  </td>
                  <td className="px-6 py-4 text-slate-400">{c.phone || '—'}</td>
                  <td className="px-6 py-4 font-medium">{c.total_visits}</td>
                  <td className="px-6 py-4 font-bold text-emerald-400">{Number(c.total_spent).toLocaleString()} ₽</td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        c.status === 'regular'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : c.status === 'at_risk'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {c.status === 'regular' ? 'Постоянный' : c.status === 'at_risk' ? 'В зоне риска' : c.status}
                    </span>
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
