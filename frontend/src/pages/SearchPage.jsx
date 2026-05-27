import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Star, Film, AlertCircle, Loader2, ArrowLeft, Play } from 'lucide-react';
import axios from '../api/axios';

const SearchPage = ({ query, onRate, savedRatings = {}, onBack }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [hoverRating, setHoverRating] = useState({});
  const [localRatings, setLocalRatings] = useState({});
  const abortRef = useRef(null);

  // ── Fetch search results when query changes ──
  useEffect(() => {
    if (!query || !query.trim()) {
      setResults([]);
      setSearched(false);
      return;
    }

    const fetchResults = async () => {
      // Cancel previous in-flight request
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setSearched(true);
      try {
        const res = await axios.get(
          `/movies/search?q=${encodeURIComponent(query.trim())}&limit=60`,
          { signal: controller.signal }
        );
        setResults(res.data || []);
      } catch (err) {
        if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
          console.error('[SearchPage] Error:', err.message);
        }
      }
      setLoading(false);
    };

    fetchResults();

    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, [query]);

  const handleRateClick = (e, movie, rating) => {
    e.preventDefault();
    e.stopPropagation();
    setLocalRatings(prev => ({ ...prev, [movie.movie_id]: rating }));
    onRate?.(movie.movie_id, movie.title, rating);
  };

  const getDisplayStars = (movieId) => {
    if (hoverRating[movieId]) return hoverRating[movieId];
    if (localRatings[movieId]) return localRatings[movieId];
    if (savedRatings[movieId]) return savedRatings[movieId];
    return 0;
  };

  const getPosterUrl = (movie) => {
    const encodedTitle = encodeURIComponent(movie.title);
    return `https://placehold.co/300x450/141414/ffffff?text=${encodedTitle}`;
  };

  // ── Card animation variants ──
  const cardVariants = {
    hidden: { opacity: 0, y: 30, scale: 0.95 },
    visible: (i) => ({
      opacity: 1, y: 0, scale: 1,
      transition: { delay: i * 0.04, duration: 0.4, ease: 'easeOut' },
    }),
  };

  return (
    <div className="px-4 lg:px-12 pt-4 pb-16 min-h-[80vh]">
      {/* ── Header ── */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5
                     hover:bg-white/10 border border-white/10 text-gray-300
                     hover:text-white transition-all text-sm"
        >
          <ArrowLeft size={16} />
          Trang chu
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 to-rose-500
                          flex items-center justify-center shadow-lg shadow-red-900/30">
            <Search size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl lg:text-2xl font-bold text-white">
              Ket qua tim kiem
            </h1>
            {query && (
              <p className="text-sm text-gray-400">
                Tu khoa: "<span className="text-red-400 font-medium">{query}</span>"
                {searched && !loading && (
                  <span className="ml-2 text-gray-500">— {results.length} phim</span>
                )}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ── Loading state ── */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <Loader2 size={40} className="text-red-500 animate-spin" />
          <p className="text-gray-400 text-sm">Dang tim kiem...</p>
        </div>
      )}

      {/* ── No results ── */}
      {searched && !loading && results.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center py-24 gap-4"
        >
          <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center
                          border border-white/10">
            <AlertCircle size={36} className="text-gray-500" />
          </div>
          <h2 className="text-xl font-bold text-white">Khong tim thay phim</h2>
          <p className="text-gray-400 text-sm text-center max-w-md">
            Khong tim thay phim nao khop voi tu khoa "
            <span className="text-red-400 font-medium">{query}</span>".
            <br />
            Hay thu voi tu khoa khac hoac kiem tra lai chinh ta.
          </p>
          <button
            onClick={onBack}
            className="mt-4 px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white
                       rounded-xl font-semibold text-sm transition-all shadow-lg
                       shadow-red-900/30 active:scale-95"
          >
            Ve trang chu
          </button>
        </motion.div>
      )}

      {/* ── Results Grid ── */}
      {!loading && results.length > 0 && (
        <motion.div
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 lg:gap-6"
          initial="hidden"
          animate="visible"
        >
          {results.map((movie, i) => {
            const displayStars = getDisplayStars(movie.movie_id);
            return (
              <motion.div
                key={movie.movie_id}
                custom={i}
                variants={cardVariants}
                whileHover={{ scale: 1.04, y: -6 }}
                className="relative group cursor-pointer"
              >
                {/* Card container */}
                <div className="relative aspect-[2/3] rounded-xl overflow-hidden
                                border border-white/10 bg-zinc-900
                                shadow-lg shadow-black/40 group-hover:shadow-2xl
                                group-hover:border-white/20 transition-all duration-300">
                  {/* Poster */}
                  <img
                    src={getPosterUrl(movie)}
                    alt={movie.title}
                    loading="lazy"
                    className="w-full h-full object-cover"
                  />

                  {/* Rating badge (top-right) */}
                  {movie.avg_rating > 0 && (
                    <div className="absolute top-2 right-2 flex items-center gap-1
                                    px-2 py-1 rounded-lg bg-black/70 backdrop-blur-sm
                                    border border-white/10 text-xs">
                      <Star size={11} fill="#f59e0b" stroke="#f59e0b" />
                      <span className="text-yellow-400 font-bold">{movie.avg_rating}</span>
                    </div>
                  )}

                  {/* Bottom gradient overlay (always visible) */}
                  <div className="absolute bottom-0 left-0 right-0 p-3
                                  bg-gradient-to-t from-black via-black/80 to-transparent">
                    <p className="text-white text-xs lg:text-sm font-bold truncate mb-1">
                      {movie.title}
                    </p>
                    <p className="text-gray-400 text-[10px] truncate">
                      {movie.genres_orig?.split('|').join(' · ')}
                    </p>

                    {/* Vote count */}
                    {movie.vote_count > 0 && (
                      <p className="text-gray-500 text-[9px] mt-0.5">
                        {movie.vote_count.toLocaleString()} luot danh gia
                      </p>
                    )}
                  </div>

                  {/* ── Hover overlay ── */}
                  <div className="absolute inset-0 bg-black/85 flex flex-col p-4
                                  opacity-0 group-hover:opacity-100 transition-opacity
                                  duration-200 z-10">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-9 h-9 rounded-full bg-white flex items-center
                                      justify-center shadow-lg">
                        <Play size={16} fill="black" className="text-black ml-0.5" />
                      </div>
                      {movie.avg_rating > 0 && (
                        <span className="text-green-400 text-xs font-bold">
                          ★ {movie.avg_rating}
                        </span>
                      )}
                    </div>

                    {/* Genre chips */}
                    <div className="flex flex-wrap gap-1 mb-3">
                      {movie.genres_orig?.split('|').slice(0, 3).map((g, gi) => (
                        <span key={gi} className="px-2 py-0.5 rounded-md bg-white/10
                                                   text-[9px] text-gray-300">
                          {g.trim()}
                        </span>
                      ))}
                    </div>

                    <div className="mt-auto">
                      {/* Star rating */}
                      <div className="flex space-x-1 mb-2">
                        {[1, 2, 3, 4, 5].map((star) => {
                          const isActive = star <= displayStars;
                          return (
                            <Star
                              key={star}
                              size={18}
                              onClick={(e) => handleRateClick(e, movie, star)}
                              onMouseEnter={() =>
                                setHoverRating(p => ({ ...p, [movie.movie_id]: star }))
                              }
                              onMouseLeave={() =>
                                setHoverRating(p => ({ ...p, [movie.movie_id]: 0 }))
                              }
                              fill={isActive ? '#f59e0b' : 'none'}
                              stroke={isActive ? '#f59e0b' : '#6b7280'}
                              className="cursor-pointer hover:scale-125 transition-all"
                            />
                          );
                        })}
                      </div>
                      <h3 className="text-white font-bold text-xs lg:text-sm line-clamp-2">
                        {movie.title}
                      </h3>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
};

export default SearchPage;
