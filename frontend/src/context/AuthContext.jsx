import { createContext, useContext, useState, useEffect } from 'react';
import client from '../api/client';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on mount if a token exists
  useEffect(() => {
    const token = localStorage.getItem('access');
    if (!token) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const profile = await client.get('/users/profile/');
        if (!cancelled) setUser(profile.data);
      } catch (e) {
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const login = async (reg_number, password) => {
    const res = await client.post('/users/login/', { reg_number, password });
    localStorage.setItem('access', res.data.access);
    localStorage.setItem('refresh', res.data.refresh);
    const profile = await client.get('/users/profile/');
    setUser(profile.data);
    return profile.data;
  };

  const register = async (phone_number, username, password) => {
    await client.post('/users/register/', { phone_number, username, password });
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);