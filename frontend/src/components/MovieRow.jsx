import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Star, ChevronLeft, ChevronRight, Info } from 'lucide-react';
import MovieSkeleton from './MovieSkeleton';
import MovieDetailModal from './MovieDetailModal';
import api from '../api/axios';
import { fixTitle, getPosterUrl } from '../utils/formatTitle';

const MovieRow = ({ title, movies, isLoading, onRate, reason, savedRatings = {} }) => {
  const [hoverRating, setHoverRating]   = useState({});
  const [userRatings, setUserRatings]   = useState({});
  const [detailMovie, setDetailMovie]   = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const scrollRef = useRef(null);


  const handleRateClick = (e, movie, rating) => {
    e.preventDefault();
    e.stopPropagation();
    setUserRatings(prev => ({ ...prev, [movie.movie_id]: rating }));
    if (onRate) onRate(movie.movie_id, movie.title, rating);
  };

  // Thu tu uu tien: hover > click local > da luu DB > 0
  const getDisplayStars = (movieId) => {
    if (hoverRating[movieId]) return hoverRating[movieId];
    if (userRatings[movieId]) return userRatings[movieId];
    if (savedRatings[movieId]) return savedRatings[movieId];
    return 0;
  };

  // Mở detail modal — fetch full detail từ API
  const openDetail = async (e, movie) => {
    e.stopPropagation();
    setDetailMovie(movie);      // hiện modal ngay với data có sẵn
    setDetailLoading(true);
    try {
      const res = await api.get(`/movies/${movie.movie_id}`);
      setDetailMovie(res.data); // cập nhật với đầy đủ metadata
    } catch {
      // fallback giữ nguyên data có sẵn
    } finally {
      setDetailLoading(false);
    }
  };

  // Arrow scroll
  const scroll = (direction) => {
    if (!scrollRef.current) return;
    const amount = scrollRef.current.clientWidth * 0.75;
    scrollRef.current.scrollBy({ left: direction === 'left' ? -amount : amount, behavior: 'smooth' });
  };

  return (
    <>
      <div className="my-12 px-4 lg:px-12 min-h-[300px] group/row">
        {/* ── Header ── */}
        <div className="flex items-baseline space-x-4 mb-4">
          <h2 className="text-xl lg:text-3xl font-bold text-white">{title}</h2>
          {reason && <span className="text-netflix-green text-xs font-bold uppercase tracking-widest">{reason}</span>}
        </div>

        {/* ── Scrollable container ── */}
        <div className="relative">
          {/* Arrow Left */}
          <button
            onClick={() => scroll('left')}
            className="absolute -left-2 lg:-left-4 top-1/2 -translate-y-1/2 z-30
                       w-10 h-10 lg:w-12 lg:h-12 rounded-full
                       bg-zinc-800/90 hover:bg-red-600 border border-white/20
                       flex items-center justify-center
                       transition-all duration-200 cursor-pointer
                       shadow-xl shadow-black/50 hover:scale-110 active:scale-95"
            aria-label="Scroll left"
          >
            <ChevronLeft size={22} className="text-white" />
          </button>

          {/* Arrow Right */}
          <button
            onClick={() => scroll('right')}
            className="absolute -right-2 lg:-right-4 top-1/2 -translate-y-1/2 z-30
                       w-10 h-10 lg:w-12 lg:h-12 rounded-full
                       bg-zinc-800/90 hover:bg-red-600 border border-white/20
                       flex items-center justify-center
                       transition-all duration-200 cursor-pointer
                       shadow-xl shadow-black/50 hover:scale-110 active:scale-95"
            aria-label="Scroll right"
          >
            <ChevronRight size={22} className="text-white" />
          </button>

          {/* ── Movie list ── */}
          <div
            ref={scrollRef}
            className="flex flex-nowrap gap-3 lg:gap-4 overflow-x-auto scrollbar-hide py-6 scroll-smooth"
          >
            {isLoading ? (
              <MovieSkeleton count={6} />
            ) : (
              movies && movies.map((movie) => {
                const displayStars = getDisplayStars(movie.movie_id);
                const hasRated = userRatings[movie.movie_id] > 0;

                return (
                  <motion.div
                    key={movie.movie_id}
                    whileHover={{ scale: 1.08, zIndex: 50 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className="relative flex-shrink-0 w-[150px] sm:w-[170px] lg:w-[200px] xl:w-[220px]
                               aspect-[2/3] cursor-pointer group/card"
                  >
                    {/* Poster */}
                    <img
                      src={getPosterUrl(movie)}
                      alt={movie.title}
                      loading="lazy"
                      className="w-full h-full object-cover rounded-xl
                                 border border-white/10 shadow-lg shadow-black/40
                                 group-hover/card:border-white/20 group-hover/card:shadow-2xl
                                 transition-all duration-300"
                    />

                    {/* Bottom gradient: Tên phim + Sao LUÔN HIỂN THỊ */}
                    <div className="absolute bottom-0 left-0 right-0 p-3 rounded-b-xl
                                    bg-gradient-to-t from-black via-black/80 to-transparent">
                      <p className="text-white text-[10px] lg:text-xs font-bold truncate mb-1">
                        {fixTitle(movie.title)}
                      </p>
                      <div className="flex space-x-0.5 items-center">
                        {[1, 2, 3, 4, 5].map((star) => {
                          const isActive = star <= displayStars;
                          return (
                            <Star
                              key={star}
                              size={13}
                              onMouseEnter={() => setHoverRating(prev => ({ ...prev, [movie.movie_id]: star }))}
                              onMouseLeave={() => setHoverRating(prev => ({ ...prev, [movie.movie_id]: 0 }))}
                              onClick={(e) => handleRateClick(e, movie, star)}
                              fill={isActive ? "#f59e0b" : "none"}
                              stroke={isActive ? "#f59e0b" : "#6b7280"}
                              className="cursor-pointer transition-all duration-150 hover:scale-125"
                            />
                          );
                        })}
                        {hasRated && (
                          <span className="text-yellow-500 text-[10px] font-bold ml-1">
                            {userRatings[movie.movie_id]}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Hover overlay */}
                    <div className="absolute inset-0 bg-black/85 flex flex-col p-4
                                    opacity-0 group-hover/card:opacity-100 transition-opacity duration-200
                                    rounded-xl border border-white/15 z-40">
                      <div className="flex items-center gap-2 mb-3">
                        {/* Info button → mở Detail Modal */}
                        <button
                          onClick={(e) => openDetail(e, movie)}
                          className="w-9 h-9 rounded-full bg-white/10 border border-white/20
                                     flex items-center justify-center hover:bg-white/20 transition"
                          title="Xem chi tiết phim"
                        >
                          <Info size={16} className="text-white" />
                        </button>

                        {/* Removed AI Match Score per user request */}
                      </div>

                      {/* Genre chips */}
                      <div className="flex flex-wrap gap-1 mb-2">
                        {movie.genres_orig?.split('|').slice(0, 3).map((g, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded-md bg-white/10 text-[9px] text-gray-300">
                            {g.trim()}
                          </span>
                        ))}
                      </div>

                      <div className="mt-auto">
                        {/* Sao lớn trong overlay */}
                        <div className="flex space-x-1 mb-2">
                          {[1, 2, 3, 4, 5].map((star) => {
                            const isActive = star <= displayStars;
                            return (
                              <Star
                                key={star}
                                size={20}
                                onClick={(e) => handleRateClick(e, movie, star)}
                                onMouseEnter={() => setHoverRating(prev => ({ ...prev, [movie.movie_id]: star }))}
                                onMouseLeave={() => setHoverRating(prev => ({ ...prev, [movie.movie_id]: 0 }))}
                                fill={isActive ? "#f59e0b" : "none"}
                                stroke={isActive ? "#f59e0b" : "#6b7280"}
                                className="cursor-pointer hover:scale-125 transition-all"
                              />
                            );
                          })}
                        </div>
                        <h3 className="text-white font-bold text-xs lg:text-sm line-clamp-2">{fixTitle(movie.title)}</h3>
                        <p className="text-gray-400 text-[9px] mt-1">{movie.genres_orig?.split('|').join(' · ')}</p>
                      </div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* ── Movie Detail Modal ──────────────────────────────── */}
      {detailMovie && (
        <MovieDetailModal
          movie={detailMovie}
          onClose={() => setDetailMovie(null)}
        />
      )}
    </>
  );
};

export default MovieRow;
