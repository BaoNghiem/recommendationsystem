import React, { useState, useEffect } from 'react';
import axios from '../api/axios';
import MovieRow from '../components/MovieRow';
import { motion, AnimatePresence } from 'framer-motion';
import { Film, ChevronLeft, ChevronRight, Loader2, AlertTriangle, ArrowLeft } from 'lucide-react';
import { fixTitle, getPosterUrl } from '../utils/formatTitle';

// Mapping genre key -> display label (phai dong bo voi Backend)
const GENRE_LABELS = {
  action: "Action", adventure: "Adventure", animation: "Animation",
  childrens: "Children's", comedy: "Comedy", crime: "Crime",
  documentary: "Documentary", drama: "Drama", fantasy: "Fantasy",
  film_noir: "Film-Noir", horror: "Horror", musical: "Musical",
  mystery: "Mystery", romance: "Romance", sci_fi: "Sci-Fi",
  thriller: "Thriller", war: "War", western: "Western",
};

const MOVIES_PER_PAGE = 30;

export default function GenrePage({ genre, onRate, savedRatings = {}, onBack }) {
  const [movies, setMovies]       = useState([]);
  const [total, setTotal]         = useState(0);
  const [page, setPage]           = useState(1);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);

  const genreLabel = GENRE_LABELS[genre?.key] || genre?.label || genre?.key || 'Unknown';
  const isValidGenre = genre?.key && genre.key in GENRE_LABELS;
  const totalPages = Math.ceil(total / MOVIES_PER_PAGE);

  // Fetch khi genre hoac page thay doi
  useEffect(() => {
    if (!isValidGenre) {
      setError(`The loai "${genre?.key}" khong ton tai.`);
      setLoading(false);
      return;
    }

    fetchGenreMovies();
  }, [genre?.key, page]);

  // Reset page khi doi genre
  useEffect(() => {
    setPage(1);
  }, [genre?.key]);

  const fetchGenreMovies = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`/movies/by-genre?genre=${genre.key}&limit=${MOVIES_PER_PAGE}&page=${page}`);
      setMovies(res.data.movies || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('[ERR] GenrePage:', err.message);
      if (err.response?.status === 400) {
        setError(`The loai "${genre.key}" khong hop le.`);
      } else {
        setError('Khong the tai danh sach phim. Vui long thu lai.');
      }
    }
    setLoading(false);
  };

  // ── Error state ──
  if (error) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center px-4">
        <div className="bg-zinc-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-10 text-center max-w-md">
          <AlertTriangle size={48} className="text-amber-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Loi</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => onBack?.()}
            className="flex items-center gap-2 mx-auto px-5 py-2.5 rounded-lg
                       bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition"
          >
            <ArrowLeft size={16} />
            Quay ve trang chu
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-4 pb-8 min-h-[80vh]">
      {/* ── Header ── */}
      <div className="px-4 lg:px-12 mb-6">
        <div className="flex items-center gap-3 mb-1">
          <button
            onClick={() => onBack?.()}
            className="text-gray-400 hover:text-white transition p-1 -ml-1"
            title="Quay ve"
          >
            <ArrowLeft size={20} />
          </button>
          <Film size={22} className="text-red-400" />
          <h1 className="text-2xl lg:text-3xl font-bold text-white">
            Phim {genreLabel}
          </h1>
        </div>
        <p className="text-gray-400 text-sm ml-10">
          {loading ? 'Dang tai...' : `${total} phim`}
          {totalPages > 1 && ` · Trang ${page}/${totalPages}`}
        </p>
      </div>

      {/* ── Movie Grid ── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${genre?.key}-${page}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="px-4 lg:px-12"
        >
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 size={32} className="animate-spin text-red-500" />
              <span className="ml-3 text-gray-400">Dang tai phim {genreLabel}...</span>
            </div>
          ) : movies.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
              Khong co phim nao trong the loai nay.
            </div>
          ) : (
            <>
              {/* Grid Layout (khong phai horizontal scroll) */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {movies.map((movie) => (
                  <MovieCard
                    key={movie.movie_id}
                    movie={movie}
                    onRate={onRate}
                    savedRating={savedRatings[movie.movie_id]}
                  />
                ))}
              </div>

              {/* ── Pagination ── */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-10">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="flex items-center gap-1 px-4 py-2 rounded-lg
                               bg-white/5 border border-white/10 text-sm text-gray-300
                               hover:bg-white/10 hover:text-white disabled:opacity-30
                               disabled:cursor-not-allowed transition"
                  >
                    <ChevronLeft size={16} />
                    Truoc
                  </button>

                  {/* Page numbers */}
                  <div className="flex items-center gap-1">
                    {generatePageNumbers(page, totalPages).map((p, i) => (
                      p === '...' ? (
                        <span key={`dot-${i}`} className="px-2 text-gray-500">...</span>
                      ) : (
                        <button
                          key={p}
                          onClick={() => setPage(p)}
                          className={`w-9 h-9 rounded-lg text-sm font-medium transition
                            ${p === page
                              ? 'bg-red-600 text-white shadow-lg shadow-red-900/30'
                              : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                            }`}
                        >
                          {p}
                        </button>
                      )
                    ))}
                  </div>

                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="flex items-center gap-1 px-4 py-2 rounded-lg
                               bg-white/5 border border-white/10 text-sm text-gray-300
                               hover:bg-white/10 hover:text-white disabled:opacity-30
                               disabled:cursor-not-allowed transition"
                  >
                    Sau
                    <ChevronRight size={16} />
                  </button>
                </div>
              )}
            </>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}


// ── Movie Card (grid layout) ──────────────────────────────
function MovieCard({ movie, onRate, savedRating }) {
  const [hoverStar, setHoverStar] = useState(0);
  const [localRating, setLocalRating] = useState(0);
  const displayStars = hoverStar || localRating || savedRating || 0;

  const handleRate = (e, star) => {
    e.stopPropagation();
    setLocalRating(star);
    onRate?.(movie.movie_id, movie.title, star);
  };

  return (
    <motion.div
      whileHover={{ scale: 1.03, y: -4 }}
      className="group relative bg-zinc-900/60 rounded-xl overflow-hidden border border-white/5
                 hover:border-white/15 transition-all cursor-pointer"
    >
      {/* Poster */}
      <div className="aspect-[2/3] relative overflow-hidden">
        <img
          src={getPosterUrl(movie)}
          alt={movie.title}
          loading="lazy"
          className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
        />
        {/* Rating badge */}
        {movie.rating_count > 0 && (
          <div className="absolute top-2 right-2 bg-black/70 backdrop-blur-sm rounded-md px-1.5 py-0.5 text-[10px] text-gray-300">
            {movie.rating_count} votes
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="text-white text-xs font-semibold line-clamp-2 mb-1.5 leading-tight">
          {movie.title}
        </h3>
        <p className="text-gray-500 text-[10px] mb-2 line-clamp-1">
          {movie.genres_orig?.split('|').join(' · ')}
        </p>

        {/* Star Rating */}
        <div className="flex items-center gap-0.5">
          {[1, 2, 3, 4, 5].map((star) => {
            const active = star <= displayStars;
            return (
              <button
                key={star}
                onClick={(e) => handleRate(e, star)}
                onMouseEnter={() => setHoverStar(star)}
                onMouseLeave={() => setHoverStar(0)}
                className="transition-transform hover:scale-125"
              >
                <svg
                  width="14" height="14" viewBox="0 0 24 24"
                  fill={active ? '#f59e0b' : 'none'}
                  stroke={active ? '#f59e0b' : '#4b5563'}
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                >
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </button>
            );
          })}
          {(localRating > 0 || savedRating > 0) && (
            <span className="text-amber-400 text-[10px] ml-1 font-bold">
              {localRating || savedRating}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}


// ── Utility: Generate page number array with ellipsis ──────
function generatePageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const pages = [];
  pages.push(1);

  if (current > 3) pages.push('...');

  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  for (let i = start; i <= end; i++) pages.push(i);

  if (current < total - 2) pages.push('...');

  pages.push(total);
  return pages;
}
