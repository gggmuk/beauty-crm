import React, { useState } from 'react';
import { Bot, Key, CheckCircle, ExternalLink, ShieldCheck } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export const BotSettings = () => {
  const { tenant, fetchProfile } = useAuth();
  const [botToken, setBotToken] = useState('');
  const [welcomeMessage, setWelcomeMessage] = useState(tenant?.welcome_message || '');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSetupBot = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/bot/setup', { bot_token: botToken });
      await fetchProfile();
      setSuccess(true);
      setBotToken('');
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      alert(err.response?.data?.detail || 'Ошибка при подключения бота');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateBranding = async (e) => {
    e.preventDefault();
    try {
      await api.patch('/tenants/me', { welcome_message: welcomeMessage });
      await fetchProfile();
      alert('Приветственное сообщение обновлено!');
    } catch (err) {
      alert('Ошибка при сохранении');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gradient">Конструктор Telegram Бота</h1>
        <p className="text-sm text-slate-400">Подключение токена от @BotFather и брендинг</p>
      </div>

      {/* Connection Status Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-500/20 to-pink-500/20 text-blue-400 flex items-center justify-center">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-white text-lg">
              {tenant?.bot_username ? `@${tenant.bot_username}` : 'Бот не подключен'}
            </h3>
            <p className="text-xs text-slate-400">
              {tenant?.bot_username ? 'Статус: Подключен и готов приём записей' : 'Вставьте токен бота ниже'}
            </p>
          </div>
        </div>

        {tenant?.bot_username && (
          <a
            href={`https://t.me/${tenant.bot_username}`}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 rounded-xl bg-blue-500/20 text-blue-400 font-semibold text-xs flex items-center space-x-2 border border-blue-500/30 hover:bg-blue-500/30"
          >
            <span>Открыть в Telegram</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      {/* Setup Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Token Input */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Key className="w-5 h-5 text-pink-400" />
            <span>Токен Telegram API</span>
          </h2>

          <p className="text-xs text-slate-400">
            Создайте бота у <a href="https://t.me/BotFather" target="_blank" rel="noreferrer" className="text-pink-400 underline">@BotFather</a> и скопируйте токен сюда. Токен зашифрован ключом AES-256.
          </p>

          <form onSubmit={handleSetupBot} className="space-y-4">
            <input
              type="password"
              required
              placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
              value={botToken}
              onChange={(e) => setBotToken(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500 font-mono"
            />

            <button
              type="submit"
              disabled={saving}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 font-semibold text-white text-sm flex items-center justify-center space-x-2 shadow-lg shadow-pink-500/20 disabled:opacity-50"
            >
              {success ? <CheckCircle className="w-4 h-4 text-emerald-300" /> : <ShieldCheck className="w-4 h-4" />}
              <span>{saving ? 'Проверка...' : success ? 'Бот успешно привязан!' : 'Привязать Токен'}</span>
            </button>
          </form>
        </div>

        {/* Welcome Message Customization */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white">Приветственное Сообщение</h2>
          <p className="text-xs text-slate-400">Сообщение, которое получает клиент при старте (/start)</p>

          <form onSubmit={handleUpdateBranding} className="space-y-4">
            <textarea
              rows={4}
              value={welcomeMessage}
              onChange={(e) => setWelcomeMessage(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-pink-500"
            />

            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 font-semibold text-white text-sm border border-slate-700"
            >
              Сохранить Приветствие
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
