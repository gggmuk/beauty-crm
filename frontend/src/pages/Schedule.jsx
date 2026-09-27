import React, { useEffect, useState } from 'react';
import { Clock, Save, Coffee, CheckCircle } from 'lucide-react';
import api from '../api/client';

const DAYS = [
  'Понедельник',
  'Вторник',
  'Среда',
  'Четверг',
  'Пятница',
  'Суббота',
  'Воскресенье',
];

export const Schedule = () => {
  const [schedules, setSchedules] = useState(
    DAYS.map((_, i) => ({
      day_of_week: i,
      start_time: '10:00',
      end_time: '19:00',
      is_working_day: i < 5,
    }))
  );

  const [bufferMinutes, setBufferMinutes] = useState(15);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        const [schedRes, tenantRes] = await Promise.all([
          api.get('/schedules'),
          api.get('/tenants/me'),
        ]);
        if (schedRes.data && schedRes.data.length > 0) {
          const mapped = DAYS.map((_, i) => {
            const found = schedRes.data.find((s) => s.day_of_week === i);
            return (
              found || {
                day_of_week: i,
                start_time: '10:00',
                end_time: '19:00',
                is_working_day: false,
              }
            );
          });
          setSchedules(mapped);
        }
        if (tenantRes.data) {
          setBufferMinutes(tenantRes.data.buffer_minutes || 15);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchSchedule();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSavedSuccess(false);
    try {
      await Promise.all([
        api.post('/schedules/batch', schedules),
        api.patch('/tenants/me', { buffer_minutes: Number(bufferMinutes) }),
      ]);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      alert('Ошибка при сохранении расписания');
    } finally {
      setSaving(false);
    }
  };

  const updateDay = (index, field, value) => {
    const copy = [...schedules];
    copy[index][field] = value;
    setSchedules(copy);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gradient">График работы и Слоты</h1>
          <p className="text-sm text-slate-400">Настройка рабочих дней, часов и буферного времени</p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 font-semibold text-white text-sm flex items-center space-x-2 shadow-lg shadow-pink-500/25 disabled:opacity-50"
        >
          {savedSuccess ? <CheckCircle className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
          <span>{saving ? 'Сохранение...' : savedSuccess ? 'Сохранено!' : 'Сохранить график'}</span>
        </button>
      </div>

      {/* Buffer Time Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
            <Coffee className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Буферное время между клиентами</h3>
            <p className="text-xs text-slate-400">Время на дезинфекцию и перерыв после каждой записи</p>
          </div>
        </div>

        <select
          value={bufferMinutes}
          onChange={(e) => setBufferMinutes(Number(e.target.value))}
          className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none"
        >
          <option value={0}>Без буфера (0 мин)</option>
          <option value={10}>10 минут</option>
          <option value={15}>15 минут (рекомендуется)</option>
          <option value={20}>20 минут</option>
          <option value={30}>30 минут</option>
        </select>
      </div>

      {/* 7 Days List */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-white mb-4">Рабочая неделя</h2>

        <div className="space-y-3">
          {schedules.map((item, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border transition-all flex items-center justify-between ${
                item.is_working_day
                  ? 'bg-slate-900/80 border-slate-800'
                  : 'bg-slate-950/40 border-slate-900 opacity-60'
              }`}
            >
              <div className="flex items-center space-x-4 w-48">
                <input
                  type="checkbox"
                  checked={item.is_working_day}
                  onChange={(e) => updateDay(idx, 'is_working_day', e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-pink-500 focus:ring-pink-500"
                />
                <span className="font-semibold text-white">{DAYS[idx]}</span>
              </div>

              {item.is_working_day ? (
                <div className="flex items-center space-x-3">
                  <input
                    type="time"
                    value={item.start_time?.slice(0, 5) || '10:00'}
                    onChange={(e) => updateDay(idx, 'start_time', e.target.value)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none"
                  />
                  <span className="text-slate-400">—</span>
                  <input
                    type="time"
                    value={item.end_time?.slice(0, 5) || '19:00'}
                    onChange={(e) => updateDay(idx, 'end_time', e.target.value)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none"
                  />
                </div>
              ) : (
                <span className="text-xs text-rose-400 font-medium uppercase tracking-wider">Выходной</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
