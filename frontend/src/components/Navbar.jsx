import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 font-bold text-white hover:text-blue-400 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="22" height="22" aria-hidden="true">
            <path d="M16 2 L28 7 L28 17 C28 23.5 22.5 29 16 30 C9.5 29 4 23.5 4 17 L4 7 Z" fill="#1d4ed8"/>
            <path d="M16 5 L25 9 L25 17 C25 22 21 26.5 16 27.5 C11 26.5 7 22 7 17 L7 9 Z" fill="#2563eb"/>
            <polyline points="11,16 14.5,19.5 21,12" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          </svg>
          <span>CodeSentinel</span>
        </button>

        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/new")}
            className={`text-sm transition-colors ${
              location.pathname === "/new"
                ? "text-blue-400"
                : "text-gray-400 hover:text-white"
            }`}
          >
            New Review
          </button>

          <div className="h-4 w-px bg-gray-700" />

          <span className="text-gray-500 text-sm hidden sm:block">{user?.email}</span>

          <button
            onClick={handleLogout}
            className="text-sm text-gray-400 hover:text-red-400 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>
    </nav>
  );
}
