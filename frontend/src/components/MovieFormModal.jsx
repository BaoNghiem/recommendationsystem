import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  X, Film, Tv2, Loader2, CheckCircle, AlertCircle, ChevronDown,
  Video, UserCircle, Plus, Trash2, Search, ImagePlus, UploadCloud
} from 'lucide-react';
import api from '../api/axios';

const ALL_GENRES = [
  "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime",
  "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
  "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
];

const COUNTRIES = [
  "Mỹ", "Anh", "Pháp", "Đức", "Ý", "Nhật Bản", "Hàn Quốc", "Ấn Độ",
  "Úc", "Canada", "Tây Ban Nha", "Thụy Điển", "Đan Mạch", "Ireland",
  "Hồng Kông", "Trung Quốc", "Việt Nam", "Khác",
];

/**
 * MovieFormModal — Thêm / Sửa phim với tab Cast (đạo diễn + diễn viên).
 * Tabs: Info | Cast
 */
export default function MovieFormModal({ mode = 'create', movie = null, onClose, onSave }) {
  const [tab, setTab] = useState('info');

  // ── Info fields ──
  const [title, setTitle]                   = useState('');
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [releaseYear, setReleaseYear]       = useState('');
  const [country, setCountry]               = useState('');
  const [totalEpisodes, setTotalEpisodes]   = useState('');
  const [description, setDescription]       = useState('');
  const [isSerial, setIsSerial]             = useState(false);
  const [loading, setLoading]               = useState(false);
  const [feedback, setFeedback]             = useState(null);

  // Poster upload state
  const [posterFile, setPosterFile]         = useState(null);
  const [posterPreview, setPosterPreview]   = useState(null);
  const [existingPoster, setExistingPoster] = useState(null);
  const fileInputRef                        = useRef(null);

  // ── Cast state (only active when editing) ──
  const [directors, setDirectors] = useState([]);
  const [actors, setActors]       = useState([]);
  const [castLoading, setCastLoading] = useState(false);
  const [pendingOps, setPendingOps]   = useState([]);

  // Populate form when editing
  useEffect(() => {
    if (mode === 'edit' && movie) {
      setTitle(movie.title || '');
      setSelectedGenres((movie.genres_orig || '').split('|').map(g => g.trim()).filter(Boolean));
      setReleaseYear(movie.release_year ? String(movie.release_year) : '');
      setCountry(movie.country || '');
      setTotalEpisodes(movie.total_episodes ? String(movie.total_episodes) : '');
      setDescription(movie.description || '');
      setIsSerial(!!movie.total_episodes);
      setExistingPoster(movie.poster_url || null);
      setPosterFile(null);
      setPosterPreview(null);
      // Fetch current cast
      fetchCast(movie.movie_id);
    } else {
      setTitle(''); setSelectedGenres([]);
      setReleaseYear(''); setCountry('');
      setTotalEpisodes(''); setDescription('');
      setIsSerial(false);
      setDirectors([]); setActors([]);
      setPendingOps([]);
      setPosterFile(null); setPosterPreview(null); setExistingPoster(null);
    }
    setFeedback(null);
    setTab('info');
  }, [mode, movie]);

  const fetchCast = async (movieId) => {
    if (!movieId) return;
    setCastLoading(true);
    try {
      const res = await api.get(`/admin/movies/${movieId}/cast`);
      setDirectors(res.data.directors || []);
      setActors(res.data.actors || []);
    } catch { /* ignore */ }
    finally { setCastLoading(false); }
  };

  const toggleGenre = (genre) =>
    setSelectedGenres(prev => prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return setFeedback({ type: 'error', msg: 'Tên phim không được để trống.' });
    if (selectedGenres.length === 0) return setFeedback({ type: 'error', msg: 'Chọn ít nhất 1 thể loại.' });
    if (releaseYear && (isNaN(releaseYear) || +releaseYear < 1888 || +releaseYear > 2100))
      return setFeedback({ type: 'error', msg: 'Năm ra mắt không hợp lệ.' });

    setLoading(true); setFeedback(null);
    try {
      await onSave({
        title, genres_str: selectedGenres.join('|'),
        release_year: releaseYear ? parseInt(releaseYear) : null,
        country: country || null,
        total_episodes: isSerial && totalEpisodes ? parseInt(totalEpisodes) : null,
        description: description.trim() || null,
        movie_id: movie?.movie_id,
      });

      // ── Process pending cast operations (only in edit mode) ──
      if (mode === 'edit' && movie?.movie_id) {
        for (const op of pendingOps) {
          try {
            if (op.type === 'add_director') await api.post(`/admin/movies/${movie.movie_id}/directors`, op.data);
            if (op.type === 'remove_director') await api.delete(`/admin/movies/${movie.movie_id}/directors/${op.data.director_id}`);
            if (op.type === 'add_actor') await api.post(`/admin/movies/${movie.movie_id}/actors`, op.data);
            if (op.type === 'remove_actor') await api.delete(`/admin/movies/${movie.movie_id}/actors/${op.data.actor_id}`);
          } catch (e) {
            console.error('[Cast Update Error]', e);
          }
        }
      }

      setFeedback({ type: 'success', msg: mode === 'create' ? 'Thêm phim thành công!' : 'Cập nhật thành công!' });

      // Upload poster nếu có chọn file
      const savedId = movie?.movie_id || null;
      if (posterFile && savedId) {
        try {
          const formData = new FormData();
          formData.append('file', posterFile);
          await api.post(`/admin/movies/${savedId}/poster`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });
        } catch (err) {
          console.warn('[Poster upload error]', err.message);
        }
      }

      setTimeout(onClose, 800);
    } catch (err) {
      setFeedback({ type: 'error', msg: err.message || 'Đã xảy ra lỗi.' });
    } finally { setLoading(false); }
  };

  // ── Cast handlers (Local caching) ──
  const handleAssignDirector = (director) => {
    // Kiem tra da ton tai chua
    if (directors.some(d => d.director_id === director.director_id)) return;
    setDirectors(prev => [...prev, director]);
    setPendingOps(prev => [...prev, { type: 'add_director', data: { director_id: director.director_id } }]);
  };

  const handleRemoveDirector = (directorId) => {
    setDirectors(prev => prev.filter(d => d.director_id !== directorId));
    setPendingOps(prev => [...prev, { type: 'remove_director', data: { director_id: directorId } }]);
  };

  const handleAssignActor = (actor, characterName) => {
    if (actors.some(a => a.actor_id === actor.actor_id)) return;
    setActors(prev => [...prev, { ...actor, character_name: characterName }]);
    setPendingOps(prev => [...prev, { type: 'add_actor', data: { actor_id: actor.actor_id, character_name: characterName } }]);
  };

  const handleRemoveActor = (actorId) => {
    setActors(prev => prev.filter(a => a.actor_id !== actorId));
    setPendingOps(prev => [...prev, { type: 'remove_actor', data: { actor_id: actorId } }]);
  };

  const content = (
    <>
      <motion.div className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.div
        className="fixed inset-0 z-[201] flex items-center justify-center p-4 pointer-events-none"
        initial={{ opacity: 0, scale: 0.92, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 20 }}
        transition={{ type: 'spring', damping: 22, stiffness: 300 }}
      >
        <div
          className="pointer-events-auto w-full max-w-xl bg-zinc-900 border border-white/10
                     rounded-2xl shadow-2xl overflow-hidden max-h-[92vh] flex flex-col"
          onClick={e => e.stopPropagation()}
        >
          {/* Gradient bar */}
          <div className="h-1 w-full bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 flex-shrink-0" />

          {/* Header */}
          <div className="flex items-center justify-between px-6 pt-5 flex-shrink-0">
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

          {/* Tabs (only show Cast tab when editing) */}
          {mode === 'edit' && (
            <div className="flex gap-1 px-6 pt-4 flex-shrink-0">
              {['info', 'cast'].map(t => (
                <button key={t} onClick={() => setTab(t)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                    tab === t
                      ? 'bg-amber-600/20 text-amber-400 border border-amber-500/40'
                      : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                  }`}>
                  {t === 'info' ? '📋 Thông tin' : '🎬 Cast'}
                </button>
              ))}
            </div>
          )}

          {/* ── TAB: INFO ── */}
          {tab === 'info' && (
            <form onSubmit={handleSubmit} className="px-6 pt-5 pb-6 space-y-5 overflow-y-auto flex-1">
              <FormField label="Tên phim" required>
                <input type="text" value={title} onChange={e => setTitle(e.target.value)}
                  placeholder="Ví dụ: The Matrix (1999)" className={inputCls} />
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Năm ra mắt">
                  <input type="number" value={releaseYear} onChange={e => setReleaseYear(e.target.value)}
                    placeholder="1999" min="1888" max="2100" className={inputCls} />
                </FormField>
                <FormField label="Quốc gia">
                  <CountryPicker value={country} onChange={setCountry} />
                </FormField>
              </div>

              <FormField label="Định dạng">
                <div className="flex gap-3">
                  <TypeToggle active={!isSerial} icon={<Film size={14} />} label="Phim lẻ"
                    onClick={() => { setIsSerial(false); setTotalEpisodes(''); }} />
                  <TypeToggle active={isSerial} icon={<Tv2 size={14} />} label="TV Series"
                    onClick={() => setIsSerial(true)} />
                </div>
                {isSerial && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                    className="mt-3">
                    <input type="number" value={totalEpisodes} onChange={e => setTotalEpisodes(e.target.value)}
                      placeholder="Tổng số tập" min="1" className={inputCls} />
                  </motion.div>
                )}
              </FormField>

              <FormField label={`Thể loại (${selectedGenres.length} đã chọn)`} required>
                <div className="flex flex-wrap gap-2">
                  {ALL_GENRES.map(genre => {
                    const active = selectedGenres.includes(genre);
                    return (
                      <button key={genre} type="button" onClick={() => toggleGenre(genre)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all
                          ${active
                            ? 'bg-amber-600/20 text-amber-400 border-amber-500/50'
                            : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/20'}`}>
                        {genre}
                      </button>
                    );
                  })}
                </div>
                {selectedGenres.length > 0 && (
                  <p className="text-xs text-gray-600 mt-2 font-mono">{selectedGenres.join('|')}</p>
                )}
              </FormField>

              <FormField label="Mô tả (tùy chọn)">
                <textarea value={description} onChange={e => setDescription(e.target.value)}
                  placeholder="Mô tả ngắn về nội dung phim..." rows={3}
                  className={inputCls + ' resize-none'} />
              </FormField>

              {/* Poster Upload */}
              <FormField label="Poster phim (tùy chọn)">
                <div className="flex items-start gap-4">
                  {/* Preview */}
                  <div className="relative w-24 h-36 rounded-xl overflow-hidden border border-white/10
                                  bg-zinc-800 flex items-center justify-center shrink-0 cursor-pointer"
                       onClick={() => fileInputRef.current?.click()}>
                    {posterPreview || existingPoster ? (
                      <img src={posterPreview || `http://localhost:8000${existingPoster}`}
                           alt="poster preview" className="w-full h-full object-cover" />
                    ) : (
                      <ImagePlus size={24} className="text-gray-600" />
                    )}
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center
                                    opacity-0 hover:opacity-100 transition">
                      <UploadCloud size={18} className="text-white" />
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex flex-col gap-2">
                    <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp"
                           className="hidden"
                           onChange={e => {
                             const f = e.target.files?.[0];
                             if (f) {
                               setPosterFile(f);
                               setPosterPreview(URL.createObjectURL(f));
                             }
                           }}
                    />
                    <button type="button" onClick={() => fileInputRef.current?.click()}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                                 bg-white/5 border border-white/10 text-gray-300
                                 hover:bg-white/10 hover:text-white transition">
                      <UploadCloud size={14} />
                      {posterFile ? posterFile.name : 'Chọn ảnh...'}
                    </button>
                    {posterPreview && (
                      <button type="button"
                        onClick={() => { setPosterFile(null); setPosterPreview(null); }}
                        className="text-xs text-red-400 hover:text-red-300 transition text-left">
                        Xóa ảnh đã chọn
                      </button>
                    )}
                    <p className="text-[11px] text-gray-600">JPG, PNG, WEBP · Tối đa 5MB</p>
                  </div>
                </div>
              </FormField>

              <AnimatePresence>
                {feedback && (
                  <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${
                      feedback.type === 'success'
                        ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                    {feedback.type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
                    {feedback.msg}
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="flex gap-3 pt-1">
                <button type="button" onClick={onClose}
                  className="flex-1 py-2.5 rounded-lg text-sm font-medium text-gray-400
                             bg-white/5 border border-white/10 hover:bg-white/10 transition">
                  Hủy
                </button>
                <button type="submit" disabled={loading}
                  className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white
                             bg-gradient-to-r from-amber-600 to-orange-600
                             hover:from-amber-500 hover:to-orange-500
                             disabled:opacity-50 shadow-lg shadow-amber-900/30 transition-all
                             flex items-center justify-center gap-2">
                  {loading && <Loader2 size={15} className="animate-spin" />}
                  {mode === 'create' ? 'Thêm phim' : 'Cập nhật'}
                </button>
              </div>
            </form>
          )}

          {/* ── TAB: CAST ── */}
          {tab === 'cast' && mode === 'edit' && (
            <div className="px-6 pt-4 pb-6 space-y-6 overflow-y-auto flex-1">
              {castLoading ? (
                <div className="flex items-center justify-center py-10 text-gray-500">
                  <Loader2 size={20} className="animate-spin mr-2" /> Đang tải cast...
                </div>
              ) : (
                <>
                  {/* Directors section */}
                  <CastSection
                    title="Đạo diễn"
                    icon={<Video size={14} className="text-blue-400" />}
                    color="blue"
                    items={directors}
                    searchPlaceholder="Tìm đạo diễn..."
                    searchEndpoint="/admin/directors/"
                    searchKey="directors"
                    idKey="director_id"
                    onAssign={handleAssignDirector}
                    onRemove={handleRemoveDirector}
                  />

                  {/* Actors section */}
                  <CastSection
                    title="Diễn viên"
                    icon={<UserCircle size={14} className="text-violet-400" />}
                    color="violet"
                    items={actors}
                    searchPlaceholder="Tìm diễn viên..."
                    searchEndpoint="/admin/actors/"
                    searchKey="actors"
                    idKey="actor_id"
                    onAssign={handleAssignActor}
                    onRemove={handleRemoveActor}
                    withCharacter
                  />
                </>
              )}

              {feedback && (
                <div className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${
                  feedback.type === 'error'
                    ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                    : 'bg-green-500/10 text-green-400 border border-green-500/20'}`}>
                  <AlertCircle size={15} />{feedback.msg}
                </div>
              )}

              <div className="flex gap-3 pt-1">
                <button type="button" onClick={onClose}
                  className="flex-1 py-2.5 rounded-lg text-sm font-medium text-gray-400
                             bg-white/5 border border-white/10 hover:bg-white/10 transition">
                  Hủy
                </button>
                <button type="button" onClick={handleSubmit} disabled={loading}
                  className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white
                             bg-gradient-to-r from-amber-600 to-orange-600
                             hover:from-amber-500 hover:to-orange-500
                             disabled:opacity-50 shadow-lg shadow-amber-900/30 transition-all
                             flex items-center justify-center gap-2">
                  {loading && <Loader2 size={15} className="animate-spin" />}
                  Lưu Cast & Cập nhật Phim
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </>
  );

  return createPortal(content, document.body);
}

// ── CastSection: search + assign + list ───────────────────────────────────
function CastSection({ title, icon, color, items, searchPlaceholder, searchEndpoint, searchKey,
  idKey, onAssign, onRemove, withCharacter }) {
  const [query, setQuery]         = useState('');
  const [results, setResults]     = useState([]);
  const [searching, setSearching] = useState(false);
  const [charName, setCharName]   = useState('');
  const debounceRef               = useRef(null);

  const colorMap = {
    blue:   { chip: 'bg-blue-500/10 text-blue-300 border-blue-500/20', btn: 'hover:bg-blue-500/10 text-blue-400' },
    violet: { chip: 'bg-violet-500/10 text-violet-300 border-violet-500/20', btn: 'hover:bg-violet-500/10 text-violet-400' },
  };
  const c = colorMap[color] || colorMap.blue;

  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setResults([]); return; }
    setSearching(true);
    try {
      const res = await api.get(searchEndpoint, { params: { q, limit: 8 } });
      setResults(res.data[searchKey] || []);
    } catch { setResults([]); }
    finally { setSearching(false); }
  }, [searchEndpoint, searchKey]);

  const handleInput = (v) => {
    setQuery(v);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(v), 300);
  };

  const assignedIds = new Set(items.map(i => i[idKey]));

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <span className="text-sm font-semibold text-white">{title}</span>
        <span className="text-xs text-gray-500 ml-auto">{items.length} người</span>
      </div>

      {/* Current cast chips */}
      {items.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {items.map(item => (
            <div key={item[idKey]}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs border ${c.chip}`}>
              <span className="font-medium">{item.name}</span>
              {item.character_name && <span className="opacity-50">· {item.character_name}</span>}
              <button onClick={() => onRemove(item[idKey])}
                className="ml-1 text-gray-500 hover:text-red-400 transition">
                <X size={11} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Search + assign */}
      <div className="relative">
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2
                        focus-within:border-amber-500/50 transition">
          {searching ? <Loader2 size={13} className="text-gray-400 animate-spin shrink-0" />
                     : <Search size={13} className="text-gray-500 shrink-0" />}
          <input
            value={query}
            onChange={e => handleInput(e.target.value)}
            placeholder={searchPlaceholder}
            className="bg-transparent outline-none text-sm text-white placeholder-gray-500 flex-1 min-w-0"
          />
        </div>

        {results.length > 0 && (
          <div className="absolute z-10 top-full left-0 right-0 mt-1
                          bg-zinc-800 border border-white/10 rounded-xl shadow-2xl overflow-hidden">
            {results.filter(r => !assignedIds.has(r[idKey])).map(item => (
              <div key={item[idKey]}
                className="px-3 py-2 hover:bg-white/5 transition">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-white font-medium">{item.name}</p>
                    {item.nationality && <p className="text-xs text-gray-500">{item.nationality}</p>}
                  </div>
                  {withCharacter ? (
                    <AssignWithChar item={item} onAssign={(charN) => {
                      onAssign(item, charN);
                      setQuery(''); setResults([]);
                    }} color={color} />
                  ) : (
                    <button
                      onClick={() => { onAssign(item); setQuery(''); setResults([]); }}
                      className={`flex items-center gap-1 text-xs px-2 py-1 rounded-lg ${c.btn} transition`}>
                      <Plus size={12} /> Thêm
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AssignWithChar({ item, onAssign, color }) {
  const [charName, setCharName] = useState('');
  const colorBtn = color === 'violet' ? 'hover:bg-violet-500/10 text-violet-400' : 'hover:bg-blue-500/10 text-blue-400';
  return (
    <div className="flex items-center gap-1.5">
      <input
        value={charName}
        onChange={e => setCharName(e.target.value)}
        placeholder="Tên nhân vật"
        className="bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-white
                   placeholder-gray-600 outline-none w-28 focus:border-amber-500/50 transition"
        onClick={e => e.stopPropagation()}
      />
      <button onClick={() => onAssign(charName)}
        className={`flex items-center gap-1 text-xs px-2 py-1 rounded-lg ${colorBtn} transition`}>
        <Plus size={12} /> Thêm
      </button>
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────
const inputCls = `w-full bg-white/5 border border-white/10 rounded-lg py-2.5 px-3
  text-white text-sm placeholder-gray-500 outline-none
  focus:border-amber-500 focus:ring-1 focus:ring-amber-500/40 transition`;

function FormField({ label, children, required }) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1.5">
        {label} {required && <span className="text-amber-500">*</span>}
      </label>
      {children}
    </div>
  );
}

function CountryPicker({ value, onChange }) {
  const [open, setOpen]     = useState(false);
  const [search, setSearch] = useState('');
  const ref                 = useRef(null);
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);
  const filtered = COUNTRIES.filter(c => c.toLowerCase().includes(search.toLowerCase()));
  return (
    <div ref={ref} className="relative">
      <button type="button" onClick={() => setOpen(o => !o)}
        className={`w-full flex items-center justify-between bg-white/5 border rounded-lg py-2.5 px-3 text-sm transition
          ${open ? 'border-amber-500 ring-1 ring-amber-500/40' : 'border-white/10 hover:border-white/20'}`}>
        <span className={value ? 'text-white' : 'text-gray-500'}>{value || '— Chọn quốc gia —'}</span>
        <div className="flex items-center gap-1">
          {value && (
            <span onClick={e => { e.stopPropagation(); onChange(''); }}
              className="text-gray-500 hover:text-white transition text-xs px-1 cursor-pointer">×</span>
          )}
          <ChevronDown size={14} className={`text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`} />
        </div>
      </button>
      {open && (
        <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
          style={{ transformOrigin: 'top' }}
          className="absolute z-50 mt-1 w-full bg-zinc-800 border border-white/10 rounded-xl shadow-2xl overflow-hidden">
          <div className="p-2 border-b border-white/5">
            <input autoFocus type="text" placeholder="Tìm quốc gia..." value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm
                         text-white placeholder-gray-500 outline-none focus:border-amber-500 transition" />
          </div>
          <div className="max-h-52 overflow-y-auto py-1 scrollbar-hide">
            {filtered.map(c => (
              <button key={c} type="button" onClick={() => { onChange(c); setOpen(false); setSearch(''); }}
                className={`w-full text-left px-3 py-2 text-sm transition
                  ${value === c ? 'bg-amber-600/20 text-amber-400' : 'text-gray-300 hover:bg-white/5 hover:text-white'}`}>
                {c}
              </button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

function TypeToggle({ active, icon, label, onClick }) {
  return (
    <button type="button" onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border transition-all
        ${active ? 'bg-amber-600/20 text-amber-400 border-amber-500/50' : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/20'}`}>
      {icon} {label}
    </button>
  );
}
