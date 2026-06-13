import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Film, Tv2, Star, Globe, Calendar,
  Play, List, CheckCircle, Clock, Loader2, AlertCircle
} from 'lucide-react';
import axios from '../api/axios';
import VideoPlayer from '../components/VideoPlayer';
import { fixTitle, getPosterUrl } from '../utils/formatTitle';
import { useAuth } from '../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * WatchPage — Trang xem phim
 * Props:
 *   movie  : object  — thông tin phim đầy đủ (từ MovieDetailModal)
 *   onBack : fn()    — quay lại
 *   onRate : fn(movieId, title, rating) — callback rating
 *   savedRatings: object
 */
export default function WatchPage({ movie, onBack, onRate, savedRatings = {}, onWatch }) {
  const { user, isLoggedIn } = useAuth();

  const [videoInfo,      setVideoInfo]      = useState(null);   // { has_video, episodes: [] }
  const [activeEpisode,  setActiveEpisode]  = useState(null);   // episode object đang phát
  const [watchHistoryList, setWatchHistoryList] = useState([]); // array of watched episodes
  const [related,        setRelated]        = useState([]);
  const [loadingInfo,    setLoadingInfo]    = useState(true);
  const [error,          setError]          = useState('');
  const [userRating,     setUserRating]     = useState(savedRatings[movie?.movie_id] || 0);
  const [hoverRating,    setHoverRating]    = useState(0);
  const [rateSuccess,    setRateSuccess]    = useState(false);
  const [showEpisodes,   setShowEpisodes]   = useState(false);

  const isSeries = Boolean(movie?.total_episodes);

  // ── Fetch video info ────────────────────────────────────────
  useEffect(() => {
    if (!movie?.movie_id) return;
    setLoadingInfo(true);
    setError('');

    axios.get(`/videos/${movie.movie_id}/info`)
      .then(res => {
        setVideoInfo(res.data);
        if (res.data.episodes?.length > 0) {
          setActiveEpisode(res.data.episodes[0]);
        }
      })
      .catch(() => setError('Không thể tải thông tin video.'))
      .finally(() => setLoadingInfo(false));
  }, [movie?.movie_id]);

  // ── Fetch watch history list ──────────────────
  useEffect(() => {
    if (!isLoggedIn || !movie?.movie_id) return;
    axios.get(`/watch/history/${movie.movie_id}`)
      .then(res => {
        setWatchHistoryList(res.data.history || []);
      })
      .catch(() => {});
  }, [isLoggedIn, movie?.movie_id]);

  // ── Fetch related movies ────────────────────────────────────
  // BUG FIX: Dung bang map chinh xac thay vi .replace() tuy tien
  // De tranh loi: "Children's" -> "children's" (sai), nen -> "childrens" (dung)
  const GENRE_TO_KEY = {
    'action': 'action', 'adventure': 'adventure', 'animation': 'animation',
    "children's": 'childrens', 'comedy': 'comedy', 'crime': 'crime',
    'documentary': 'documentary', 'drama': 'drama', 'fantasy': 'fantasy',
    'film-noir': 'film_noir', 'horror': 'horror', 'musical': 'musical',
    'mystery': 'mystery', 'romance': 'romance', 'sci-fi': 'sci_fi',
    'thriller': 'thriller', 'war': 'war', 'western': 'western',
  };
  useEffect(() => {
    if (!movie?.movie_id) return;
    const rawGenre = (movie.genres_orig || '').split('|')[0]?.trim().toLowerCase() || '';
    const genre = GENRE_TO_KEY[rawGenre] || 'action';
    // FEATURE: random=true -> moi lan xem phim se goi y bo phim khac nhau cung the loai
    axios.get(`/movies/by-genre?genre=${genre}&limit=10&random=true`)
      .then(res => {
        const others = (res.data.movies || []).filter(m => m.movie_id !== movie.movie_id);
        setRelated(others.slice(0, 6));
      })
      .catch(() => {});
  }, [movie?.movie_id, movie?.genres_orig]);

  // ── Save watch progress ─────────────────────────────────────
  const handleProgress = useCallback((currentSecs, durationSecs) => {
    if (!isLoggedIn || !movie?.movie_id) return;
    axios.put('/watch/progress', {
      movie_id:           movie.movie_id,
      episode_no:         activeEpisode?.episode_no ?? null,
      season_no:          activeEpisode?.season_no  ?? 1,
      last_position_secs: currentSecs,
      duration_secs:      durationSecs,
    }).catch(() => {});
  }, [isLoggedIn, movie?.movie_id, activeEpisode]);

  // ── Handle rating ───────────────────────────────────────────
  const handleRate = async (val) => {
    setUserRating(val);
    if (onRate) {
      await onRate(movie.movie_id, movie.title, val);
      setRateSuccess(true);
      setTimeout(() => setRateSuccess(false), 2500);
    }
  };

  // ── Stream URL builder ──────────────────────────────────────
  const buildStreamUrl = (ep) => {
    if (!ep) return '';
    const token = localStorage.getItem('access_token');
    const epParam = ep.episode_no != null ? `&episode_no=${ep.episode_no}` : '';
    const snParam = `&season_no=${ep.season_no ?? 1}`;
    return `${API_BASE}/videos/${movie.movie_id}/stream?token=${token}${epParam}${snParam}`;
  };

  // ── Resume time ─────────────────────────────────────────────
  const getResumeTime = () => {
    if (!watchHistoryList.length) return 0;
    
    // Tìm lịch sử của tập đang phát
    const epHistory = watchHistoryList.find(h => 
      (h.episode_no === (activeEpisode?.episode_no ?? null))
    );
    
    if (epHistory) {
      return epHistory.last_position_secs || 0;
    }
    return 0;
  };

  if (!movie) return null;

  const genres = (movie.genres_orig || '').split('|').map(g => g.trim()).filter(Boolean);
  const currentRating = savedRatings[movie.movie_id] || userRating;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-zinc-950 text-white"
    >
      {/* ── Top bar ── */}
      <div className="sticky top-16 z-40 bg-zinc-950/90 backdrop-blur-md border-b border-white/5 px-6 py-3 flex items-center gap-4">
        <button
          id="watch-back-btn"
          onClick={onBack}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors group"
        >
          <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">Quay lại</span>
        </button>
        <div className="h-4 w-px bg-white/10" />
        <span className="text-white font-semibold text-sm truncate max-w-xs">
          {fixTitle(movie.title)}
        </span>
        {activeEpisode?.episode_no && (
          <span className="text-amber-400 text-sm">
            — Tập {activeEpisode.episode_no}
          </span>
        )}
      </div>

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6 space-y-8">

        {/* ── Main layout: Player + Sidebar ── */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* ── LEFT: Player ─────────────────────────────── */}
          <div className="xl:col-span-2 space-y-4">

            {/* Player area */}
            {loadingInfo ? (
              <div className="aspect-video bg-zinc-900 rounded-2xl flex items-center justify-center">
                <Loader2 size={40} className="text-amber-400 animate-spin" />
              </div>
            ) : error ? (
              <div className="aspect-video bg-zinc-900 rounded-2xl flex flex-col items-center justify-center gap-3">
                <AlertCircle size={40} className="text-red-400" />
                <p className="text-gray-400">{error}</p>
              </div>
            ) : !videoInfo?.has_video ? (
              /* Chưa có video */
              <div className="aspect-video bg-zinc-900 rounded-2xl flex flex-col items-center justify-center gap-4
                              border border-white/5">
                <div className="w-20 h-20 rounded-full bg-white/5 border border-white/10
                                flex items-center justify-center">
                  {isSeries
                    ? <Tv2 size={36} className="text-gray-600" />
                    : <Film size={36} className="text-gray-600" />}
                </div>
                <div className="text-center">
                  <p className="text-gray-400 font-medium">Video chưa được upload</p>
                  <p className="text-gray-600 text-sm mt-1">Admin cần upload video để xem phim này.</p>
                </div>
                {/* Hiển thị poster nếu có */}
                {movie.poster_url && (
                  <img
                    src={getPosterUrl(movie)}
                    alt={movie.title}
                    className="absolute inset-0 w-full h-full object-cover rounded-2xl opacity-10"
                  />
                )}
              </div>
            ) : (
              /* VideoPlayer */
              <VideoPlayer
                key={`${movie.movie_id}-${activeEpisode?.id}`}
                src={buildStreamUrl(activeEpisode)}
                title={fixTitle(movie.title)}
                episodeLabel={
                  activeEpisode?.episode_no
                    ? (activeEpisode.episode_title || `Tập ${activeEpisode.episode_no}`)
                    : 'Phim lẻ'
                }
                initialTime={getResumeTime()}
                onProgress={handleProgress}
                onEnded={() => {
                  // Tự chuyển tập tiếp theo nếu là phim bộ
                  if (isSeries && videoInfo?.episodes) {
                    const idx = videoInfo.episodes.findIndex(e => e.id === activeEpisode?.id);
                    if (idx >= 0 && idx < videoInfo.episodes.length - 1) {
                      setActiveEpisode(videoInfo.episodes[idx + 1]);
                    }
                  }
                }}
              />
            )}

            {/* Episode list toggle (phim bộ) */}
            {isSeries && videoInfo?.episodes?.length > 0 && (
              <div>
                <button
                  onClick={() => setShowEpisodes(v => !v)}
                  className="flex items-center gap-2 text-sm text-gray-400 hover:text-white
                             transition-colors font-medium"
                >
                  <List size={16} />
                  {showEpisodes ? 'Ẩn danh sách tập' : `Danh sách tập (${videoInfo.episodes.length})`}
                </button>

                <AnimatePresence>
                  {showEpisodes && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden mt-3"
                    >
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                        {videoInfo.episodes.map(ep => {
                          const isActive = ep.id === activeEpisode?.id;
                          // Tìm lịch sử của tập này
                          const epHistory = watchHistoryList.find(h => h.episode_no === ep.episode_no);
                          const isWatched = epHistory && epHistory.is_completed;

                          let btnClass = 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:text-white';
                          if (isActive) {
                            btnClass = 'bg-amber-500/20 border-amber-500/50 text-amber-300 ring-1 ring-amber-500/30 shadow-lg shadow-amber-900/20';
                          } else if (isWatched) {
                            btnClass = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20';
                          }

                          return (
                            <button
                              key={ep.id}
                              onClick={() => setActiveEpisode(ep)}
                              className={`p-3 rounded-xl text-left transition-all border text-sm relative ${btnClass}`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <p className="font-semibold truncate">Tập {ep.episode_no}</p>
                                {isWatched && !isActive && <CheckCircle size={14} className="text-emerald-500 shrink-0" />}
                              </div>
                              {ep.episode_title && (
                                <p className="text-xs opacity-70 mt-0.5 line-clamp-1">{ep.episode_title}</p>
                              )}
                              {ep.duration_mins && (
                                <p className="text-xs opacity-50 mt-1 flex items-center gap-1">
                                  <Clock size={10} /> {ep.duration_mins} phút
                                </p>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* ── Movie Info ── */}
            <div className="bg-zinc-900/60 rounded-2xl border border-white/5 p-5 space-y-4">
              <div className="flex items-start gap-4">
                {/* Poster nhỏ */}
                {movie.poster_url ? (
                  <img
                    src={getPosterUrl(movie)}
                    alt={movie.title}
                    className="w-16 h-24 object-cover rounded-xl border border-white/10 flex-shrink-0"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-xl bg-white/5 border border-white/10
                                  flex items-center justify-center flex-shrink-0">
                    {isSeries
                      ? <Tv2 size={24} className="text-amber-400" />
                      : <Film size={24} className="text-amber-400" />}
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <h1 className="text-xl font-bold text-white leading-tight">
                    {fixTitle(movie.title)}
                  </h1>
                  <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-500">
                    {movie.release_year && (
                      <span className="flex items-center gap-1">
                        <Calendar size={11} /> {movie.release_year}
                      </span>
                    )}
                    {movie.country && (
                      <span className="flex items-center gap-1">
                        <Globe size={11} /> {movie.country}
                      </span>
                    )}
                    {isSeries && (
                      <span className="flex items-center gap-1">
                        <Tv2 size={11} /> {movie.total_episodes} tập
                      </span>
                    )}
                    {movie.avg_rating && (
                      <span className="flex items-center gap-1 text-amber-400">
                        <Star size={11} className="fill-amber-400" />
                        {movie.avg_rating?.toFixed(1)} / 5
                      </span>
                    )}
                  </div>

                  {/* Genres */}
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {genres.map(g => (
                      <span key={g}
                        className="px-2.5 py-0.5 rounded-full text-xs bg-amber-500/10
                                   text-amber-400 border border-amber-500/20">
                        {g}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Description */}
              {movie.description && movie.description !== '(Chưa có mô tả)' && (
                <p className="text-sm text-gray-400 leading-relaxed">{movie.description}</p>
              )}

              {/* Cast & Crew */}
              {(movie.directors?.length > 0 || movie.actors?.length > 0) && (
                <div className="space-y-3 pt-3 border-t border-white/5 mt-4">
                  {movie.directors?.length > 0 && (
                    <div className="flex items-start">
                      <span className="text-gray-500 text-sm font-medium w-24 shrink-0">Đạo diễn:</span>
                      <span className="text-gray-300 text-sm">
                        {movie.directors.map(d => d.name).join(', ')}
                      </span>
                    </div>
                  )}
                  {movie.actors?.length > 0 && (
                    <div className="flex items-start">
                      <span className="text-gray-500 text-sm font-medium w-24 shrink-0">Diễn viên:</span>
                      <span className="text-gray-300 text-sm leading-relaxed">
                        {movie.actors.slice(0, 15).map(a => a.name).join(', ')}
                        {movie.actors.length > 15 && '...'}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* ── Rating widget ── */}
              {isLoggedIn && (
                <div className="pt-3 border-t border-white/5">
                  <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">
                    Đánh giá của bạn
                  </p>
                  <div className="flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map(star => (
                      <button
                        key={star}
                        id={`watch-star-${star}`}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        onClick={() => handleRate(star)}
                        className="transition-transform hover:scale-125"
                      >
                        <Star
                          size={24}
                          className={`transition-colors ${
                            star <= (hoverRating || currentRating)
                              ? 'text-amber-400 fill-amber-400'
                              : 'text-gray-600'
                          }`}
                        />
                      </button>
                    ))}
                    <AnimatePresence>
                      {rateSuccess && (
                        <motion.span
                          initial={{ opacity: 0, x: -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0 }}
                          className="ml-2 text-green-400 text-sm flex items-center gap-1"
                        >
                          <CheckCircle size={14} /> Đã lưu!
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ── RIGHT: Sidebar — Related movies ─────────────────── */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider px-1">
              Phim liên quan
            </h3>
            {related.length === 0 ? (
              <p className="text-gray-600 text-sm px-1">Không có phim liên quan.</p>
            ) : (
              related.map(m => (
                <RelatedCard
                  key={m.movie_id}
                  movie={m}
                  onWatch={() => onWatch && onWatch(m)}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Related Movie Card ─────────────────────────────────────── */
function RelatedCard({ movie, onWatch }) {
  const genres = (movie.genres_orig || '').split('|').slice(0, 2).map(g => g.trim());
  return (
    <div
      className="flex gap-3 bg-zinc-900/50 border border-white/5 rounded-xl p-3
                 hover:bg-zinc-800/60 hover:border-white/10 transition-all cursor-pointer group"
      onClick={onWatch}
    >
      {movie.poster_url ? (
        <img
          src={getPosterUrl(movie)}
          alt={movie.title}
          className="w-14 h-20 object-cover rounded-lg border border-white/10 flex-shrink-0"
        />
      ) : (
        <div className="w-14 h-20 bg-white/5 rounded-lg border border-white/10
                        flex items-center justify-center flex-shrink-0">
          <Film size={20} className="text-gray-600" />
        </div>
      )}
      <div className="flex-1 min-w-0 py-0.5">
        <p className="text-sm font-semibold text-white line-clamp-2 leading-tight
                      group-hover:text-amber-400 transition-colors">
          {fixTitle(movie.title)}
        </p>
        {movie.release_year && (
          <p className="text-xs text-gray-500 mt-1">{movie.release_year}</p>
        )}
        <div className="flex flex-wrap gap-1 mt-2">
          {genres.map(g => (
            <span key={g}
              className="text-[10px] px-1.5 py-0.5 rounded-full
                         bg-white/5 text-gray-500 border border-white/8">
              {g}
            </span>
          ))}
        </div>
        <div className="mt-2 flex items-center gap-1 text-amber-400/70 text-xs
                        group-hover:text-amber-400 transition-colors">
          <Play size={11} />
          <span>Xem ngay</span>
        </div>
      </div>
    </div>
  );
}
