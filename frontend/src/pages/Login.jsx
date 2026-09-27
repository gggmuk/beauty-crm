import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    telegram_user_id: '',
    phone: '',
    password: '',
  });

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isRegister) {
        await register({
          ...formData,
          telegram_user_id: Number(formData.telegram_user_id),
        });
      } else {
        await login(formData.telegram_user_id, formData.password);
      }
      navigate('/');
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка авторизации');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Ambient Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-pink-500/20 rounded-full blur-[128px] pointer-events-none" />

      <div className="glass-panel w-full max-w-md p-8 rounded-3xl border border-slate-800 space-y-6 relative z-10 shadow-2xl">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center font-bold text-xl text-white mx-auto shadow-lg shadow-pink-500/30">
            ✨
          </div>
          <h1 className="text-2xl font-bold text-gradient">BeautyCRM</h1>
          <p className="text-xs text-slate-400">
            {isRegister ? 'Регистрация нового мастера' : 'Вход в личный кабинет мастера'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs text-slate-400 mb-1">Название Студии / Имя Мастера</label>
              <input
                type="text"
                required
                placeholder="Елена Маникюр"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-pink-500"
              />
            </div>
          )}

          <div>
            <label className="block text-xs text-slate-400 mb-1">Telegram User ID</label>
            <input
              type="number"
              required
              placeholder="123456789"
              value={formData.telegram_user_id}
              onChange={(e) => setFormData({ ...formData, telegram_user_id: e.target.value })}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-pink-500 font-mono"
            />
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs text-slate-400 mb-1">Телефон</label>
              <input
                type="text"
                placeholder="+7 (999) 000-00-00"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-pink-500"
              />
            </div>
          )}

          <div>
            <label className="block text-xs text-slate-400 mb-1">Пароль</label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-pink-500"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 font-bold text-white text-sm shadow-lg shadow-pink-500/25 hover:opacity-90 transition-opacity"
          >
            {isRegister ? 'Зарегистрироваться' : 'Войти'}
          </button>
        </form>

        <div className="text-center pt-2">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-xs text-pink-400 hover:underline"
          >
            {isRegister ? 'Уже есть аккаунт? Войти' : 'Нет аккаунта? Зарегистрироваться'}
          </button>
        </div>
      </div>
    </div>
  );
};
