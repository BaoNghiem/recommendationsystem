import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Info, ChevronLeft, ChevronRight } from 'lucide-react';
import MovieDetailModal from './MovieDetailModal';
import api from '../api/axios';
import { fixTitle, splitTitle, getPosterUrl } from '../utils/formatTitle';

/* ── Bảng màu gradient cho từng slide (xoay vòng) ── */
const GRADIENTS = [
  'linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%)',
  'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
  'linear-gradient(135deg, #141e30 0%, #243b55 100%)',
  'linear-gradient(135deg, #1b1b2f 0%, #162447 50%, #1f4068 100%)',
  'linear-gradient(135deg, #0d1117 0%, #161b22 40%, #21262d 100%)',
  'linear-gradient(135deg, #1a002e 0%, #2d0045 40%, #1a1a2e 100%)',
  'linear-gradient(135deg, #0a1628 0%, #1c3a5f 50%, #0d2137 100%)',
  'linear-gradient(135deg, #1c1c1c 0%, #2c2c2c 40%, #3a3a3a 100%)',
  'linear-gradient(135deg, #071a2b 0%, #0e3b5e 50%, #071a2b 100%)',
  'linear-gradient(135deg, #1a0000 0%, #3d0000 40%, #1a0000 100%)',
];

const AUTO_SLIDE_INTERVAL = 10000;

const Hero = ({ movies = [], onWatch }) => {
  const [currentIndex, setCurrentIndex]   = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [detailMovie, setDetailMovie]     = useState(null);
  const timerRef   = useRef(null);
  const touchStartX = useRef(0);
  const touchEndX   = useRef(0);

  const heroMovies = movies.slice(0, 10);
  const total      = heroMovies.length;

  /* ── Auto-slide ── */
  const resetTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (total <= 1) return;
    timerRef.current = setInterval(() => goNext(), AUTO_SLIDE_INTERVAL);
  }, [total]);

  useEffect(() => {
    resetTimer();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [resetTimer]);

  /* ── Navigation ── */
  const goTo = (index) => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    setCurrentIndex(index);
    resetTimer();
    setTimeout(() => setIsTransitioning(false), 600);
  };

  const goNext = () => {
    // BUG FIX: Them isTransitioning guard giong goPrev() de tranh animation chong
    if (isTransitioning) return;
    setIsTransitioning(true);
    setCurrentIndex(prev => (prev + 1) % (total || 1));
    resetTimer();
    setTimeout(() => setIsTransitioning(false), 600);
  };

  const goPrev = () => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    setCurrentIndex(prev => (prev - 1 + total) % (total || 1));
    resetTimer();
    setTimeout(() => setIsTransitioning(false), 600);
  };

  /* ── Touch / Swipe ── */
  const handleTouchStart = (e) => { touchStartX.current = e.changedTouches[0].screenX; };
  const handleTouchEnd   = (e) => {
    touchEndX.current = e.changedTouches[0].screenX;
    const diff = touchStartX.current - touchEndX.current;
    if (Math.abs(diff) > 60) { if (diff > 0) goNext(); else goPrev(); }
  };

  /* ── Keyboard ── */
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowRight') goNext();
      if (e.key === 'ArrowLeft')  goPrev();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [total]);

  /* ── Mở detail modal ── */
  const openDetail = async (movie) => {
    setDetailMovie(movie);      // hiện ngay với data có sẵn
    try {
      const res = await api.get(`/movies/${movie.movie_id}`);
      setDetailMovie(res.data); // cập nhật với full metadata
    } catch { /* giữ data có sẵn */ }
  };

  if (!heroMovies.length) return null;

  const movie    = heroMovies[currentIndex] || heroMovies[0];
  const gradient = GRADIENTS[currentIndex % GRADIENTS.length];

  const { name: displayTitle, year: displayYear } = splitTitle(movie.title);

  return (
    <>
      <div
        className="relative w-full select-none"
        style={{ height: '85vh' }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {/* ── Background layer ── */}
        <div
          className="absolute inset-0 transition-all duration-700 ease-in-out"
          style={{ background: gradient }}
        >
          {/* Decorative circles */}
          <div
            className="absolute rounded-full opacity-[0.06] blur-3xl"
            style={{
              width: '60vw', height: '60vw',
              top: '-20%', right: '-15%',
              background: 'radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%)',
            }}
          />
          <div
            className="absolute rounded-full opacity-[0.04] blur-3xl"
            style={{
              width: '40vw', height: '40vw',
              bottom: '-10%', left: '-10%',
              background: 'radial-gradient(circle, rgba(220,38,38,0.4) 0%, transparent 70%)',
            }}
          />
          {/* Bottom fade — pointer-events-none để không chặn click các dots phía dưới */}
          <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-zinc-950 to-transparent pointer-events-none" />
        </div>

        {/* ── Content center ── */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center z-10 transition-all duration-500"
          key={currentIndex}
          style={{ animation: 'heroFadeIn 0.6s ease-out' }}
        >
          {/* Year badge */}
          {displayYear && (
            <span
              className="mb-4 px-4 py-1 rounded-full text-sm font-semibold tracking-wider uppercase"
              style={{
                background: 'rgba(220,38,38,0.2)',
                border: '1px solid rgba(220,38,38,0.4)',
                color: '#f87171',
              }}
            >
              {displayYear}
            </span>
          )}

          {/* Main title */}
          <h1
            className="text-center font-black leading-none tracking-tight drop-shadow-2xl px-8"
            style={{
              fontSize: 'clamp(2.5rem, 7vw, 6rem)',
              color: '#fff',
              textShadow: '0 4px 30px rgba(0,0,0,0.5), 0 0 80px rgba(220,38,38,0.15)',
              maxWidth: '80vw',
              wordBreak: 'break-word',
            }}
          >
            {displayTitle}
          </h1>

          {/* Genre tags */}
          {movie.genres_orig && (
            <div className="flex flex-wrap justify-center gap-2 mt-6 px-4">
              {movie.genres_orig.split('|').map((g, i) => (
                <span
                  key={i}
                  className="px-3 py-1 rounded-full text-xs font-medium"
                  style={{
                    background: 'rgba(255,255,255,0.08)',
                    border: '1px solid rgba(255,255,255,0.12)',
                    color: '#d4d4d8',
                  }}
                >
                  {g.trim()}
                </span>
              ))}
            </div>
          )}

          {/* Nút Phát ngay và Chi tiết */}
          <div className="flex gap-4 mt-8">
            <button
              onClick={() => onWatch?.(movie)}
              className="flex items-center px-8 py-3 bg-white/10 text-white font-bold text-base
                         rounded-lg backdrop-blur-md border border-white/10 shadow-xl
                         hover:bg-amber-500 hover:text-black hover:border-amber-500 hover:shadow-amber-500/20
                         transition-all duration-300 transform active:scale-95 group"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="mr-2">
                <path d="M8 5v14l11-7z" />
              </svg>
              Phát ngay
            </button>
            <button
              onClick={() => openDetail(movie)}
              className="flex items-center px-8 py-3 bg-white/10 text-white font-bold text-base
                         rounded-lg hover:bg-white/20 transition transform active:scale-95
                         backdrop-blur-md border border-white/10 shadow-xl"
            >
              <Info size={20} className="mr-2" />
              Chi tiết
            </button>
          </div>
        </div>

        {/* ── Poster bên phải (chỉ hiện khi có ảnh thật) ── */}
        {movie.poster_url && (
          <div className="absolute right-8 lg:right-16 top-1/2 -translate-y-1/2 z-10
                          hidden lg:block pointer-events-none">
            <div className="w-36 xl:w-48 aspect-[2/3] rounded-2xl overflow-hidden
                            shadow-2xl shadow-black/60 border border-white/10
                            ring-1 ring-white/5">
              <img
                src={getPosterUrl(movie)}
                alt={movie.title}
                className="w-full h-full object-cover object-top"
              />
            </div>
          </div>
        )}

        {/* ── Arrow buttons — z-20 (thấp hơn modal z-300) ── */}
        {total > 1 && (
          <>
            <button
              onClick={goPrev}
              className="absolute left-4 top-1/2 -translate-y-1/2 z-20 w-12 h-12
                         flex items-center justify-center rounded-full
                         bg-black/30 hover:bg-black/60 backdrop-blur-sm border border-white/10
                         transition-all hover:scale-110 text-white"
              aria-label="Previous"
            >
              <ChevronLeft size={24} />
            </button>
            <button
              onClick={() => goTo((currentIndex + 1) % total)}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-20 w-12 h-12
                         flex items-center justify-center rounded-full
                         bg-black/30 hover:bg-black/60 backdrop-blur-sm border border-white/10
                         transition-all hover:scale-110 text-white"
              aria-label="Next"
            >
              <ChevronRight size={24} />
            </button>
          </>
        )}

        {/* ── Dot indicators — z-30, bottom-14 — */}
        {total > 1 && (
          <div className="absolute bottom-14 left-1/2 -translate-x-1/2 z-30 flex gap-2">
            {heroMovies.map((_, i) => (
              <button
                key={i}
                onClick={() => goTo(i)}
                className="transition-all duration-300 rounded-full"
                aria-label={`Slide ${i + 1}`}
                style={{
                  width:  i === currentIndex ? 32 : 10,
                  height: 10,
                  background: i === currentIndex
                    ? 'linear-gradient(90deg, #dc2626, #ef4444)'
                    : 'rgba(255,255,255,0.25)',
                  border: i === currentIndex ? 'none' : '1px solid rgba(255,255,255,0.1)',
                }}
              />
            ))}
          </div>
        )}

        {/* ── Progress bar — z-10 ── */}
        {total > 1 && (
          <div className="absolute top-0 left-0 w-full h-[3px] z-10 bg-white/5">
            <div
              className="h-full bg-gradient-to-r from-red-600 to-red-400"
              style={{
                animation: `heroProgress ${AUTO_SLIDE_INTERVAL}ms linear infinite`,
                animationDelay: '0ms',
              }}
              key={currentIndex}
            />
          </div>
        )}

        {/* ── CSS Keyframes ── */}
        <style>{`
          @keyframes heroFadeIn {
            from { opacity: 0; transform: translateY(20px) scale(0.97); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
          }
          @keyframes heroProgress {
            from { width: 0%; }
            to   { width: 100%; }
          }
        `}</style>
      </div>

      {/* ── Movie Detail Modal — render NGOÀI Hero div (tránh stacking context) ── */}
      {detailMovie && (
        <MovieDetailModal
          movie={detailMovie}
          onClose={() => setDetailMovie(null)}
        />
      )}
    </>
  );
};

export default Hero;
