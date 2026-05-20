import { createContext, useContext, useState, useCallback } from "react";
import { login as apiLogin, register as apiRegister } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("user"));
    } catch {
      return null;
    }
  });

  const login = useCallback(async (email, password) => {
    const { data } = await apiLogin(email, password);
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify({ id: data.user_id, email: data.email }));
    setToken(data.access_token);
    setUser({ id: data.user_id, email: data.email });
  }, []);

  const register = useCallback(async (email, password, githubUsername, githubToken) => {
    const { data } = await apiRegister(email, password, githubUsername, githubToken);
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify({ id: data.user_id, email: data.email }));
    setToken(data.access_token);
    setUser({ id: data.user_id, email: data.email });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
