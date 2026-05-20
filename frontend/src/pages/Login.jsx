import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, "", githubToken || undefined);
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="36" height="36" aria-hidden="true">
              <path d="M16 2 L28 7 L28 17 C28 23.5 22.5 29 16 30 C9.5 29 4 23.5 4 17 L4 7 Z" fill="#1d4ed8"/>
              <path d="M16 5 L25 9 L25 17 C25 22 21 26.5 16 27.5 C11 26.5 7 22 7 17 L7 9 Z" fill="#2563eb"/>
              <polyline points="11,16 14.5,19.5 21,12" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </svg>
            <h1 className="text-2xl font-bold text-white">CodeSentinel</h1>
          </div>
          <p className="text-gray-400 text-sm">Autonomous GitHub PR code review powered by Claude AI</p>
        </div>

        {/* Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          {/* Tab switch */}
          <div className="flex mb-6 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => { setMode("login"); setError(""); }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                mode === "login" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setMode("register"); setError(""); }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                mode === "register" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Create Account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {mode === "register" && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  GitHub Token <span className="text-gray-500 font-normal">(optional — enables posting reviews to PRs)</span>
                </label>
                <input
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_..."
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            )}

            {error && (
              <div className="bg-red-900/40 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-lg transition-colors"
            >
              {loading ? "Please wait…" : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>
        </div>

        {/* Demo credentials box */}
        <div className="bg-gray-900/60 border border-gray-700 rounded-xl px-5 py-4 mt-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Demo Accounts</p>
          <div className="space-y-2">
            {[
              { email: "user1@codesentinel.dev", password: "password123" },
              { email: "user2@codesentinel.dev", password: "password123" },
            ].map((u) => (
              <button
                key={u.email}
                type="button"
                onClick={() => { setEmail(u.email); setPassword(u.password); setMode("login"); }}
                className="w-full flex items-center justify-between bg-gray-800/60 hover:bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 transition-colors group"
              >
                <span className="text-sm text-gray-300 font-mono">{u.email}</span>
                <span className="text-xs text-gray-500 group-hover:text-blue-400 transition-colors">click to fill</span>
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-600 mt-2">Password: <span className="font-mono text-gray-500">password123</span></p>
        </div>

      </div>
    </div>
  );
}
