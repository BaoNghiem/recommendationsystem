import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);   // { user_id, email, role, account_type }
  const [token, setToken]     = useState(null);
  const [loading, setLoading] = useState(true);   // đang khôi phục session

  // ── Khôi phục session từ localStorage khi app load ────────
  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    const savedUser  = localStorage.getItem('user');
    if (savedToken && savedUser) {
      try {
        // Kiểm tra token còn hạn không (decode payload)
        const payload = JSON.parse(atob(savedToken.split('.')[1]));
        const isExpired = payload.exp && payload.exp * 1000 < Date.now();
        if (isExpired) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        } else {
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
        }
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);


  // ── Lắng nghe sự kiện token hết hạn từ axios interceptor ──
  useEffect(() => {
    const onLogout = () => logout();
    window.addEventListener('auth:logout', onLogout);
    return () => window.removeEventListener('auth:logout', onLogout);
  }, []);

  // ── Login ──────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const data = res.data;                          // TokenResponse
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify({
      user_id:      data.user_id,
      email:        data.email,
      role:         data.role,
      account_type: data.account_type,
    }));
    setToken(data.access_token);
    setUser({ user_id: data.user_id, email: data.email, role: data.role, account_type: data.account_type });
    return data;
  }, []);

  // ── Register ───────────────────────────────────────────────
  const register = useCallback(async (email, password) => {
    const res = await api.post('/auth/register', { email, password });
    return res.data;  // { message: "..." }
  }, []);

  // ── Logout ─────────────────────────────────────────────────
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  }, []);

  const isAdmin = user?.role === 'admin';
  const isLoggedIn = !!user;

  return (
    <AuthContext.Provider value={{ user, token, loading, isLoggedIn, isAdmin, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
