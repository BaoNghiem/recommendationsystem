import React, { useState, useEffect, useRef } from 'react';
import { Search, Bell, User, LogOut, ShieldCheck, Home, Database, Users, X, ChevronDown, Film,
  Swords, Mountain, Clapperboard, Baby, Laugh, Fingerprint, BookOpen, Drama, Sparkles,
  Moon, Skull, Music, HelpCircle, Heart, Atom, Crosshair, Shield, Wheat, UserCircle,
  Loader2, BarChart3, UserCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from '../api/axios';
import { fixTitle } from '../utils/formatTitle';

// ── Genre icons & data ────────────────────────────────────
const GENRE_ITEMS = [
  { key: "action",      label: "Action",      icon: Swords },
  { key: "adventure",   label: "Adventure",   icon: Mountain },
  { key: "animation",   label: "Animation",   icon: Clapperboard },
  { key: "childrens",   label: "Children's",  icon: Baby },
  { key: "comedy",      label: "Comedy",      icon: Laugh },
  { key: "crime",       label: "Crime",       icon: Fingerprint },
  { key: "documentary", label: "Documentary", icon: BookOpen },
  { key: "drama",       label: "Drama",       icon: Drama },
  { key: "fantasy",     label: "Fantasy",     icon: Sparkles },
  { key: "film_noir",   label: "Film-Noir",   icon: Moon },
  { key: "horror",      label: "Horror",      icon: Skull },
  { key: "musical",     label: "Musical",     icon: Music },
  { key: "mystery",     label: "Mystery",     icon: HelpCircle },
  { key: "romance",     label: "Romance",     icon: Heart },
  { key: "sci_fi",      label: "Sci-Fi",      icon: Atom },
  { key: "thriller",    label: "Thriller",    icon: Crosshair },
  { key: "war",         label: "War",         icon: Shield },
  { key: "western",     label: "Western",     icon: Wheat },
];

const Navbar = ({ onOpenLogin, currentPage = 'home', onNavigate, onSearch, onGenreSelect }) => {
  const { user, isLoggedIn, isAdmin, logout } = useAuth();
  const [isScrolled, setIsScrolled]   = useState(false);
  const [showMenu, setShowMenu]       = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showGenre, setShowGenre]     = useState(false);

  // ── Dropdown suggestion states ──
  const [suggestions, setSuggestions]       = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestLoading, setSuggestLoading] = useState(false);

  const genreTimeout  = useRef(null);
  const genreRef      = useRef(null);
  const searchTimeout = useRef(null);
  const searchRef     = useRef(null);
  const suggestAbort  = useRef(null);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 0);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // ── Close genre dropdown on outside click ──
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (genreRef.current && !genreRef.current.contains(e.target)) {
        setShowGenre(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Cleanup ALL timeouts & abort controllers on unmount ──
  useEffect(() => {
    return () => {
      clearTimeout(searchTimeout.current);
      clearTimeout(genreTimeout.current);
      if (suggestAbort.current) suggestAbort.current.abort();
    };
  }, []);

  const handleGenreEnter = () => {
    clearTimeout(genreTimeout.current);
    setShowGenre(true);
  };
  const handleGenreLeave = () => {
    genreTimeout.current = setTimeout(() => setShowGenre(false), 200);
  };

  // ── Fetch live suggestions (debounced 300ms) ──
  const fetchSuggestions = (value) => {
    // Cancel any in-flight request
    if (suggestAbort.current) suggestAbort.current.abort();

    if (!value.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      setSuggestLoading(false);
      return;
    }

    setSuggestLoading(true);
    const controller = new AbortController();
    suggestAbort.current = controller;

    axios.get(`/movies/search/suggest?q=${encodeURIComponent(value.trim())}&limit=6`, {
      signal: controller.signal,
    })
      .then((res) => {
        setSuggestions(res.data || []);
        setShowSuggestions(true);
        setSuggestLoading(false);
      })
      .catch((err) => {
        if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
          console.error('[Navbar Suggest]', err.message);
        }
        setSuggestLoading(false);
      });
  };

  // ── Handle search input change ──
  const handleSearchChange = (value) => {
    setSearchQuery(value);
    clearTimeout(searchTimeout.current);

    if (!value.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      setSuggestLoading(false);
      return;
    }

    // Debounce 300ms before fetching suggestions
    searchTimeout.current = setTimeout(() => {
      fetchSuggestions(value);
    }, 300);
  };

  // ── Submit search (Enter or click search icon) → navigate to SearchPage ──
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    clearTimeout(searchTimeout.current);
    if (suggestAbort.current) suggestAbort.current.abort();

    const q = searchQuery.trim();
    if (q) {
      setShowSuggestions(false);
      onSearch?.(q);
      onNavigate?.('search');
    }
  };

  // ── Click a suggestion item → navigate to SearchPage ──
  const handleSuggestionClick = (movie) => {
    setSearchQuery(movie.title);
    setShowSuggestions(false);
    clearTimeout(searchTimeout.current);
    if (suggestAbort.current) suggestAbort.current.abort();
    onSearch?.(movie.title);
    onNavigate?.('search');
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
    setSuggestLoading(false);
    clearTimeout(searchTimeout.current);
    if (suggestAbort.current) suggestAbort.current.abort();
    onSearch?.('');
  };

  const handleLogout = () => {
    logout();
    setShowMenu(false);
    onNavigate?.('home');
  };

  const handleGenreClick = (genre) => {
    setShowGenre(false);
    onGenreSelect?.(genre);
  };

  const navLink = (page, label, icon) => {
    const active = currentPage === page;
    return (
      <li
        onClick={() => onNavigate?.(page)}
        className={`cursor-pointer transition flex items-center gap-1.5 text-sm
          ${active ? 'text-white font-bold' : 'text-gray-400 hover:text-white'}`}
      >
        {icon}
        {label}
      </li>
    );
  };

  return (
    <nav className={`fixed top-0 w-full z-50 transition-all duration-300
      flex items-center justify-between px-4 py-3 lg:px-12
      ${isScrolled ? 'bg-zinc-950/95 backdrop-blur-md shadow-lg' : 'bg-transparent'}`}
    >
      {/* ── Left: Logo + Nav links ── */}
      <div className="flex items-center space-x-8">
        <h1
          onClick={() => { onNavigate?.('home'); handleClearSearch(); }}
          className="text-red-600 text-2xl lg:text-3xl font-extrabold tracking-tighter uppercase
                     select-none cursor-pointer hover:text-red-500 transition"
        >
          Recommender System
        </h1>
        <ul className="hidden lg:flex items-center space-x-5">
          {navLink('home', 'Home', <Home size={14} />)}

          {/* ━━━ THE LOAI DROPDOWN ━━━ */}
          <li
            ref={genreRef}
            className="relative"
            onMouseEnter={handleGenreEnter}
            onMouseLeave={handleGenreLeave}
          >
            <button
              className={`flex items-center gap-1 text-sm cursor-pointer transition
                ${currentPage === 'genre' ? 'text-white font-bold' : 'text-gray-400 hover:text-white'}`}
            >
              <Film size={14} />
              The loai
              <ChevronDown size={12} className={`transition-transform duration-200 ${showGenre ? 'rotate-180' : ''}`} />
            </button>

            {/* ── MEGA MENU DROPDOWN (Glassmorphism + smooth transition) ── */}
            <div
              className={`absolute left-0 top-full mt-3 w-[520px]
                         bg-zinc-900/80 backdrop-blur-xl
                         border border-white/10 rounded-2xl
                         shadow-2xl shadow-black/60
                         overflow-hidden z-[200]
                         transition-all duration-300 ease-out origin-top
                         ${showGenre
                           ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto'
                           : 'opacity-0 scale-95 -translate-y-2 pointer-events-none'}`}
              onMouseEnter={handleGenreEnter}
              onMouseLeave={handleGenreLeave}
            >
              {/* Gradient accent bar */}
              <div className="h-0.5 w-full bg-gradient-to-r from-red-600 via-rose-500 to-orange-500" />

              <div className="p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Film size={16} className="text-red-400" />
                  <span className="text-sm font-semibold text-white">Kham pha theo the loai</span>
                  <span className="text-xs text-gray-500 ml-auto">18 the loai</span>
                </div>

                {/* Genre Grid: 3 columns */}
                <div className="grid grid-cols-3 gap-1.5">
                  {GENRE_ITEMS.map((g) => {
                    const Icon = g.icon;
                    return (
                      <button
                        key={g.key}
                        onClick={() => handleGenreClick(g)}
                        className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl
                                   text-gray-300 text-sm
                                   hover:bg-white/10 hover:text-white
                                   transition-all duration-150 group text-left"
                      >
                        <div className="w-7 h-7 rounded-lg bg-white/5 group-hover:bg-red-600/20
                                        flex items-center justify-center transition-colors shrink-0">
                          <Icon size={14} className="text-gray-400 group-hover:text-red-400 transition-colors" />
                        </div>
                        <span className="truncate">{g.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </li>

          {isAdmin && navLink('dashboard', 'Dashboard', <BarChart3 size={14} />)}
          {isAdmin && navLink('admin', 'Quan ly phim', <Database size={14} />)}
          {isAdmin && navLink('people', 'Dien vien', <UserCircle2 size={14} />)}
          {isAdmin && navLink('users', 'Quan ly nguoi dung', <Users size={14} />)}
        </ul>
      </div>

      {/* ── Right: Search + Auth ── */}
      <div className="flex items-center space-x-3">
        {/* Movie Search — with live dropdown */}
        <div ref={searchRef} className="relative">
          <form onSubmit={handleSearchSubmit}
              className="flex items-center bg-black/50 border border-white/10 rounded-lg px-3 py-1.5
                         focus-within:border-red-500/50 transition-colors">
              <Search
                size={15}
                className="text-gray-400 shrink-0 cursor-pointer hover:text-white transition"
                onClick={handleSearchSubmit}
              />
              <input
                type="text"
                id="search-movies"
                placeholder="Tim phim..."
                className="bg-transparent border-none outline-none text-sm ml-2 w-28 sm:w-40 text-white placeholder-gray-500"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={() => {
                  if (suggestions.length > 0) setShowSuggestions(true);
                }}
              />
              {suggestLoading && (
                <Loader2 size={13} className="text-gray-400 animate-spin ml-1 shrink-0" />
              )}
              {searchQuery && !suggestLoading && (
                <X
                  size={14}
                  className="text-gray-400 hover:text-white cursor-pointer ml-1 shrink-0"
                  onClick={handleClearSearch}
                />
              )}
            </form>

          {/* ── Live suggestion dropdown ── */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 w-[300px]
                            bg-zinc-900/95 backdrop-blur-xl border border-white/10
                            rounded-xl shadow-2xl shadow-black/60 overflow-hidden z-[300]
                            animate-in slide-in-from-top-2 duration-200">
              {/* Accent bar */}
              <div className="h-0.5 w-full bg-gradient-to-r from-red-600 to-rose-500" />

              <div className="py-1">
                {suggestions.map((movie) => (
                  <button
                    key={movie.movie_id}
                    onClick={() => handleSuggestionClick(movie)}
                    className="w-full flex items-center gap-3 px-4 py-2.5
                               hover:bg-white/10 transition-colors text-left group"
                  >
                    <div className="w-8 h-8 rounded-lg bg-white/5 group-hover:bg-red-600/20
                                    flex items-center justify-center shrink-0 transition-colors">
                      <Film size={14} className="text-gray-400 group-hover:text-red-400 transition-colors" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-white font-medium truncate group-hover:text-red-400 transition-colors">
                        {fixTitle(movie.title)}
                      </p>
                      <p className="text-[10px] text-gray-500 truncate">
                        {movie.genres_orig?.split('|').join(' · ')}
                      </p>
                    </div>
                  </button>
                ))}
              </div>

              {/* Footer: view all results */}
              <button
                onClick={handleSearchSubmit}
                className="w-full px-4 py-2.5 text-xs text-gray-400 hover:text-white
                           hover:bg-white/5 transition-colors border-t border-white/5
                           flex items-center justify-center gap-1"
              >
                <Search size={12} />
                Xem tat ca ket qua cho "{searchQuery}"
              </button>
            </div>
          )}

          {/* Empty suggestion state */}
          {showSuggestions && !suggestLoading && suggestions.length === 0 && searchQuery.trim() && (
            <div className="absolute top-full left-0 right-0 mt-2 w-[300px]
                            bg-zinc-900/95 backdrop-blur-xl border border-white/10
                            rounded-xl shadow-2xl shadow-black/60 overflow-hidden z-[300]">
              <div className="h-0.5 w-full bg-gradient-to-r from-red-600 to-rose-500" />
              <div className="px-4 py-4 text-center">
                <p className="text-sm text-gray-400">Khong tim thay phim nao</p>
                <p className="text-xs text-gray-500 mt-1">Thu voi tu khoa khac</p>
              </div>
            </div>
          )}
        </div>

        <Bell size={20} className="cursor-pointer text-gray-300 hover:text-white transition hidden sm:block" />

        {/* Auth Button */}
        {!isLoggedIn ? (
          <button
            onClick={onOpenLogin}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white
                       text-sm font-semibold px-4 py-2 rounded-lg transition-all
                       shadow-md shadow-red-900/30 active:scale-95"
          >
            <User size={15} />
            Dang nhap
          </button>
        ) : (
          <div className="relative">
            <button
              onClick={() => setShowMenu(p => !p)}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/15
                         border border-white/10 rounded-lg px-3 py-2 text-sm transition"
            >
              <div className="w-6 h-6 rounded-full bg-red-600 flex items-center justify-center text-xs font-bold">
                {user.email?.[0]?.toUpperCase() ?? 'U'}
              </div>
              <span className="hidden sm:block text-white max-w-[120px] truncate text-xs">
                {user.email}
              </span>
              {isAdmin && <ShieldCheck size={13} className="text-amber-400" />}
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-2 w-52 bg-zinc-900/95 backdrop-blur-xl
                              border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-white/10">
                  <p className="text-xs text-gray-400">Dang nhap voi</p>
                  <p className="text-sm text-white font-medium truncate">{user.email}</p>
                  <p className="text-xs mt-0.5">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                      ${isAdmin ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'}`}>
                      {user.role}
                    </span>
                    <span className="ml-1 text-gray-500">ID: {user.user_id}</span>
                  </p>
                </div>

                {isAdmin && (
                  <>
                    <button
                      onClick={() => { onNavigate?.('dashboard'); setShowMenu(false); }}
                      className="w-full flex items-center gap-2 px-4 py-3 text-sm text-emerald-400
                                 hover:bg-emerald-500/10 transition border-b border-white/5"
                    >
                      <BarChart3 size={15} />
                      Dashboard
                    </button>
                    <button
                      onClick={() => { onNavigate?.('admin'); setShowMenu(false); }}
                      className="w-full flex items-center gap-2 px-4 py-3 text-sm text-amber-400
                                 hover:bg-amber-500/10 transition border-b border-white/5"
                    >
                      <Database size={15} />
                      Quan ly phim
                    </button>
                    <button
                      onClick={() => { onNavigate?.('people'); setShowMenu(false); }}
                      className="w-full flex items-center gap-2 px-4 py-3 text-sm text-violet-400
                                 hover:bg-violet-500/10 transition border-b border-white/5"
                    >
                      <UserCircle2 size={15} />
                      Dien vien & Dao dien
                    </button>
                    <button
                      onClick={() => { onNavigate?.('users'); setShowMenu(false); }}
                      className="w-full flex items-center gap-2 px-4 py-3 text-sm text-violet-400
                                 hover:bg-violet-500/10 transition border-b border-white/5"
                    >
                      <Users size={15} />
                      Quan ly nguoi dung
                    </button>
                  </>
                )}

                <button
                  onClick={() => { onNavigate?.('profile'); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-4 py-3 text-sm text-gray-300
                             hover:bg-white/10 transition border-b border-white/5"
                >
                  <UserCircle size={15} />
                  Ho so ca nhan
                </button>

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-3 text-sm text-red-400
                             hover:bg-red-500/10 transition"
                >
                  <LogOut size={15} />
                  Dang xuat
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
