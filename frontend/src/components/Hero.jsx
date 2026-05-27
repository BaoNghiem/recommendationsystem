import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Play, Info, ChevronLeft, ChevronRight } from 'lucide-react';

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

const AUTO_SLIDE_INTERVAL = 10000; // 10 giây

/**
 * Sửa định dạng tiêu đề MovieLens:
 *   "Wrong Trousers, The (1993)" → "The Wrong Trousers (1993)"
 *   "Godfather, The (1972)"      → "The Godfather (1972)"
 *   "Bug's Life, A (1998)"       → "A Bug's Life (1998)"
 * Hỗ trợ các mạo từ: The, A, An
 */
function fixTitle(raw) {
  if (!raw) return '';
  // Pattern: "Tên phim, Article (Year)" hoặc "Tên phim, Article"
  const match = raw.match(/^(.+),\s*(The|A|An)\s*(\((\d{4})\))?\s*$/i);
  if (match) {
    const name = match[1].trim();
    const article = match[2];
    const yearPart = match[3] || '';
    return `${article} ${name} ${yearPart}`.trim();
  }
  return raw;
}

const Hero = ({ movies = [] }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const timerRef = useRef(null);
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);

  const heroMovies = movies.slice(0, 10);
  const total = heroMovies.length;

  /* ── Auto-slide ── */
  const resetTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (total <= 1) return;
    timerRef.current = setInterval(() => {
      goNext();
    }, AUTO_SLIDE_INTERVAL);
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
    setCurrentIndex(prev => (prev + 1) % (total || 1));
    resetTimer();
  };

  const goPrev = () => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    setCurrentIndex(prev => (prev - 1 + total) % (total || 1));
    resetTimer();
    setTimeout(() => setIsTransitioning(false), 600);
  };

  /* ── Touch / Swipe support ── */
  const handleTouchStart = (e) => {
    touchStartX.current = e.changedTouches[0].screenX;
  };
  const handleTouchEnd = (e) => {
    touchEndX.current = e.changedTouches[0].screenX;
    const diff = touchStartX.current - touchEndX.current;
    if (Math.abs(diff) > 60) {
      if (diff > 0) goNext(); else goPrev();
    }
  };

  /* ── Keyboard support ── */
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowRight') goNext();
      if (e.key === 'ArrowLeft') goPrev();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [total]);

  if (!heroMovies.length) return null;

  const movie = heroMovies[currentIndex] || heroMovies[0];
  const gradient = GRADIENTS[currentIndex % GRADIENTS.length];

  /* ── Sửa title MovieLens + tách year ── */
  const fixedTitle = fixTitle(movie.title);
  const titleMatch = fixedTitle.match(/^(.+?)\s*\((\d{4})\)\s*$/);
  const displayTitle = titleMatch ? titleMatch[1].trim() : fixedTitle;
  const displayYear = titleMatch ? titleMatch[2] : '';

  return (
    <div
      className="relative w-full overflow-hidden select-none"
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
        {/* Bottom gradient fade */}
        <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-zinc-950 to-transparent" />
      </div>

      {/* ── Movie Title — BIG center text ── */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center z-10 transition-all duration-500"
        key={currentIndex}
        style={{
          animation: 'heroFadeIn 0.6s ease-out',
        }}
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

        {/* Buttons */}
        <div className="flex gap-4 mt-8">
          <button className="flex items-center px-8 py-3 bg-white text-black font-bold text-base rounded-lg hover:bg-gray-200 transition transform active:scale-95 shadow-xl">
            <Play fill="black" size={20} className="mr-2" /> Phát ngay
          </button>
          <button className="flex items-center px-8 py-3 bg-white/10 text-white font-bold text-base rounded-lg hover:bg-white/20 transition transform active:scale-95 backdrop-blur-md border border-white/10 shadow-xl">
            <Info size={20} className="mr-2" /> Chi tiết
          </button>
        </div>
      </div>

      {/* ── Arrow buttons ── */}
      {total > 1 && (
        <>
          <button
            onClick={goPrev}
            className="absolute left-4 top-1/2 -translate-y-1/2 z-30 w-12 h-12 flex items-center justify-center rounded-full bg-black/30 hover:bg-black/60 backdrop-blur-sm border border-white/10 transition-all hover:scale-110 text-white"
            aria-label="Previous"
          >
            <ChevronLeft size={24} />
          </button>
          <button
            onClick={() => goTo((currentIndex + 1) % total)}
            className="absolute right-4 top-1/2 -translate-y-1/2 z-30 w-12 h-12 flex items-center justify-center rounded-full bg-black/30 hover:bg-black/60 backdrop-blur-sm border border-white/10 transition-all hover:scale-110 text-white"
            aria-label="Next"
          >
            <ChevronRight size={24} />
          </button>
        </>
      )}

      {/* ── Dot indicators ── */}
      {total > 1 && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30 flex gap-2">
          {heroMovies.map((_, i) => (
            <button
              key={i}
              onClick={() => goTo(i)}
              className="transition-all duration-300 rounded-full"
              aria-label={`Slide ${i + 1}`}
              style={{
                width: i === currentIndex ? 32 : 10,
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

      {/* ── Progress bar (auto-slide visual) ── */}
      {total > 1 && (
        <div className="absolute top-0 left-0 w-full h-[3px] z-30 bg-white/5">
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
  );
};

export default Hero;
