import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X, Film, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

const ALL_GENRES = [
  "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime",
  "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
  "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
];

/**
 * Modal form để Thêm / Sửa phim.
 * Props:
 *   mode:    'create' | 'edit'
 *   movie:   { movie_id, title, genres_orig } | null  (khi edit)
 *   onClose: callback đóng modal
 *   onSave:  async (formData) => void  — gọi API, throw nếu lỗi
 */
export default function MovieFormModal({ mode = 'create', movie = null, onClose, onSave }) {
  const [title, setTitle] = useState('');
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // Populate form khi edit
  useEffect(() => {
    if (mode === 'edit' && movie) {
      setTitle(movie.title || '');
      const existing = (movie.genres_orig || '')
        .split('|')
        .map(g => g.trim())
        .filter(Boolean);
      setSelectedGenres(existing);
    } else {
      setTitle('');
      setSelectedGenres([]);
    }
    setFeedback(null);
  }, [mode, movie]);

  const toggleGenre = (genre) => {
    setSelectedGenres(prev =>
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return setFeedback({ type: 'error', msg: 'Tên phim không được để trống.' });
    if (selectedGenres.length === 0) return setFeedback({ type: 'error', msg: 'Chọn ít nhất 1 thể loại.' });

    setLoading(true);
    setFeedback(null);
    try {
      await onSave({
        title: title.trim(),
        genres_str: selectedGenres.join('|'),
        movie_id: movie?.movie_id,
      });
      setFeedback({ type: 'success', msg: mode === 'create' ? 'Thêm phim thành công!' : 'Cập nhật thành công!' });
      setTimeout(onClose, 800);
    } catch (err) {
      setFeedback({ type: 'error', msg: err.message || 'Đã xảy ra lỗi.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <motion.div
        className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
      />

      {/* Modal */}
      <motion.div
        className="fixed inset-0 z-[201] flex items-center justify-center p-4 pointer-events-none"
        initial={{ opacity: 0, scale: 0.92, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 20 }}
        transition={{ type: 'spring', damping: 22, stiffness: 300 }}
      >
        <div
          className="pointer-events-auto w-full max-w-lg bg-zinc-900 border border-white/10
                     rounded-2xl shadow-2xl overflow-hidden"
          onClick={e => e.stopPropagation()}
        >
          {/* Gradient bar */}
          <div className="h-1 w-full bg-gradient-to-r from-amber-500 via-orange-500 to-red-500" />

          {/* Header */}
          <div className="flex items-center justify-between px-6 pt-5">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-600 flex items-center justify-center">
                <Film size={18} className="text-white" />
              </div>
              <h2 className="text-lg font-bold text-white">
                {mode === 'create' ? 'Thêm phim mới' : `Sửa phim #${movie?.movie_id}`}
              </h2>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition">
              <X size={20} />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-6 pt-5 pb-6 space-y-5">
            {/* Title */}
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Tên phim</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Ví dụ: The Matrix (1999)"
                className="w-full bg-white/5 border border-white/10 rounded-lg py-2.5 px-3
                           text-white text-sm placeholder-gray-500 outline-none
                           focus:border-amber-500 focus:ring-1 focus:ring-amber-500/40 transition"
              />
            </div>

            {/* Genre chips */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Thể loại <span className="text-gray-600">({selectedGenres.length} đã chọn)</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {ALL_GENRES.map(genre => {
                  const active = selectedGenres.includes(genre);
                  return (
                    <button
                      key={genre}
                      type="button"
                      onClick={() => toggleGenre(genre)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all
                        ${active
                          ? 'bg-amber-600/20 text-amber-400 border-amber-500/50 shadow-sm shadow-amber-900/20'
                          : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/20 hover:text-gray-300'
                        }`}
                    >
                      {genre}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Preview */}
            {selectedGenres.length > 0 && (
              <div className="text-xs text-gray-500 bg-white/5 rounded-lg px-3 py-2">
                <span className="text-gray-400">genres_str:</span>{' '}
                <span className="text-amber-400 font-mono">{selectedGenres.join('|')}</span>
              </div>
            )}

            {/* Feedback */}
            <AnimatePresence>
              {feedback && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${
                    feedback.type === 'success'
                      ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                      : 'bg-red-500/10 text-red-400 border border-red-500/20'
                  }`}
                >
                  {feedback.type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
                  {feedback.msg}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-2.5 rounded-lg text-sm font-medium text-gray-400
                           bg-white/5 border border-white/10 hover:bg-white/10 transition"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white
                           bg-gradient-to-r from-amber-600 to-orange-600
                           hover:from-amber-500 hover:to-orange-500
                           disabled:opacity-50 disabled:cursor-not-allowed
                           shadow-lg shadow-amber-900/30 transition-all
                           flex items-center justify-center gap-2"
              >
                {loading && <Loader2 size={15} className="animate-spin" />}
                {mode === 'create' ? 'Thêm phim' : 'Cập nhật'}
              </button>
            </div>
          </form>
        </div>
      </motion.div>
    </>
  );
}
