import React, { useEffect, useState } from 'react';
import { useTelegram } from './hooks/useTelegram';
import { Sparkles, Calendar, Clock, CheckCircle2, ChevronRight, AlertCircle, ArrowLeft } from 'lucide-react';
import axios from 'axios';

export default function App() {
  const { user, tg } = useTelegram();
  const [tenantId, setTenantId] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [services, setServices] = useState([]);
  const [step, setStep] = useState(1); // 1: Service, 2: Date & Slot, 3: Confirm & Pay, 4: Success

  // Selected values
  const [selectedService, setSelectedService] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [clientName, setClientName] = useState('');
  const [clientPhone, setClientPhone] = useState('');
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [booking, setBooking] = useState(null);

  // Parse tenant_id from URL query string
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tid = params.get('tenant_id') || params.get('startapp');
    if (tid) setTenantId(tid);

    if (user) {
      setClientName(`${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Клиент');
    }
  }, [user]);

  // Fetch Services for Tenant
  useEffect(() => {
    if (!tenantId) return;
    axios.get(`/api/v1/services?tenant_id=${tenantId}`).then((res) => setServices(res.data)).catch(console.error);
  }, [tenantId]);

  // Fetch Slots when Date or Service changes
  useEffect(() => {
    if (!tenantId || !selectedService || !selectedDate) return;
    setLoadingSlots(true);
    axios
      .get(`/api/v1/appointments/slots?tenant_id=${tenantId}&service_id=${selectedService.id}&date=${selectedDate}`)
      .then((res) => setSlots(res.data))
      .catch(console.error)
      .finally(() => setLoadingSlots(false));
  }, [tenantId, selectedService, selectedDate]);

  const handleCreateBooking = async () => {
    if (!selectedSlot || !selectedService) return;
    try {
      const res = await axios.post(`/api/v1/appointments?tenant_id=${tenantId}`, {
        service_id: selectedService.id,
        start_time: selectedSlot.start_time,
        client_name: clientName,
        client_phone: clientPhone,
        client_telegram_id: user?.id || 0,
        source: 'twa',
      });
      setBooking(res.data);

      if (res.data.prepayment_amount > 0) {
        // Init Stripe Session
        const payRes = await axios.post('/api/v1/payments/create-session', {
          appointment_id: res.data.id,
        });
        if (payRes.data.checkout_url) {
          window.location.href = payRes.data.checkout_url;
          return;
        }
      }

      setStep(4); // Success step
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка бронирования');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 max-w-md mx-auto space-y-6">
      {/* Header Banner */}
      <div className="glass-card p-5 rounded-2xl border border-pink-500/20 text-center relative overflow-hidden">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center text-xl font-bold mx-auto mb-2 shadow-lg shadow-pink-500/30">
          ✨
        </div>
        <h1 className="text-xl font-bold text-gradient">Онлайн-Запись</h1>
        <p className="text-xs text-slate-400">Выберите услугу и удобное время</p>
      </div>

      {/* STEP 1: Select Service */}
      {step === 1 && (
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">1. Выберите услугу</h2>

          <div className="space-y-3">
            {services.map((s) => (
              <div
                key={s.id}
                onClick={() => {
                  setSelectedService(s);
                  setStep(2);
                }}
                className={`glass-card p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedService?.id === s.id
                    ? 'border-pink-500 bg-pink-500/10'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <h3 className="font-bold text-white text-base">{s.title}</h3>
                  <div className="flex items-center space-x-3 mt-1 text-xs text-slate-400">
                    <span className="flex items-center">
                      <Clock className="w-3.5 h-3.5 mr-1 text-pink-400" /> {s.duration_minutes} мин
                    </span>
                    {s.effective_prepayment > 0 && (
                      <span className="text-emerald-400 font-medium">
                        Предоплата: {s.effective_prepayment} ₽
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-right flex items-center space-x-2">
                  <span className="font-bold text-lg text-white">{s.price} ₽</span>
                  <ChevronRight className="w-5 h-5 text-slate-500" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STEP 2: Date & Time Slot Picker */}
      {step === 2 && (
        <div className="space-y-6">
          <button
            onClick={() => setStep(1)}
            className="text-xs text-slate-400 flex items-center space-x-1 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Назад к услугам</span>
          </button>

          <div className="glass-card p-4 rounded-2xl border border-slate-800 space-y-2">
            <span className="text-xs text-pink-400 font-semibold uppercase">Выбрано</span>
            <h2 className="text-lg font-bold text-white">{selectedService.title}</h2>
            <p className="text-xs text-slate-400">{selectedService.duration_minutes} мин · {selectedService.price} ₽</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              2. Выберите дату
            </label>
            <input
              type="date"
              value={selectedDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full px-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 text-white font-medium text-sm focus:outline-none focus:border-pink-500"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              3. Свободное время
            </label>

            {loadingSlots ? (
              <div className="py-8 text-center text-xs text-slate-400">Поиск слотов...</div>
            ) : slots.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400 glass-card rounded-2xl border border-slate-800">
                На эту дату нет свободных слотов.
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-2.5">
                {slots.map((slot, idx) => {
                  const timeStr = new Date(slot.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  return (
                    <button
                      key={idx}
                      disabled={!slot.is_available}
                      onClick={() => setSelectedSlot(slot)}
                      className={`py-3 px-2 rounded-xl text-sm font-bold transition-all border ${
                        selectedSlot?.start_time === slot.start_time
                          ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white border-transparent shadow-lg shadow-pink-500/25'
                          : slot.is_available
                          ? 'bg-slate-900 text-slate-200 border-slate-800 hover:border-slate-700'
                          : 'bg-slate-950 text-slate-600 border-slate-900 cursor-not-allowed opacity-40 line-through'
                      }`}
                    >
                      {timeStr}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {selectedSlot && (
            <button
              onClick={() => setStep(3)}
              className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-pink-500 to-purple-600 font-bold text-white text-base shadow-lg shadow-pink-500/25"
            >
              Продолжить запись
            </button>
          )}
        </div>
      )}

      {/* STEP 3: Client Info & Prepayment confirmation */}
      {step === 3 && (
        <div className="space-y-6">
          <button
            onClick={() => setStep(2)}
            className="text-xs text-slate-400 flex items-center space-x-1 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Назад к выбору времени</span>
          </button>

          <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
            <h3 className="font-bold text-lg text-white">Детали Записи</h3>
            <div className="text-xs text-slate-300 space-y-1">
              <p><span className="text-slate-400">Услуга:</span> {selectedService.title}</p>
              <p><span className="text-slate-400">Время:</span> {new Date(selectedSlot.start_time).toLocaleString()}</p>
              <p><span className="text-slate-400">Стоимость:</span> {selectedService.price} ₽</p>
              {selectedService.effective_prepayment > 0 && (
                <p className="text-emerald-400 font-semibold">
                  <span>К оплате сейчас (предоплата):</span> {selectedService.effective_prepayment} ₽
                </p>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Ваше Имя</label>
              <input
                type="text"
                required
                placeholder="Екатерина"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-pink-500"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Телефон для связи</label>
              <input
                type="tel"
                required
                placeholder="+7 (999) 000-00-00"
                value={clientPhone}
                onChange={(e) => setClientPhone(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-pink-500"
              />
            </div>

            <button
              onClick={handleCreateBooking}
              className="w-full py-4 rounded-2xl bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 font-bold text-white text-base shadow-xl shadow-pink-500/25 mt-4"
            >
              {selectedService.effective_prepayment > 0 ? 'Внести предоплату и записаться' : 'Подтвердить запись'}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Success Screen */}
      {step === 4 && (
        <div className="py-12 text-center space-y-6">
          <div className="w-20 h-20 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/30">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div>
            <h2 className="text-2xl font-bold text-white">Вы успешно записаны! 🎉</h2>
            <p className="text-xs text-slate-400 mt-2 max-w-xs mx-auto">
              Подтверждение и детали визита отправлены вам в Telegram бот.
            </p>
          </div>

          <button
            onClick={() => tg?.close()}
            className="px-8 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 font-semibold text-white text-sm border border-slate-700"
          >
            Закрыть окно
          </button>
        </div>
      )}
    </div>
  );
}
