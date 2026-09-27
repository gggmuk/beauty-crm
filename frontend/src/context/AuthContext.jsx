import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      const res = await api.get('/tenants/me');
      setTenant(res.data);
    } catch (err) {
      setTenant(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('beautycrm_token');
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (telegram_user_id, password) => {
    const res = await api.post('/auth/login', { telegram_user_id: Number(telegram_user_id), password });
    localStorage.setItem('beautycrm_token', res.data.access_token);
    await fetchProfile();
  };

  const register = async (data) => {
    await api.post('/auth/register', data);
    await login(data.telegram_user_id, data.password);
  };

  const logout = () => {
    localStorage.removeItem('beautycrm_token');
    setTenant(null);
  };

  return (
    <AuthContext.Provider value={{ tenant, loading, login, register, logout, fetchProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
