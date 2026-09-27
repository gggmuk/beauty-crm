import React, { useEffect, useState } from 'react';
import { Calendar as CalendarIcon, Plus, Check, X, User, Clock, Phone } from 'lucide-react';
import api from '../api/client';

export const Appointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Manual booking modal state
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    service_id: '',
    client_name: '',
    client_phone: '',
    start_time: '',
    notes: '',
  });

  const fetchAppointments = async () => {
    try {
      const [apptsRes, servRes] = await Promise.all([
        api.get('/appointments'),
        api.get('/services'),
      ]);
      setAppointments(apptsRes.data);
      setServices(servRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const handleUpdateStatus = async (id, status) => {
    try {
      await api.patch(`/appointments/${id}`, { status });
      fetchAppointments();
    } catch (err) {
      alert('Ошибка при изменении статуса');
    }
  };

  const handleCreateManualBooking = async (e) => {
    e.preventDefault();
    try {
      const tenantRes = await api.get('/tenants/me');
      await api.post(`/appointments?tenant_id=${tenantRes.data.id}`, {
        ...formData,
        start_time: new Date(formData.start_time).toISOString(),
        source: 'manual',
      });
      setShowModal(false);
      setFormData({ service_id: '', client_name: '', client_phone: '', start_time: '', notes: '' });
      fetchAppointments();
    } catch (err) {
      alert('Ошибка создания записи');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gradient">Журнал Записей</h1>
          <p className="text-sm text-slate-400">Управление расписанием и ручная запись клиентов</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 font-semibold text-white text-sm flex items-center space-x-2 shadow-lg shadow-pink-500/25 hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          <span>Запись «с улицы»</span>
        </button>
      </div>

      {/* Appointments List */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        {loading ? (
          <div className="py-12 text-center text-slate-400">Загрузка журнала...</div>
        ) : appointments.length === 0 ? (
          <div className="py-12 text-center text-slate-400">Записи отсутствуют.</div>
        ) : (
          <div className="divide-y divide-slate-800">
            {appointments.map((appt) => (
              <div key={appt.id} className="py-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center text-xs">
                    <span className="font-bold text-pink-400">
                      {new Date(appt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {new Date(appt.start_time).toLocaleDateString([], { day: '2-digit', month: '2-digit' })}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-semibold text-white flex items-center space-x-2">
                      <span>{appt.client?.name || 'Гость'}</span>
                      {appt.client?.phone && (
                        <span className="text-xs font-normal text-slate-400 flex items-center">
                          <Phone className="w-3 h-3 mr-1" /> {appt.client.phone}
                        </span>
                      )}
                    </h3>
                    <p className="text-xs text-slate-400">{appt.service?.title || 'Услуга'}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      appt.status === 'confirmed'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : appt.status === 'completed'
                        ? 'bg-blue-500/20 text-blue-400'
                        : appt.status === 'pending_payment'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-rose-500/20 text-rose-400'
                    }`}
                  >
                    {appt.status}
                  </span>

                  {/* Actions */}
                  {appt.status !== 'completed' && appt.status !== 'cancelled' && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleUpdateStatus(appt.id, 'completed')}
                        className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                        title="Завершить визит"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleUpdateStatus(appt.id, 'cancelled')}
                        className="p-2 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20"
                        title="Отменить"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Manual Booking Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-3xl border border-slate-700 space-y-6">
            <h2 className="text-xl font-bold text-white">Добавить запись вручную</h2>

            <form onSubmit={handleCreateManualBooking} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Услуга</label>
                <select
                  required
                  value={formData.service_id}
                  onChange={(e) => setFormData({ ...formData, service_id: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
                >
                  <option value="">Выберите услугу</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.title} ({s.price} ₽, {s.duration_minutes} мин)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Имя клиента</label>
                <input
                  type="text"
                  required
                  placeholder="Анна"
                  value={formData.client_name}
                  onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Телефон</label>
                <input
                  type="text"
                  placeholder="+7 (999) 000-00-00"
                  value={formData.client_phone}
                  onChange={(e) => setFormData({ ...formData, client_phone: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Дата и время</label>
                <input
                  type="datetime-local"
                  required
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 font-semibold text-white text-sm"
                >
                  Сохранить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
