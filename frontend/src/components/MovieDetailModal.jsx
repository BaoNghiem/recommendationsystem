import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Star, Globe, Calendar, Tv2, Film,
  Info, Tag, BarChart3, Users, Video, UserCircle
} from 'lucide-react';
import { fixTitle, getPosterUrl } from '../utils/formatTitle';
import PersonInfoModal from './PersonInfoModal';

/**
 * MovieDetailModal — Chi tiết phim bao gồm cast (đạo diễn + diễn viên).
 * Props:
 *   movie:   object { movie_id, title, genres_orig, release_year, country,
 *                     total_episodes, description, avg_rating, vote_count,
 *                     directors: [], actors: [] }
 *   onClose: callback
 */
export default function MovieDetailModal({ movie, onClose, onWatch }) {
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [hasVideo, setHasVideo]             = useState(false);
  const [checkingVideo, setCheckingVideo]   = useState(true);

  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  // Check if video available
  useEffect(() => {
    if (!movie?.movie_id) return;
    setCheckingVideo(true);
    import('../api/axios').then(({ default: axiosInst }) => {
      axiosInst.get(`/videos/${movie.movie_id}/info`)
        .then(res => setHasVideo(res.data?.has_video === true))
        .catch(() => setHasVideo(false))
        .finally(() => setCheckingVideo(false));
    });
  }, [movie?.movie_id]);

  if (!movie) return null;

  const genres = (movie.genres_orig || '').split('|').map(g => g.trim()).filter(Boolean);
  const directors = movie.directors || [];
  const actors    = movie.actors    || [];

  const genreGradients = {
    Action: 'from-red-600/30 to-orange-600/10',
    Drama: 'from-blue-600/30 to-indigo-600/10',
    Comedy: 'from-yellow-500/30 to-amber-600/10',
    Horror: 'from-purple-700/30 to-violet-900/10',
    Romance: 'from-pink-600/30 to-rose-700/10',
    'Sci-Fi': 'from-cyan-600/30 to-blue-700/10',
    Thriller: 'from-slate-600/30 to-gray-700/10',
    Animation: 'from-emerald-500/30 to-teal-600/10',
    Documentary: 'from-amber-600/30 to-yellow-700/10',
  };
  const gradient = genreGradients[genres[0]] || 'from-amber-600/20 to-zinc-900/10';

  const modalContent = (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 bg-black/85 backdrop-blur-md"
        style={{ zIndex: 9998 }}
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
      />

      <motion.div
        className="fixed inset-0 flex items-center justify-center p-4 pointer-events-none"
        style={{ zIndex: 9999 }}
        initial={{ opacity: 0, scale: 0.92, y: 24 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 24 }}
        transition={{ type: 'spring', damping: 24, stiffness: 280 }}
      >
        <div
          className="pointer-events-auto w-full max-w-2xl bg-zinc-900 border border-white/10
                     rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
          onClick={e => e.stopPropagation()}
        >
          {/* Hero banner */}
          <div className={`relative bg-gradient-to-br ${gradient} px-7 pt-7 pb-6 flex-shrink-0`}>
            <button
              onClick={onClose}
              className="absolute top-4 right-4 w-8 h-8 rounded-full bg-black/30
                         flex items-center justify-center text-gray-400
                         hover:text-white hover:bg-black/50 transition"
            >
              <X size={16} />
            </button>

            <div className="flex items-start gap-4">
              {/* Poster thumbnail hoac icon */}
              {movie.poster_url ? (
                <div className="w-14 h-20 rounded-xl overflow-hidden border border-white/15
                                flex-shrink-0 shadow-lg">
                  <img
                    src={getPosterUrl(movie)}
                    alt={movie.title}
                    className="w-full h-full object-cover object-top"
                  />
                </div>
              ) : (
                <div className="w-14 h-14 rounded-xl bg-white/10 border border-white/10
                                flex items-center justify-center flex-shrink-0 shadow-lg">
                  {movie.total_episodes
                    ? <Tv2 size={26} className="text-amber-400" />
                    : <Film size={26} className="text-amber-400" />}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs text-amber-400/80 font-mono mb-1">#{movie.movie_id}</p>
                <h2 className="text-xl font-bold text-white leading-tight line-clamp-2 pr-8">
                  {fixTitle(movie.title)}
                </h2>
                {directors.length > 0 && (
                  <p className="text-sm text-gray-400 mt-1 flex items-center gap-1.5">
                    <Video size={12} className="text-gray-500" />
                    {directors.map(d => d.name).join(', ')}
                  </p>
                )}
                {!directors.length && (
                  <p className="text-sm text-gray-400 mt-1">
                    {movie.total_episodes ? `TV Series · ${movie.total_episodes} tập` : 'Feature Film'}
                  </p>
                )}
              </div>
            </div>

            {movie.avg_rating && (
              <div className="mt-5 flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <Star size={16} className="text-amber-400 fill-amber-400" />
                  <span className="text-lg font-bold text-white">{movie.avg_rating?.toFixed(1)}</span>
                  <span className="text-gray-500 text-sm">/5.0</span>
                </div>
                <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(movie.avg_rating / 5) * 100}%` }}
                    transition={{ delay: 0.2, duration: 0.6, ease: 'easeOut' }}
                  />
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Users size={12} />
                  {(movie.vote_count || 0).toLocaleString()} đánh giá
                </div>
              </div>
            )}
          </div>

          {/* Scrollable body */}
          <div className="px-7 py-5 space-y-5 overflow-y-auto flex-1 scrollbar-hide">

            {/* Metadata */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {movie.release_year && (
                <MetaBadge icon={<Calendar size={14} />} label="Năm" value={movie.release_year} />
              )}
              {movie.country && (
                <MetaBadge icon={<Globe size={14} />} label="Quốc gia" value={movie.country} />
              )}
              {movie.total_episodes
                ? <MetaBadge icon={<Tv2 size={14} />} label="Số tập" value={`${movie.total_episodes} tập`} />
                : <MetaBadge icon={<Film size={14} />} label="Định dạng" value="Phim lẻ" />
              }
              {movie.vote_count !== undefined && (
                <MetaBadge icon={<BarChart3 size={14} />} label="Lượt đánh giá"
                  value={(movie.vote_count || 0).toLocaleString()} />
              )}
            </div>

            {/* Directors */}
            {directors.length > 0 && (
              <div>
                <SectionLabel icon={<Video size={12} />} label="Đạo diễn" />
                <div className="flex flex-wrap gap-2 mt-2.5">
                  {directors.map(d => (
                    <PersonChip 
                      key={`dir-${d.director_id}`} 
                      name={d.name} 
                      sub={d.nationality} 
                      color="blue" 
                      onClick={() => setSelectedPerson({ type: 'director', ...d })}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Actors */}
            {actors.length > 0 && (
              <div>
                <SectionLabel icon={<UserCircle size={12} />} label={`Diễn viên (${actors.length})`} />
                <div className="flex flex-wrap gap-2 mt-2.5">
                  {actors.map(a => (
                    <PersonChip
                      key={`act-${a.actor_id}`}
                      name={a.name}
                      sub={a.character_name || a.nationality}
                      color="violet"
                      onClick={() => setSelectedPerson({ type: 'actor', ...a })}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Genres */}
            {genres.length > 0 && (
              <div>
                <SectionLabel icon={<Tag size={12} />} label="Thể loại" />
                <div className="flex flex-wrap gap-2 mt-2.5">
                  {genres.map(g => (
                    <span key={g}
                      className="px-3 py-1 rounded-full text-xs font-medium
                                 bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Description */}
            {movie.description && movie.description !== '(Chưa có mô tả)' ? (
              <div>
                <SectionLabel icon={<Info size={12} />} label="Mô tả" />
                <p className="text-sm text-gray-300 leading-relaxed mt-2.5">{movie.description}</p>
              </div>
            ) : (
              <p className="text-sm text-gray-600 italic text-center py-2">
                Chưa có mô tả cho bộ phim này.
              </p>
            )}
          </div>

          {/* Footer */}
          <div className="px-7 py-4 border-t border-white/5 flex items-center justify-between flex-shrink-0">
            {/* Watch button */}
            <div>
              {!checkingVideo && onWatch && (
                <button
                  id="movie-watch-btn"
                  onClick={() => { onClose(); onWatch(movie); }}
                  className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold
                               transition-all ${
                    hasVideo
                      ? 'bg-amber-500 hover:bg-amber-400 text-black shadow-lg shadow-amber-500/20'
                      : 'bg-white/5 border border-white/10 text-gray-500 cursor-not-allowed'
                  }`}
                  disabled={!hasVideo}
                  title={hasVideo ? 'Xem phim ngay' : 'Chưa có video'}
                >
                  {hasVideo ? (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                      {movie.total_episodes ? 'Xem tập phim' : 'Xem phim'}
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                      Chưa có video
                    </>
                  )}
                </button>
              )}
            </div>

            <button
              onClick={onClose}
              className="px-5 py-2 rounded-lg text-sm font-medium text-gray-400
                         bg-white/5 border border-white/10 hover:bg-white/10 hover:text-white transition"
            >
              Đóng
            </button>
          </div>
        </div>
      </motion.div>

      {/* Person Info Modal */}
      <AnimatePresence>
        {selectedPerson && (
          <PersonInfoModal 
            person={selectedPerson} 
            onClose={() => setSelectedPerson(null)} 
          />
        )}
      </AnimatePresence>
    </AnimatePresence>
  );

  return createPortal(modalContent, document.body);
}

function SectionLabel({ icon, label }) {
  return (
    <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wider">
      {icon}
      {label}
    </div>
  );
}

function MetaBadge({ icon, label, value }) {
  return (
    <div className="bg-white/5 border border-white/8 rounded-xl px-4 py-3">
      <div className="flex items-center gap-1.5 text-gray-500 text-xs mb-1">{icon}{label}</div>
      <p className="text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function PersonChip({ name, sub, color, onClick }) {
  const colors = {
    blue:   'bg-blue-500/10 text-blue-300 border-blue-500/20 hover:bg-blue-500/20',
    violet: 'bg-violet-500/10 text-violet-300 border-violet-500/20 hover:bg-violet-500/20',
  };
  return (
    <button 
      type="button"
      onClick={onClick}
      className={`px-3 py-1.5 rounded-xl text-xs border ${colors[color] || colors.blue} flex flex-col text-left transition-colors cursor-pointer`}
    >
      <span className="font-semibold">{name}</span>
      {sub && <span className="text-[10px] opacity-60 mt-0.5">{sub}</span>}
    </button>
  );
}
