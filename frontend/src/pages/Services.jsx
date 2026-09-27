import React, { useEffect, useState } from 'react';
import { Plus, Trash2, Edit2, Sparkles, Clock, DollarSign } from 'lucide-react';
import api from '../api/client';

export const Services = () => {
  const [services, setServices] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [newService, setNewService] = useState({
    title: '',
    duration_minutes: 60,
    price: 1500,
    prepayment_amount: 500,
    category_id: '',
  });

  const fetchData = async () => {
    try {
      const [servRes, catRes] = await Promise.all([
        api.get('/services'),
        api.get('/services/categories'),
      ]);
      setServices(servRes.data);
      setCategories(catRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateService = async (e) => {
    e.preventDefault();
    try {
      await api.post('/services', {
        ...newService,
        category_id: newService.category_id || null,
      });
      setShowModal(false);
      setNewService({ title: '', duration_minutes: 60, price: 1500, prepayment_amount: 500, category_id: '' });
      fetchData();
    } catch (err) {
      alert('Ошибка при создании услуги');
    }
  };

  const handleDeleteService = async (id) => {
    if (confirm('Удалить услугу?')) {
      try {
        await api.delete(`/services/${id}`);
        fetchData();
      } catch (err) {
        alert('Ошибка при удалении');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gradient">Услуги и Цены</h1>
          <p className="text-sm text-slate-400">Настройка прайс-листа и сумм предоплаты</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 font-semibold text-white text-sm flex items-center space-x-2 shadow-lg shadow-pink-500/25"
        >
          <Plus className="w-4 h-4" />
          <span>Добавить услугу</span>
        </button>
      </div>

      {/* Grid of Services */}
      {loading ? (
        <div className="py-12 text-center text-slate-400">Загрузка прайс-листа...</div>
      ) : services.length === 0 ? (
        <div className="glass-panel p-12 text-center text-slate-400 rounded-2xl border border-slate-800">
          Услуги пока не добавлены.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((s) => (
            <div key={s.id} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 relative group">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg text-white">{s.title}</h3>
                  <p className="text-xs text-pink-400 font-medium mt-0.5">
                    {s.duration_minutes} минут
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteService(s.id)}
                  className="p-2 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 block">Стоимость</span>
                  <span className="text-xl font-bold text-white">{s.price} ₽</span>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Предоплата</span>
                  <span className="text-sm font-semibold text-emerald-400">{s.prepayment_amount} ₽</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-3xl border border-slate-700 space-y-6">
            <h2 className="text-xl font-bold text-white">Новая услуга</h2>

            <form onSubmit={handleCreateService} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Название услуги</label>
                <input
                  type="text"
                  required
                  placeholder="Маникюр + Покрытие"
                  value={newService.title}
                  onChange={(e) => setNewService({ ...newService, title: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Длительность (мин)</label>
                  <input
                    type="number"
                    required
                    value={newService.duration_minutes}
                    onChange={(e) => setNewService({ ...newService, duration_minutes: Number(e.target.value) })}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Цена (₽)</label>
                  <input
                    type="number"
                    required
                    value={newService.price}
                    onChange={(e) => setNewService({ ...newService, price: Number(e.target.value) })}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Предоплата (₽)</label>
                <input
                  type="number"
                  value={newService.prepayment_amount}
                  onChange={(e) => setNewService({ ...newService, prepayment_amount: Number(e.target.value) })}
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
                  Создать
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
