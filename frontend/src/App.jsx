import React, { useState, useEffect, useCallback } from 'react';
import axios from './api/axios';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import MovieRow from './components/MovieRow';
import LoginModal from './components/LoginModal';
import MovieManagement from './pages/MovieManagement';
import UserManagement from './pages/admin/UserManagement';
import AdminDashboard from './pages/admin/AdminDashboard';
import GenrePage from './pages/GenrePage';
import SearchPage from './pages/SearchPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import Profile from './pages/Profile';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle, Sparkles, Search as SearchIcon, X } from 'lucide-react';
import { useAuth } from './context/AuthContext';

function AppInner() {
  const { user, isLoggedIn } = useAuth();

  // ── Page routing: 'home' | 'admin' | 'users' | 'dashboard' | 'genre' | 'search' | 'reset-password' ──
  const [currentPage, setCurrentPage] = useState('home');

  // ── Data states ──
  const [trending, setTrending]               = useState([]);
  const [latestMovies, setLatestMovies]       = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [searchResults, setSearchResults]     = useState([]);
  const [loading, setLoading]                 = useState(true);
  const [recLoading, setRecLoading]           = useState(false);
  const [searchLoading, setSearchLoading]     = useState(false);
  const [toast, setToast]                     = useState({ show: false, message: '' });
  const [refreshTrigger, setRefreshTrigger]   = useState(0);
  const [savedRatings, setSavedRatings]       = useState({});
  const [showLogin, setShowLogin]             = useState(false);
  const [aiStrategy, setAiStrategy]           = useState('');
  const [aiExplanation, setAiExplanation]     = useState('');
  const [searchQuery, setSearchQuery]         = useState('');
  const [activeGenre, setActiveGenre]         = useState(null); // { key, label }
  const [resetToken, setResetToken]           = useState(null);

  // ── Check URL params on mount for reset-password deep link ──
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const page = params.get('page');
    const token = params.get('token');
    if (page === 'reset-password' && token) {
      setResetToken(token);
      setCurrentPage('reset-password');
      // Clean URL without reload
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const showToast = (msg) => {
    setToast({ show: true, message: msg });
    setTimeout(() => setToast({ show: false, message: '' }), 3000);
  };

  // ── Khi user dang nhap → refresh recommendations ──
  useEffect(() => {
    if (isLoggedIn && user?.user_id) {
      setRefreshTrigger(p => p + 1);
    }
  }, [isLoggedIn, user]);

  // ── Fetch Trending + Latest (1 lan khi mount) ──
  useEffect(() => {
    async function fetchTrending() {
      setLoading(true);
      try {
        const res = await axios.get(`/trending?limit=15&_t=${Date.now()}`);
        setTrending(res.data);
      } catch (err) {
        console.error('[ERR] Trending:', err.message);
      }
      setLoading(false);
    }
    async function fetchLatest() {
      try {
        const res = await axios.get(`/latest?limit=10&_t=${Date.now()}`);
        setLatestMovies(res.data);
      } catch (err) {
        console.error('[ERR] Latest:', err.message);
      }
    }
    fetchTrending();
    fetchLatest();
  }, []);

  // ── Fetch Recommendations (khac nhau giua guest va logged-in) ──
  useEffect(() => {
    fetchRecommendations();
    if (isLoggedIn && user?.user_id) {
      fetchUserRatings();
    }
  }, [isLoggedIn, user?.user_id, refreshTrigger]);

  const fetchRecommendations = async () => {
    setRecommendations([]);
    setRecLoading(true);
    try {
      if (isLoggedIn && user?.user_id) {
        // === LOGGED IN: Hybrid/Content-Based/Popularity via AI engine ===
        const res = await axios.get(`/recommend/${user.user_id}?top_n=20&_t=${Date.now()}`);
        setRecommendations(res.data.recommendations || []);
        setAiStrategy(res.data.strategy || '');
        setAiExplanation(res.data.explanation || '');
      } else {
        // === GUEST: Popularity-based ===
        const res = await axios.get(`/popular?limit=20&_t=${Date.now()}`);
        setRecommendations(res.data.recommendations || []);
        setAiStrategy('popularity');
        setAiExplanation('Phim pho bien nhat');
      }
    } catch (err) {
      console.error('[ERR] Recommend:', err.message);
    }
    setRecLoading(false);
  };

  const fetchUserRatings = async () => {
    if (!isLoggedIn || !user?.user_id) return;
    try {
      const res = await axios.get(`/user-ratings/${user.user_id}?_t=${Date.now()}`);
      setSavedRatings(res.data);
    } catch (err) {
      console.error('[ERR] UserRatings:', err.message);
    }
  };

  // ── Rating handler (giu nguyen recommendation_stale logic) ──
  const handleRateAction = async (movieId, movieTitle, ratingValue) => {
    if (!isLoggedIn) {
      showToast('Vui long dang nhap de danh gia phim!');
      setShowLogin(true);
      return;
    }
    try {
      const res = await axios.post('/rate', {
        user_id: user.user_id,
        movie_id: movieId,
        rating: ratingValue,
      });
      showToast(`Da danh gia ${ratingValue} sao cho "${movieTitle}"!`);
      setSavedRatings(prev => ({ ...prev, [movieId]: ratingValue }));

      // Real-time refresh
      if (res.data?.recommendation_stale) {
        setRefreshTrigger(p => p + 1);
      }
    } catch (err) {
      console.error('[ERR] Rate:', err.message);
      showToast('Loi gui danh gia.');
    }
  };

  // ── Search handler (tu Navbar) ──
  // Navbar now handles debounce + suggestions internally.
  // This just stores the query; SearchPage does its own API call.
  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
    setActiveGenre(null);
    // If clearing search, go back home
    if (!query) {
      setCurrentPage('home');
    }
  }, []);

  // ── Genre select handler (tu Navbar dropdown) ──
  const handleGenreSelect = useCallback((genre) => {
    setActiveGenre(genre);
    setCurrentPage('genre');
    setSearchQuery('');
    setSearchResults([]);
  }, []);

  const handleBackFromGenre = () => {
    setCurrentPage('home');
    setActiveGenre(null);
  };

  const checkSystem = async () => {
    try {
      const res = await axios.get('/api/v1/health');
      const h = res.data;
      alert(`=== SYSTEM HEALTH ===\nStatus: ${h.status}\nDatabase: ${h.database}\n====================`);
    } catch (err) {
      alert('Health Check Failed!\n' + err.message);
    }
  };


  return (
    <div className="min-h-screen bg-zinc-950 pb-12 overflow-x-hidden text-white pt-16 lg:pt-20">
      {/* Navbar */}
      <div className="fixed top-0 left-0 w-full z-[100]">
        <Navbar
          onOpenLogin={() => setShowLogin(true)}
          currentPage={currentPage}
          onNavigate={(page) => {
            setCurrentPage(page);
            if (page === 'home') {
              setActiveGenre(null);
              setSearchQuery('');
              setSearchResults([]);
            }
          }}
          onSearch={handleSearch}
          onGenreSelect={handleGenreSelect}
        />
      </div>

      {/* Login Modal */}
      <AnimatePresence>
        {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
      </AnimatePresence>

      {/* Check System Button */}
      <div className="fixed bottom-10 right-10 z-[100]">
        <button
          onClick={checkSystem}
          className="bg-red-600 text-white px-4 py-2 rounded-full font-bold shadow-lg
                     hover:scale-110 transition-transform active:scale-95 text-sm"
        >
          Check System
        </button>
      </div>

      {/* ── PAGE CONTENT ──────────────────────────────────── */}
      {currentPage === 'reset-password' ? (
        /* ── RESET PASSWORD PAGE (from email link) ── */
        <ResetPasswordPage
          token={resetToken}
          onDone={() => {
            setCurrentPage('home');
            setResetToken(null);
            showToast('Mat khau da duoc dat lai thanh cong!');
            setShowLogin(true);
          }}
        />
      ) : currentPage === 'dashboard' ? (
        <AdminDashboard onBack={() => setCurrentPage('home')} />
      ) : currentPage === 'admin' ? (
        <MovieManagement />
      ) : currentPage === 'users' ? (
        <UserManagement />
      ) : currentPage === 'profile' ? (
        <Profile />
      ) : currentPage === 'search' ? (
        /* ── SEARCH PAGE ── */
        <SearchPage
          query={searchQuery}
          onRate={handleRateAction}
          savedRatings={savedRatings}
          onBack={() => {
            setCurrentPage('home');
            setSearchQuery('');
          }}
        />
      ) : currentPage === 'genre' && activeGenre ? (
        /* ── GENRE PAGE ── */
        <GenrePage
          genre={activeGenre}
          onRate={handleRateAction}
          savedRatings={savedRatings}
          onBack={handleBackFromGenre}
        />
      ) : (
        /* ── HOME PAGE ── */
        <>
          {/* Hero Carousel — 10 phim mới nhất */}
          <div className="relative min-h-[60vh] lg:min-h-[80vh]">
            <Hero movies={latestMovies} />
          </div>

          {/* ── MAIN CONTENT AREA ──────────────────────────── */}
          <main className="relative z-20 -mt-16 lg:-mt-40">

            {/* === RECOMMENDATIONS ROW === */}
            <AnimatePresence mode="wait">
              <motion.div
                key={`rec-${user?.user_id || 'guest'}-${refreshTrigger}`}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.5 }}
              >
                <MovieRow
                  title={isLoggedIn
                    ? `Goi y danh rieng cho ${user?.email?.split('@')[0]}`
                    : 'Phim dang hot'}
                  movies={recommendations}
                  isLoading={recLoading}
                  onRate={handleRateAction}
                  savedRatings={savedRatings}
                  reason={isLoggedIn
                    ? (aiExplanation || 'AI Recommendation')
                    : ''}
                />
              </motion.div>
            </AnimatePresence>

            {/* === TRENDING ROW === */}
            <MovieRow
              title="Trending Now"
              movies={trending}
              isLoading={loading}
              onRate={handleRateAction}
              savedRatings={savedRatings}
              reason="Top rated"
            />
          </main>
        </>
      )}

      {/* Toast */}
      <AnimatePresence>
        {toast.show && (
          <motion.div
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 50, x: '-50%' }}
            className="fixed bottom-10 left-1/2 z-[110] bg-white text-black
                       px-8 py-3 rounded-xl shadow-2xl flex items-center font-bold"
          >
            <CheckCircle className="text-green-500 mr-3" size={22} />
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default AppInner;
