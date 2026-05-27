import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User, Mail, Shield, Calendar, Star, Film, Clock,
  ChevronDown, ChevronUp, Loader2, LogOut, MailCheck, MailX,
  Trash2, Lock, Eye, EyeOff, X, AlertTriangle, CheckCircle, Compass
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import ProtectedRoute from '../components/ProtectedRoute';

export default function Profile() {
  return (
    <ProtectedRoute>
      <ProfileInner />
    </ProtectedRoute>
  );
}

function ProfileInner() {
  const { user, logout } = useAuth();
  const [ratings, setRatings] = useState([]);
  const [totalRatings, setTotalRatings] = useState(0);
  const [loadingRatings, setLoadingRatings] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [showPwModal, setShowPwModal] = useState(false);

  // Stats
  const avgRating = ratings.length > 0
    ? (ratings.reduce((s, r) => s + r.rating, 0) / ratings.length).toFixed(1)
    : '0.0';

  const genreCount = {};
  // Loc lay danh sach phim duoc user cham tu 4 sao tro len (hoac fallback neu khong co phim >= 4 sao)
  const highlyRatedMovies = ratings.filter(r => r.rating >= 4);
  const targetMovies = highlyRatedMovies.length > 0 ? highlyRatedMovies : ratings;

  targetMovies.forEach(r => {
    (r.genres_orig || '').split('|').filter(Boolean).forEach(g => {
      genreCount[g.trim()] = (genreCount[g.trim()] || 0) + 1;
    });
  });

  const topGenres = Object.entries(genreCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  useEffect(() => {
    fetchRatings();
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await api.get('/auth/me');
      setProfileData(res.data);
    } catch (err) {
      console.error('[Profile] Profile fetch error:', err.message);
    }
  };

  const fetchRatings = async () => {
    setLoadingRatings(true);
    try {
      const res = await api.get('/ratings/me');
      setRatings(res.data.ratings || []);
      setTotalRatings(res.data.total || 0);
    } catch (err) {
      console.error('[Profile] Ratings error:', err.message);
    }
    setLoadingRatings(false);
  };

  const handleDeleteRating = async (movieId) => {
    setDeletingId(movieId);
    try {
      await api.delete(`/ratings/me/${movieId}`);
      setRatings(prev => prev.filter(r => r.movie_id !== movieId));
      setTotalRatings(prev => prev - 1);
    } catch (err) {
      console.error('[Profile] Delete rating error:', err.message);
    }
    setDeletingId(null);
  };

  const displayRatings = showAll ? ratings : ratings.slice(0, 10);

  const starColor = (val) => {
    if (val >= 4) return 'text-green-400';
    if (val >= 3) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getPosterUrl = (title) => {
    return `https://placehold.co/60x90/141414/ffffff?text=${encodeURIComponent(title?.substring(0, 10) || '?')}`;
  };

  const joinDate = profileData?.created_at
    ? new Date(profileData.created_at).toLocaleDateString('vi-VN', { year: 'numeric', month: 'long', day: 'numeric' })
    : '—';

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-4xl mx-auto px-4 lg:px-8 pt-6 pb-16">

        {/* ── Profile Card ────────────────────────────────── */}
        <div className="bg-zinc-900/80 border border-white/5 rounded-2xl overflow-hidden mb-8">
          {/* Banner */}
          <div className="h-28 bg-gradient-to-r from-red-900/40 via-rose-900/30 to-orange-900/20 relative">
            <div className="absolute -bottom-10 left-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-red-600 to-rose-600
                              flex items-center justify-center text-3xl font-bold shadow-2xl
                              border-4 border-zinc-950">
                {user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
            </div>
          </div>

          <div className="pt-14 px-6 pb-6">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div>
                <h1 className="text-xl font-bold">{user?.email?.split('@')[0]}</h1>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <Mail size={13} className="text-gray-500" />
                  <span className="text-sm text-gray-400">{user?.email}</span>
                  {profileData?.email_verified ? (
                    <span className="flex items-center gap-1 text-[10px] text-green-400 bg-green-500/10
                                     px-2 py-0.5 rounded-full border border-green-500/20">
                      <MailCheck size={10} /> Verified
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10
                                     px-2 py-0.5 rounded-full border border-amber-500/20">
                      <MailX size={10} /> Unverified
                    </span>
                  )}
                </div>
                {/* Join date */}
                <div className="flex items-center gap-2 mt-2">
                  <Calendar size={13} className="text-gray-500" />
                  <span className="text-xs text-gray-500">Tham gia: {joinDate}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {/* Role badge */}
                <span className={`px-3 py-1 rounded-full text-xs font-semibold
                  ${user?.role === 'admin'
                    ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20'
                    : 'bg-blue-500/15 text-blue-400 border border-blue-500/20'}`}>
                  <Shield size={11} className="inline mr-1" />
                  {user?.role}
                </span>
                {/* Account type badge */}
                <span className={`px-3 py-1 rounded-full text-xs font-medium border
                  ${user?.account_type === 'legacy'
                    ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>
                  {user?.account_type === 'legacy' ? 'Legacy' : 'Real'}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-white/5 text-gray-400
                                 border border-white/5">
                  ID: {user?.user_id}
                </span>
                {/* Change password btn */}
                <button
                  onClick={() => setShowPwModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                             bg-white/5 text-gray-300 border border-white/10
                             hover:bg-white/10 hover:text-white transition-all"
                >
                  <Lock size={12} /> Doi mat khau
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ── Stats Cards ─────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          {[
            { label: 'Phim da danh gia', value: totalRatings, icon: Film, color: 'text-red-400' },
            { label: 'Diem trung binh', value: `${avgRating} ★`, icon: Star, color: 'text-yellow-400' },
            { label: `The loai yeu thich (${highlyRatedMovies.length > 0 ? '≥ 4★' : 'Tat ca'})`, value: topGenres[0]?.[0] || '—', icon: Star, color: 'text-purple-400' },
            { label: 'Tai khoan', value: user?.account_type || 'real', icon: User, color: 'text-blue-400' },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="bg-zinc-900/60 border border-white/5 rounded-xl p-4"
            >
              <stat.icon size={16} className={`${stat.color} mb-2`} />
              <p className="text-xl font-bold">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{stat.label}</p>
            </motion.div>
          ))}
        </div>

        {/* ── Top Genres ──────────────────────────────────── */}
        {topGenres.length > 0 && (
          <div className="bg-zinc-900/60 border border-white/5 rounded-xl p-5 mb-8">
            <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">
              The loai yeu thich ({highlyRatedMovies.length > 0 ? 'Phim ≥ 4★' : 'Tat ca'})
            </h3>
            <div className="flex flex-wrap gap-2">
              {topGenres.map(([genre, count]) => (
                <div key={genre}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5">
                  <span className="text-sm text-white font-medium">{genre}</span>
                  <span className="text-[10px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded-full">
                    {count} phim
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Rating History ─────────────────────────────── */}
        <div className="bg-zinc-900/60 border border-white/5 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock size={16} className="text-gray-500" />
              <h3 className="font-semibold">Lich su danh gia</h3>
              <span className="text-xs text-gray-500">({totalRatings} phim)</span>
            </div>
          </div>

          {loadingRatings ? (
            /* Skeleton loading for ratings */
            <div className="divide-y divide-white/[0.03]">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="px-5 py-3 flex items-center gap-4 animate-pulse">
                  <div className="w-[40px] h-[60px] rounded bg-white/5 shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 w-2/3 rounded bg-white/5" />
                    <div className="h-2 w-1/3 rounded bg-white/5" />
                  </div>
                  <div className="flex gap-1">
                    {[...Array(5)].map((_, j) => (
                      <div key={j} className="w-3 h-3 rounded-full bg-white/5" />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : ratings.length === 0 ? (
            /* ── Empty state ── */
            <div className="text-center py-16 px-6">
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', damping: 20 }}
              >
                <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20
                                flex items-center justify-center mx-auto mb-4">
                  <Film size={28} className="text-red-400/60" />
                </div>
                <h4 className="text-base font-semibold text-white mb-2">
                  Ban chua danh gia bo phim nao
                </h4>
                <p className="text-sm text-gray-500 mb-5 max-w-sm mx-auto leading-relaxed">
                  Hay cho diem nhung bo phim ban yeu thich de AI co the
                  goi y chinh xac hon cho ban!
                </p>
                <a
                  href="/"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold
                             bg-gradient-to-r from-red-600 to-rose-600 text-white
                             hover:from-red-500 hover:to-rose-500
                             transition-all shadow-lg shadow-red-900/30 active:scale-95"
                >
                  <Compass size={16} />
                  Kham pha ngay!
                </a>
              </motion.div>
            </div>
          ) : (
            <>
              <div className="divide-y divide-white/[0.03]">
                <AnimatePresence initial={false}>
                  {displayRatings.map((r, i) => (
                    <motion.div
                      key={r.movie_id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20, height: 0 }}
                      transition={{ delay: i * 0.02 }}
                      className="px-5 py-3 flex items-center gap-4 hover:bg-white/[0.02] transition group"
                    >
                      {/* Poster */}
                      <img
                        src={getPosterUrl(r.title)}
                        alt={r.title}
                        className="w-[40px] h-[60px] rounded object-cover border border-white/10 shrink-0"
                      />

                      {/* Title + genres */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{r.title}</p>
                        <p className="text-[10px] text-gray-600 truncate">
                          {r.genres_orig?.split('|').join(' · ')}
                        </p>
                      </div>

                      {/* Rating stars */}
                      <div className="flex items-center gap-1 shrink-0">
                        {[1, 2, 3, 4, 5].map(s => (
                          <Star
                            key={s}
                            size={12}
                            fill={s <= r.rating ? '#f59e0b' : 'none'}
                            stroke={s <= r.rating ? '#f59e0b' : '#3f3f46'}
                          />
                        ))}
                        <span className={`text-xs font-bold ml-1 ${starColor(r.rating)}`}>
                          {r.rating}
                        </span>
                      </div>

                      {/* Timestamp */}
                      <span className="text-[10px] text-gray-600 shrink-0 hidden sm:block w-20 text-right">
                        {r.timestamp ? new Date(r.timestamp).toLocaleDateString('vi-VN') : ''}
                      </span>

                      {/* Delete button */}
                      <button
                        onClick={() => handleDeleteRating(r.movie_id)}
                        disabled={deletingId === r.movie_id}
                        className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10
                                   transition-all opacity-0 group-hover:opacity-100 shrink-0
                                   disabled:opacity-50"
                        title="Xoa danh gia"
                      >
                        {deletingId === r.movie_id
                          ? <Loader2 size={14} className="animate-spin" />
                          : <Trash2 size={14} />
                        }
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Show more/less */}
              {ratings.length > 10 && (
                <button
                  onClick={() => setShowAll(p => !p)}
                  className="w-full py-3 text-sm font-medium text-gray-400 hover:text-white
                             bg-white/[0.02] hover:bg-white/[0.04] transition
                             flex items-center justify-center gap-1 border-t border-white/5"
                >
                  {showAll ? (
                    <><ChevronUp size={14} /> Thu gon</>
                  ) : (
                    <><ChevronDown size={14} /> Xem tat ca {totalRatings} danh gia</>
                  )}
                </button>
              )}
            </>
          )}
        </div>

      </div>

      {/* ── Change Password Modal ────────────────────────── */}
      <AnimatePresence>
        {showPwModal && (
          <ChangePasswordModal onClose={() => setShowPwModal(false)} />
        )}
      </AnimatePresence>
    </div>
  );
}


/* ================================================================
   CHANGE PASSWORD MODAL
   ================================================================ */
function ChangePasswordModal({ onClose }) {
  const { logout } = useAuth();
  const [form, setForm] = useState({ current: '', newPw: '', confirm: '' });
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const validate = () => {
    if (!form.current) return 'Vui long nhap mat khau hien tai.';
    if (form.newPw.length < 6) return 'Mat khau moi phai co it nhat 6 ky tu.';
    if (form.newPw !== form.confirm) return 'Xac nhan mat khau khong khop.';
    if (form.current === form.newPw) return 'Mat khau moi phai khac mat khau cu.';
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }

    setLoading(true);
    setError('');
    try {
      await api.post('/auth/change-password', {
        current_password: form.current,
        new_password: form.newPw,
      });
      setSuccess(true);
      // Auto logout after 2.5 seconds
      setTimeout(() => {
        logout();
        onClose();
      }, 2500);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Doi mat khau that bai.');
    }
    setLoading(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm px-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-zinc-900 border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock size={16} className="text-red-400" />
            <h2 className="font-bold text-lg">Doi mat khau</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/10 transition">
            <X size={18} className="text-gray-400" />
          </button>
        </div>

        {success ? (
          /* Success state */
          <div className="px-6 py-12 text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="w-16 h-16 rounded-full bg-green-500/10 border-2 border-green-500
                          flex items-center justify-center mx-auto mb-4"
            >
              <CheckCircle size={28} className="text-green-400" />
            </motion.div>
            <h3 className="text-lg font-bold text-white mb-2">Thanh cong!</h3>
            <p className="text-sm text-gray-400">
              Mat khau da duoc thay doi. Ban se duoc dang xuat trong giay lat...
            </p>
            <div className="mt-4 flex items-center justify-center gap-2 text-xs text-amber-400">
              <Loader2 size={12} className="animate-spin" />
              Dang dang xuat...
            </div>
          </div>
        ) : (
          /* Form */
          <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
            {/* Error alert */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-red-500/10
                             border border-red-500/20 text-red-400 text-sm"
                >
                  <AlertTriangle size={14} />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Current password */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 font-medium">Mat khau hien tai</label>
              <div className="relative">
                <input
                  type={showCurrent ? 'text' : 'password'}
                  value={form.current}
                  onChange={(e) => setForm(p => ({ ...p, current: e.target.value }))}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm
                             text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none
                             transition pr-10"
                  placeholder="Nhap mat khau hien tai"
                />
                <button type="button" onClick={() => setShowCurrent(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                  {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* New password */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 font-medium">Mat khau moi</label>
              <div className="relative">
                <input
                  type={showNew ? 'text' : 'password'}
                  value={form.newPw}
                  onChange={(e) => setForm(p => ({ ...p, newPw: e.target.value }))}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm
                             text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none
                             transition pr-10"
                  placeholder="It nhat 6 ky tu"
                />
                <button type="button" onClick={() => setShowNew(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                  {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {form.newPw && form.newPw.length < 6 && (
                <p className="text-[11px] text-amber-400 mt-1">Can them {6 - form.newPw.length} ky tu nua</p>
              )}
            </div>

            {/* Confirm password */}
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 font-medium">Xac nhan mat khau moi</label>
              <input
                type="password"
                value={form.confirm}
                onChange={(e) => setForm(p => ({ ...p, confirm: e.target.value }))}
                className={`w-full bg-white/5 border rounded-lg px-4 py-2.5 text-sm
                           text-white placeholder-gray-600 focus:outline-none transition
                           ${form.confirm && form.confirm !== form.newPw
                             ? 'border-red-500/50 focus:border-red-500'
                             : 'border-white/10 focus:border-red-500/50'}`}
                placeholder="Nhap lai mat khau moi"
              />
              {form.confirm && form.confirm !== form.newPw && (
                <p className="text-[11px] text-red-400 mt-1">Mat khau khong khop</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg font-semibold text-sm text-white
                         bg-gradient-to-r from-red-600 to-rose-600
                         hover:from-red-500 hover:to-rose-500
                         disabled:opacity-50 disabled:cursor-not-allowed
                         transition-all shadow-lg shadow-red-900/20
                         flex items-center justify-center gap-2"
            >
              {loading ? (
                <><Loader2 size={16} className="animate-spin" /> Dang xu ly...</>
              ) : (
                <><Lock size={16} /> Doi mat khau</>
              )}
            </button>

            <p className="text-[11px] text-gray-600 text-center">
              Sau khi doi mat khau, ban se duoc dang xuat va can dang nhap lai.
            </p>
          </form>
        )}
      </motion.div>
    </motion.div>
  );
}
