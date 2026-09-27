import React, { useEffect, useState } from 'react';
import { Calendar, Users, DollarSign, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import api from '../api/client';

export const Dashboard = () => {
  const [appointments, setAppointments] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [apptsRes, clientsRes] = await Promise.all([
          api.get('/appointments'),
          api.get('/clients'),
        ]);
        setAppointments(apptsRes.data);
        setClients(clientsRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const confirmedAppts = appointments.filter((a) => a.status === 'confirmed');
  const todayStr = new Date().toISOString().split('T')[0];
  const todayAppts = appointments.filter((a) => a.start_time?.startsWith(todayStr));

  const totalLtv = clients.reduce((acc, c) => acc + (Number(c.total_spent) || 0), 0);

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="glass-panel p-8 rounded-3xl relative overflow-hidden border border-pink-500/20">
        <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-pink-500/10 rounded-full blur-3xl pointer-events-none" />
        <h1 className="text-3xl font-bold text-gradient mb-2">Обзор Кабинета</h1>
        <p className="text-slate-400">Статистика записей, выручки и клиентов на сегодня.</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-pink-500/20 text-pink-400 flex items-center justify-center">
            <Calendar className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Записей сегодня</p>
            <p className="text-2xl font-bold text-white">{todayAppts.length}</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Подтверждённые</p>
            <p className="text-2xl font-bold text-white">{confirmedAppts.length}</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Всего клиентов</p>
            <p className="text-2xl font-bold text-white">{clients.length}</p>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Общий оборот LTV</p>
            <p className="text-2xl font-bold text-white">{totalLtv.toLocaleString()} ₽</p>
          </div>
        </div>
      </div>

      {/* Today's Appointments List */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Clock className="w-5 h-5 text-pink-400" />
          <span>Ближайшие записи</span>
        </h2>

        {loading ? (
          <div className="py-8 text-center text-slate-400">Загрузка данных...</div>
        ) : todayAppts.length === 0 ? (
          <div className="py-8 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
            <AlertCircle className="w-8 h-8 text-slate-500 mx-auto mb-2" />
            <p>На сегодня записей пока нет.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todayAppts.map((appt) => (
              <div
                key={appt.id}
                className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between"
              >
                <div className="flex items-center space-x-4">
                  <div className="text-sm font-semibold text-pink-400 bg-pink-500/10 px-3 py-1.5 rounded-lg">
                    {new Date(appt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{appt.client?.name || 'Гость'}</h3>
                    <p className="text-xs text-slate-400">{appt.service?.title || 'Услуга'}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium uppercase tracking-wider ${
                      appt.status === 'confirmed'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : appt.status === 'pending_payment'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-rose-500/20 text-rose-400'
                    }`}
                  >
                    {appt.status}
                  </span>
                  <span className="text-sm font-bold text-slate-200">
                    {appt.service?.price ? `${appt.service.price} ₽` : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
