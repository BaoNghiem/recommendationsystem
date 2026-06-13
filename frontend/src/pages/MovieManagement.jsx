import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../api/axios';
import MovieFormModal from '../components/MovieFormModal';
import MovieDetailModal from '../components/MovieDetailModal';
import ProtectedRoute from '../components/ProtectedRoute';
import { fixTitle } from '../utils/formatTitle';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Plus, Search, ChevronLeft, ChevronRight, Pencil, Trash2,
  Film, Loader2, AlertCircle, CheckCircle, Database, Eye,
  Calendar, Globe, Tv2, Video, Upload, X, HardDrive
} from 'lucide-react';

// ── Main Page (wrapped in ProtectedRoute) ──────────────────────
export default function MovieManagement() {
  return (
    <ProtectedRoute requiredRole="admin">
      <MovieManagementInner />
    </ProtectedRoute>
  );
}

function MovieManagementInner() {
  const [movies, setMovies]           = useState([]);
  const [loading, setLoading]         = useState(true);
  const [page, setPage]               = useState(1);
  const [totalPages, setTotalPages]   = useState(1);
  const [total, setTotal]             = useState(0);
  const [search, setSearch]           = useState('');
  const [searchInput, setSearchInput] = useState('');
  const LIMIT = 15;

  // Modal state
  const [modalOpen, setModalOpen]         = useState(false);
  const [modalMode, setModalMode]         = useState('create');
  const [editingMovie, setEditingMovie]   = useState(null);

  // Detail modal
  const [detailMovie, setDetailMovie]     = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Delete confirm
  const [deleteTarget, setDeleteTarget]   = useState(null);
  const [deleting, setDeleting]           = useState(false);

  // Video upload
  const [videoTarget, setVideoTarget]     = useState(null); // { movie_id, title, total_episodes }

  // Toast
  const [toast, setToast] = useState(null);
  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  // ── Fetch Movies ───────────────────────────────────────────
  const fetchMovies = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, limit: LIMIT };
      if (search) params.q = search;
      const res = await api.get('/admin/movies/', { params });
      setMovies(res.data.movies);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      showToast(err.message, 'error');
    }
    setLoading(false);
  }, [page, search]);

  useEffect(() => { fetchMovies(); }, [fetchMovies]);

  // ── Search ─────────────────────────────────────────────────
  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  };
  const clearSearch = () => { setSearchInput(''); setSearch(''); setPage(1); };

  // ── Open Detail Modal ──────────────────────────────────────
  const openDetail = async (movie) => {
    // Dùng data đã có từ list (có thể thiếu avg_rating) → fetch detail đầy đủ
    setDetailMovie(movie);
    setDetailLoading(true);
    try {
      const res = await api.get(`/admin/movies/${movie.movie_id}`);
      setDetailMovie(res.data);
    } catch {
      // fallback: dùng data list
    } finally {
      setDetailLoading(false);
    }
  };

  // ── CRUD handlers ──────────────────────────────────────────
  const openCreate = () => {
    setEditingMovie(null);
    setModalMode('create');
    setModalOpen(true);
  };

  const openEdit = (movie, e) => {
    e.stopPropagation(); // không trigger openDetail
    setEditingMovie(movie);
    setModalMode('edit');
    setModalOpen(true);
  };

  const handleSave = async ({ title, genres_str, release_year, country, total_episodes, description, movie_id }) => {
    const payload = { title, genres_str, release_year, country, total_episodes, description };
    if (modalMode === 'create') {
      await api.post('/admin/movies/', payload);
      showToast(`Đã thêm phim "${title}"`);
    } else {
      await api.put(`/admin/movies/${movie_id}`, payload);
      showToast(`Đã cập nhật phim #${movie_id}`);
    }
    fetchMovies();
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await api.delete(`/admin/movies/${deleteTarget.movie_id}`);
      showToast(res.data.message);
      setDeleteTarget(null);
      fetchMovies();
    } catch (err) {
      showToast(err.message, 'error');
    }
    setDeleting(false);
  };

  // ── Pagination ─────────────────────────────────────────────
  const gotoPage = (p) => { if (p >= 1 && p <= totalPages) setPage(p); };
  const pageNums = [];
  const maxVisible = 5;
  let start = Math.max(1, page - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages, start + maxVisible - 1);
  if (end - start + 1 < maxVisible) start = Math.max(1, end - maxVisible + 1);
  for (let i = start; i <= end; i++) pageNums.push(i);

  // ── RENDER ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 pt-6 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-600 to-orange-600
                            flex items-center justify-center shadow-lg shadow-amber-900/30">
              <Database size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold">Quản lý Phim</h1>
              <p className="text-xs text-gray-500">{total.toLocaleString()} phim · Click vào hàng để xem chi tiết</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex items-center gap-2">
              <div className="relative">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="text"
                  placeholder="Tìm tên phim..."
                  value={searchInput}
                  onChange={e => setSearchInput(e.target.value)}
                  className="bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2
                             text-sm text-white placeholder-gray-500 outline-none w-52
                             focus:border-amber-500 focus:ring-1 focus:ring-amber-500/30 transition"
                />
              </div>
              {search && (
                <button type="button" onClick={clearSearch}
                  className="text-xs text-gray-400 hover:text-white transition">Xóa</button>
              )}
            </form>

            {/* Add button */}
            <button
              onClick={openCreate}
              className="flex items-center gap-2 bg-gradient-to-r from-amber-600 to-orange-600
                         hover:from-amber-500 hover:to-orange-500
                         text-white text-sm font-semibold px-4 py-2.5 rounded-lg
                         shadow-lg shadow-amber-900/30 active:scale-95 transition-all"
            >
              <Plus size={16} />
              Thêm phim
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 pb-8">
        <div className="bg-zinc-900/80 border border-white/5 rounded-xl overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-[70px_1fr_160px_100px_90px] gap-3 px-5 py-3
                          bg-white/5 text-xs text-gray-400 font-semibold uppercase tracking-wider">
            <span>ID</span>
            <span>Tên phim</span>
            <span>Thể loại</span>
            <span>Năm / Nước</span>
            <span className="text-center">Thao tác</span>
          </div>

          {/* Rows */}
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-500">
              <Loader2 size={24} className="animate-spin mr-3" />
              Đang tải...
            </div>
          ) : movies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-500">
              <Film size={40} className="mb-3 opacity-30" />
              <p>Không tìm thấy phim nào.</p>
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {movies.map((m, i) => (
                <motion.div
                  key={m.movie_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.02 }}
                  onClick={() => openDetail(m)}
                  className="grid grid-cols-[70px_1fr_160px_100px_90px] gap-3 px-5 py-3.5
                             items-center hover:bg-white/[0.04] transition group cursor-pointer"
                >
                  {/* ID */}
                  <span className="text-sm text-gray-500 font-mono">#{m.movie_id}</span>

                  {/* Title + meta chips */}
                  <div className="min-w-0">
                    <p className="text-sm text-white font-medium truncate">{fixTitle(m.title)}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {m.release_year && (
                        <span className="flex items-center gap-0.5 text-[10px] text-gray-500">
                          <Calendar size={9} />{m.release_year}
                        </span>
                      )}
                      {m.country && (
                        <span className="flex items-center gap-0.5 text-[10px] text-gray-500">
                          <Globe size={9} />{m.country}
                        </span>
                      )}
                      {m.total_episodes && (
                        <span className="flex items-center gap-0.5 text-[10px] text-blue-400">
                          <Tv2 size={9} />{m.total_episodes} tập
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Genres */}
                  <div className="flex flex-wrap gap-1">
                    {(m.genres_orig || '').split('|').filter(Boolean).slice(0, 3).map(g => (
                      <span key={g}
                        className="px-1.5 py-0.5 rounded text-[10px] font-medium
                                   bg-white/5 text-gray-400 border border-white/5">
                        {g.trim()}
                      </span>
                    ))}
                    {(m.genres_orig || '').split('|').filter(Boolean).length > 3 && (
                      <span className="text-[10px] text-gray-600">
                        +{(m.genres_orig || '').split('|').filter(Boolean).length - 3}
                      </span>
                    )}
                  </div>

                  {/* Year / Country */}
                  <div className="text-xs text-gray-500 space-y-0.5">
                    {m.release_year && <p>{m.release_year}</p>}
                    {m.country && <p className="truncate">{m.country}</p>}
                    {!m.release_year && !m.country && <p className="text-gray-700 italic">—</p>}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-center gap-1
                                  opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={(e) => { e.stopPropagation(); openDetail(m); }}
                      className="p-2 rounded-lg hover:bg-blue-500/10 text-blue-400 transition"
                      title="Xem chi tiết"
                    >
                      <Eye size={14} />
                    </button>
                    <button
                      onClick={(e) => openEdit(m, e)}
                      className="p-2 rounded-lg hover:bg-amber-500/10 text-amber-400 transition"
                      title="Sửa"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setVideoTarget(m); }}
                      className="p-2 rounded-lg hover:bg-green-500/10 text-green-400 transition"
                      title="Upload Video"
                    >
                      <Video size={14} />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setDeleteTarget(m); }}
                      className="p-2 rounded-lg hover:bg-red-500/10 text-red-400 transition"
                      title="Xóa"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 bg-white/[0.02] border-t border-white/5">
              <p className="text-xs text-gray-500">
                Trang {page}/{totalPages} · {total.toLocaleString()} phim
              </p>
              <div className="flex items-center gap-1">
                <button onClick={() => gotoPage(page - 1)} disabled={page === 1}
                  className="p-1.5 rounded-lg hover:bg-white/10 disabled:opacity-20 transition">
                  <ChevronLeft size={16} />
                </button>
                {pageNums.map(n => (
                  <button key={n} onClick={() => gotoPage(n)}
                    className={`w-8 h-8 rounded-lg text-xs font-medium transition
                      ${n === page
                        ? 'bg-amber-600 text-white shadow shadow-amber-900/30'
                        : 'hover:bg-white/10 text-gray-400'}`}>
                    {n}
                  </button>
                ))}
                <button onClick={() => gotoPage(page + 1)} disabled={page === totalPages}
                  className="p-1.5 rounded-lg hover:bg-white/10 disabled:opacity-20 transition">
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Movie Detail Modal ──────────────────────────────────── */}
      <AnimatePresence>
        {detailMovie && !modalOpen && !deleteTarget && !videoTarget && (
          <MovieDetailModal
            movie={detailMovie}
            onClose={() => setDetailMovie(null)}
          />
        )}
      </AnimatePresence>

      {/* ── Video Upload Modal ────────────────────────────────── */}
      <AnimatePresence>
        {videoTarget && (
          <VideoUploadModal
            movie={videoTarget}
            onClose={() => setVideoTarget(null)}
            onSuccess={(msg) => { showToast(msg); setVideoTarget(null); }}
          />
        )}
      </AnimatePresence>

      {/* ── Movie Form Modal ──────────────────────────────────── */}
      <AnimatePresence>
        {modalOpen && (
          <MovieFormModal
            mode={modalMode}
            movie={editingMovie}
            onClose={() => setModalOpen(false)}
            onSave={handleSave}
          />
        )}
      </AnimatePresence>

      {/* ── Delete Confirmation ───────────────────────────────── */}
      <AnimatePresence>
        {deleteTarget && (
          <>
            <motion.div
              className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => !deleting && setDeleteTarget(null)}
            />
            <motion.div
              className="fixed inset-0 z-[201] flex items-center justify-center p-4 pointer-events-none"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <div className="pointer-events-auto bg-zinc-900 border border-white/10
                              rounded-2xl shadow-2xl p-6 max-w-sm w-full text-center"
                   onClick={e => e.stopPropagation()}>
                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-500/10
                                flex items-center justify-center">
                  <Trash2 size={24} className="text-red-400" />
                </div>
                <h3 className="text-lg font-bold mb-1">Xác nhận xóa</h3>
                <p className="text-sm text-gray-400 mb-1">Bạn có chắc muốn xóa phim:</p>
                <p className="text-sm text-white font-semibold mb-1">"{fixTitle(deleteTarget.title)}"</p>
                <p className="text-xs text-gray-500 mb-5">
                  ID #{deleteTarget.movie_id} — Tất cả ratings liên quan cũng sẽ bị xóa.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setDeleteTarget(null)} disabled={deleting}
                    className="flex-1 py-2.5 rounded-lg text-sm font-medium text-gray-400
                               bg-white/5 border border-white/10 hover:bg-white/10 transition"
                  >Hủy</button>
                  <button
                    onClick={confirmDelete} disabled={deleting}
                    className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white
                               bg-red-600 hover:bg-red-500 disabled:opacity-50 transition-all
                               flex items-center justify-center gap-2"
                  >
                    {deleting && <Loader2 size={14} className="animate-spin" />}
                    Xóa
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ── Toast ─────────────────────────────────────────────── */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 50, x: '-50%' }}
            className={`fixed bottom-8 left-1/2 z-[300] px-6 py-3 rounded-xl shadow-2xl
                        flex items-center gap-2 font-medium text-sm
                        ${toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}
          >
            {toast.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


// ══════════════════════════════════════════════════════════════
// VIDEO UPLOAD MODAL
// ══════════════════════════════════════════════════════════════
function VideoUploadModal({ movie, onClose, onSuccess }) {
  const fileRef      = useRef(null);
  const isSeries     = Boolean(movie?.total_episodes);

  const [file,         setFile]         = useState(null);
  const [episodeNo,    setEpisodeNo]    = useState('');
  const [seasonNo,     setSeasonNo]     = useState('1');
  const [episodeTitle, setEpisodeTitle] = useState('');
  const [uploading,    setUploading]    = useState(false);
  const [progress,     setProgress]     = useState(0);
  const [existingVids, setExistingVids] = useState([]);
  const [deleting,     setDeleting]     = useState(null);

  const [editingEp,    setEditingEp]    = useState(null);
  const [editForm,     setEditForm]     = useState({ episode_no: '', episode_title: '' });

  // Fetch existing videos
  useEffect(() => {
    api.get(`/videos/${movie.movie_id}/info`)
      .then(res => setExistingVids(res.data.episodes || []))
      .catch(() => {});
  }, [movie.movie_id]);

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    if (isSeries && !episodeNo) {
      alert('Vui lòng nhập số tập.');
      return;
    }
    if (isSeries && parseInt(episodeNo) <= 0) {
      alert('Số tập phải lớn hơn 0.');
      return;
    }
    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams({ season_no: seasonNo });
    if (isSeries && episodeNo) params.append('episode_no', episodeNo);
    if (episodeTitle) params.append('episode_title', episodeTitle);

    try {
      await api.post(
        `/admin/movies/${movie.movie_id}/video?${params.toString()}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            if (e.total) setProgress(Math.round((e.loaded / e.total) * 100));
          },
          timeout: 0, // no timeout for large files
        }
      );
      // Refresh list
      const res = await api.get(`/videos/${movie.movie_id}/info`);
      setExistingVids(res.data.episodes || []);
      setFile(null);
      setEpisodeNo('');
      setEpisodeTitle('');
      setProgress(0);
      if (fileRef.current) fileRef.current.value = '';
      onSuccess(`Upload video thành công${isSeries ? ` (Tập ${episodeNo})` : ''}!`);
    } catch (err) {
      alert(`Lỗi upload: ${err.message}`);
    }
    setUploading(false);
  };

  const handleDelete = async (ep) => {
    if (!confirm(`Xóa video${ep.episode_no ? ` tập ${ep.episode_no}` : ''}?`)) return;
    setDeleting(ep.id);
    const params = new URLSearchParams({ season_no: ep.season_no ?? 1 });
    if (ep.episode_no != null) params.append('episode_no', ep.episode_no);
    try {
      await api.delete(`/admin/movies/${movie.movie_id}/video?${params.toString()}`);
      setExistingVids(prev => prev.filter(v => v.id !== ep.id));
    } catch (err) {
      alert(`Lỗi xóa: ${err.message}`);
    }
    setDeleting(null);
  };

  const startEdit = (ep) => {
    setEditingEp(ep.id);
    setEditForm({ episode_no: ep.episode_no || '', episode_title: ep.episode_title || '' });
  };

  const cancelEdit = () => {
    setEditingEp(null);
  };

  const handleUpdate = async (ep) => {
    try {
      const payload = {};
      if (editForm.episode_no !== '') {
        const epNo = parseInt(editForm.episode_no);
        if (epNo <= 0) {
          alert('Số tập phải lớn hơn 0.');
          return;
        }
        payload.episode_no = epNo;
      }
      payload.episode_title = editForm.episode_title;
      
      await api.put(`/admin/movies/${movie.movie_id}/video/${ep.id}`, payload);
      setExistingVids(prev => {
        const updated = prev.map(v => v.id === ep.id ? { ...v, episode_no: payload.episode_no, episode_title: payload.episode_title } : v);
        return updated.sort((a, b) => (a.season_no - b.season_no) || ((a.episode_no || 0) - (b.episode_no || 0)));
      });
      setEditingEp(null);
      onSuccess("Cập nhật thông tin tập thành công!");
    } catch (err) {
      alert(`Lỗi cập nhật: ${err.message}`);
    }
  };

  const fileSizeMB = file ? (file.size / (1024 * 1024)).toFixed(1) : null;

  return (
    <>
      {/* Backdrop */}
      <motion.div
        className="fixed inset-0 z-[200] bg-black/85 backdrop-blur-sm"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={() => !uploading && onClose()}
      />

      {/* Modal */}
      <motion.div
        className="fixed inset-0 z-[201] flex items-center justify-center p-4 pointer-events-none"
        initial={{ opacity: 0, scale: 0.92, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 20 }}
        transition={{ type: 'spring', damping: 24, stiffness: 280 }}
      >
        <div
          className="pointer-events-auto w-full max-w-lg bg-zinc-900 border border-white/10
                     rounded-2xl shadow-2xl overflow-hidden"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 pt-5 pb-4 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-green-500/10 border border-green-500/20
                              flex items-center justify-center">
                <Video size={18} className="text-green-400" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Upload Video</h2>
                <p className="text-xs text-gray-500 truncate max-w-[260px]">{fixTitle(movie.title)}</p>
              </div>
            </div>
            <button onClick={onClose} disabled={uploading}
              className="text-gray-500 hover:text-white transition p-1">
              <X size={18} />
            </button>
          </div>

          <div className="px-6 py-5 space-y-5">
            {/* Existing videos */}
            {existingVids.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Video hiện có</p>
                <div className="space-y-2">
                  {existingVids.map(ep => (
                    <div key={ep.id}
                      className="flex items-center justify-between bg-white/5 border border-white/8
                                 rounded-xl px-3 py-2.5 transition-all">
                      {editingEp === ep.id ? (
                        <div className="flex-1 flex gap-2 items-center">
                          {isSeries && (
                            <input 
                              type="number" min="1" 
                              value={editForm.episode_no} 
                              onChange={(e) => setEditForm({...editForm, episode_no: e.target.value})}
                              className="w-16 bg-white/10 border border-white/20 rounded px-2 py-1 text-xs text-white outline-none focus:border-amber-500"
                              placeholder="Tập"
                            />
                          )}
                          <input 
                            type="text" 
                            value={editForm.episode_title} 
                            onChange={(e) => setEditForm({...editForm, episode_title: e.target.value})}
                            className="flex-1 bg-white/10 border border-white/20 rounded px-2 py-1 text-xs text-white outline-none focus:border-amber-500"
                            placeholder="Tiêu đề tập"
                          />
                          <div className="flex gap-1 ml-2">
                            <button onClick={() => handleUpdate(ep)} className="p-1.5 text-green-400 hover:bg-green-400/10 rounded transition">
                               <CheckCircle size={14} />
                            </button>
                            <button onClick={cancelEdit} className="p-1.5 text-gray-400 hover:bg-white/10 rounded transition">
                               <X size={14} />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center gap-2.5">
                            <CheckCircle size={14} className="text-green-400 flex-shrink-0" />
                            <div>
                              <p className="text-sm text-white font-medium">
                                {ep.episode_no != null ? `Tập ${ep.episode_no}` : 'Phim lẻ'}
                                {ep.episode_title && (
                                  <span className="text-gray-400 font-normal ml-1.5">— {ep.episode_title}</span>
                                )}
                              </p>
                              <p className="text-[10px] text-gray-600 flex items-center gap-1 mt-0.5">
                                <HardDrive size={9} /> {ep.file_size_mb} MB · {ep.video_quality}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => startEdit(ep)}
                              disabled={deleting === ep.id}
                              className="text-amber-400/70 hover:text-amber-400 hover:bg-amber-400/10 rounded transition p-1.5"
                              title="Sửa thông tin"
                            >
                              <Pencil size={14} />
                            </button>
                            <button
                              onClick={() => handleDelete(ep)}
                              disabled={deleting === ep.id}
                              className="text-red-400/70 hover:text-red-400 hover:bg-red-400/10 rounded transition p-1.5"
                              title="Xóa video này"
                            >
                              {deleting === ep.id
                                ? <Loader2 size={14} className="animate-spin" />
                                : <Trash2 size={14} />}
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Phim bộ: episode fields */}
            {isSeries && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Số tập *</label>
                  <input
                    type="number" min="1" max={movie.total_episodes}
                    value={episodeNo}
                    onChange={e => setEpisodeNo(e.target.value)}
                    placeholder="VD: 1"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2
                               text-sm text-white placeholder-gray-600 outline-none
                               focus:border-green-500 focus:ring-1 focus:ring-green-500/20 transition"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Số mùa</label>
                  <input
                    type="number" min="1" value={seasonNo}
                    onChange={e => setSeasonNo(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2
                               text-sm text-white outline-none
                               focus:border-green-500 focus:ring-1 focus:ring-green-500/20 transition"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-xs text-gray-400 mb-1 block">Tên tập (tuỳ chọn)</label>
                  <input
                    type="text" value={episodeTitle}
                    onChange={e => setEpisodeTitle(e.target.value)}
                    placeholder="VD: Tập 1: Khởi đầu"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2
                               text-sm text-white placeholder-gray-600 outline-none
                               focus:border-green-500 focus:ring-1 focus:ring-green-500/20 transition"
                  />
                </div>
              </div>
            )}

            {/* File picker */}
            <div>
              <label className="text-xs text-gray-400 mb-1 block">
                File video (MP4, WebM, MKV, AVI, MOV — tối đa 2GB)
              </label>
              <div
                onClick={() => !uploading && fileRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition
                  ${file
                    ? 'border-green-500/40 bg-green-500/5'
                    : 'border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/5'
                  }`}
              >
                <input
                  ref={fileRef} type="file"
                  accept=".mp4,.webm,.mkv,.avi,.mov,video/*"
                  className="hidden"
                  onChange={handleFileChange}
                  disabled={uploading}
                />
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <Film size={20} className="text-green-400 flex-shrink-0" />
                    <div className="text-left">
                      <p className="text-sm text-white font-medium truncate max-w-[260px]">{file.name}</p>
                      <p className="text-xs text-gray-500">{fileSizeMB} MB</p>
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-500">
                    <Upload size={24} className="mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Nhấn để chọn file video</p>
                    <p className="text-xs mt-1 text-gray-600">mp4 · webm · mkv · avi · mov</p>
                  </div>
                )}
              </div>
            </div>

            {/* Progress bar */}
            {uploading && (
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1.5">
                  <span>Đang upload...</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ ease: 'linear' }}
                  />
                </div>
                <p className="text-xs text-gray-600 mt-1.5 text-center">
                  File lớn có thể mất vài phút — vui lòng không đóng trình duyệt
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 pb-5 flex gap-3">
            <button
              onClick={onClose} disabled={uploading}
              className="flex-1 py-2.5 rounded-xl text-sm font-medium text-gray-400
                         bg-white/5 border border-white/10 hover:bg-white/10 transition disabled:opacity-40"
            >
              Hủy
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white
                         bg-gradient-to-r from-green-600 to-emerald-600
                         hover:from-green-500 hover:to-emerald-500
                         disabled:opacity-40 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2 transition-all shadow-lg"
            >
              {uploading
                ? <><Loader2 size={15} className="animate-spin" /> Đang upload {progress}%</>
                : <><Upload size={15} /> Upload Video</>
              }
            </button>
          </div>
        </div>
      </motion.div>
    </>
  );
}
