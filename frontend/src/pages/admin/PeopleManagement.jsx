import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axios';
import ProtectedRoute from '../../components/ProtectedRoute';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Video, UserCircle, Plus, Pencil, Trash2, Search,
  ChevronLeft, ChevronRight, Loader2, CheckCircle, AlertCircle, X
} from 'lucide-react';

export default function PeopleManagement() {
  return (
    <ProtectedRoute requiredRole="admin">
      <PeopleManagementInner />
    </ProtectedRoute>
  );
}

const inputCls = `w-full bg-white/5 border border-white/10 rounded-lg py-2 px-3
  text-white text-sm placeholder-gray-500 outline-none
  focus:border-violet-500 focus:ring-1 focus:ring-violet-500/40 transition`;

function PeopleManagementInner() {
  const [tab, setTab] = useState('directors'); // 'directors' | 'actors'

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}
      <div className="max-w-6xl mx-auto px-4 lg:px-8 pt-6 pb-4">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-purple-600
                          flex items-center justify-center shadow-lg shadow-violet-900/30">
            <UserCircle size={22} />
          </div>
          <div>
            <h1 className="text-xl font-bold">Quản lý Đạo diễn & Diễn viên</h1>
            <p className="text-xs text-gray-500">Thêm, sửa, xóa người tham gia phim</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-2">
          <TabBtn active={tab === 'directors'} onClick={() => setTab('directors')}
            icon={<Video size={14} />} label="Đạo diễn" />
          <TabBtn active={tab === 'actors'} onClick={() => setTab('actors')}
            icon={<UserCircle size={14} />} label="Diễn viên" />
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 lg:px-8 pb-8">
        <AnimatePresence mode="wait">
          {tab === 'directors' ? (
            <motion.div key="directors"
              initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
              <PeopleTable
                type="directors"
                endpoint="/admin/directors/"
                dataKey="directors"
                idKey="director_id"
                singularLabel="đạo diễn"
                color="blue"
              />
            </motion.div>
          ) : (
            <motion.div key="actors"
              initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
              <PeopleTable
                type="actors"
                endpoint="/admin/actors/"
                dataKey="actors"
                idKey="actor_id"
                singularLabel="diễn viên"
                color="violet"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ── Generic table for directors OR actors ─────────────────────────────────
function PeopleTable({ endpoint, dataKey, idKey, singularLabel, color }) {
  const [items, setItems]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [page, setPage]           = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal]         = useState(0);
  const [search, setSearch]       = useState('');
  const [searchInput, setSearchInput] = useState('');
  const LIMIT = 20;

  const [formOpen, setFormOpen]   = useState(false);
  const [editing, setEditing]     = useState(null); // null = create
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting]   = useState(false);
  const [toast, setToast]         = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(endpoint, { params: { page, limit: LIMIT, q: search } });
      setItems(res.data[dataKey] || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) { showToast(err.message, 'error'); }
    setLoading(false);
  }, [endpoint, dataKey, page, search]);

  useEffect(() => { fetchItems(); }, [fetchItems]);

  const handleSearch = (e) => { e.preventDefault(); setPage(1); setSearch(searchInput.trim()); };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`${endpoint}${deleteTarget[idKey]}`);
      showToast(`Đã xóa ${singularLabel} "${deleteTarget.name}".`);
      setDeleteTarget(null);
      fetchItems();
    } catch (err) { showToast(err.message, 'error'); }
    setDeleting(false);
  };

  const colorMap = {
    blue:   { badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',   accent: 'from-blue-600 to-blue-700',   ring: 'focus:border-blue-500' },
    violet: { badge: 'bg-violet-500/10 text-violet-400 border-violet-500/20', accent: 'from-violet-600 to-purple-600', ring: 'focus:border-violet-500' },
  };
  const c = colorMap[color] || colorMap.violet;

  return (
    <>
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4 items-start sm:items-center justify-between">
        <p className="text-sm text-gray-500">{total.toLocaleString()} {singularLabel}</p>
        <div className="flex items-center gap-3">
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input value={searchInput} onChange={e => setSearchInput(e.target.value)}
                placeholder={`Tìm ${singularLabel}...`}
                className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-2
                           text-sm text-white placeholder-gray-500 outline-none w-48
                           focus:border-violet-500 transition" />
            </div>
            {search && (
              <button type="button" onClick={() => { setSearchInput(''); setSearch(''); setPage(1); }}
                className="text-xs text-gray-400 hover:text-white transition">Xóa</button>
            )}
          </form>
          <button onClick={() => { setEditing(null); setFormOpen(true); }}
            className={`flex items-center gap-2 bg-gradient-to-r ${c.accent}
                        text-white text-sm font-semibold px-4 py-2 rounded-lg
                        shadow-lg active:scale-95 transition-all hover:opacity-90`}>
            <Plus size={15} /> Thêm
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-zinc-900/80 border border-white/5 rounded-xl overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[60px_1fr_100px_120px_100px] gap-3 px-5 py-3
                        bg-white/5 text-xs text-gray-400 font-semibold uppercase tracking-wider">
          <span>ID</span><span>Tên</span><span>Năm sinh</span><span>Quốc tịch</span>
          <span className="text-center">Thao tác</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-gray-500">
            <Loader2 size={22} className="animate-spin mr-2" /> Đang tải...
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-600">
            <UserCircle size={36} className="mb-2 opacity-30" />
            <p>Không có {singularLabel} nào.</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {items.map((item, i) => (
              <motion.div key={item[idKey]}
                initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.02 }}
                className="grid grid-cols-[60px_1fr_100px_120px_100px] gap-3 px-5 py-3.5
                           items-center hover:bg-white/[0.03] transition group">
                <span className="text-xs text-gray-600 font-mono">#{item[idKey]}</span>
                <div>
                  <p className="text-sm font-medium text-white">{item.name}</p>
                </div>
                <span className="text-sm text-gray-400">{item.birth_year || '—'}</span>
                <span className="text-sm text-gray-400 truncate">{item.nationality || '—'}</span>
                <div className="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition">
                  <button onClick={() => { setEditing(item); setFormOpen(true); }}
                    className="p-2 rounded-lg hover:bg-amber-500/10 text-amber-400 transition">
                    <Pencil size={13} />
                  </button>
                  <button onClick={() => setDeleteTarget(item)}
                    className="p-2 rounded-lg hover:bg-red-500/10 text-red-400 transition">
                    <Trash2 size={13} />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 bg-white/[0.02] border-t border-white/5">
            <p className="text-xs text-gray-500">Trang {page}/{totalPages}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="p-1.5 rounded-lg hover:bg-white/10 disabled:opacity-20 transition">
                <ChevronLeft size={15} />
              </button>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                className="p-1.5 rounded-lg hover:bg-white/10 disabled:opacity-20 transition">
                <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Form Modal */}
      <AnimatePresence>
        {formOpen && (
          <PersonFormModal
            item={editing}
            singularLabel={singularLabel}
            endpoint={endpoint}
            idKey={idKey}
            color={color}
            onClose={() => setFormOpen(false)}
            onSaved={() => { setFormOpen(false); fetchItems(); showToast(editing ? `Đã cập nhật.` : `Đã thêm ${singularLabel}.`); }}
          />
        )}
      </AnimatePresence>

      {/* Delete confirm */}
      <AnimatePresence>
        {deleteTarget && (
          <>
            <motion.div className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => !deleting && setDeleteTarget(null)} />
            <motion.div className="fixed inset-0 z-[201] flex items-center justify-center p-4 pointer-events-none"
              initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}>
              <div className="pointer-events-auto bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl p-6 max-w-sm w-full text-center">
                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
                  <Trash2 size={22} className="text-red-400" />
                </div>
                <h3 className="font-bold text-lg mb-1">Xác nhận xóa</h3>
                <p className="text-sm text-gray-400 mb-4">
                  Xóa {singularLabel} <span className="text-white font-semibold">"{deleteTarget.name}"</span>?
                  <br /><span className="text-xs text-gray-600">Liên kết với phim sẽ bị xóa theo.</span>
                </p>
                <div className="flex gap-3">
                  <button onClick={() => setDeleteTarget(null)} disabled={deleting}
                    className="flex-1 py-2.5 rounded-lg text-sm text-gray-400 bg-white/5 border border-white/10 hover:bg-white/10 transition">
                    Hủy
                  </button>
                  <button onClick={confirmDelete} disabled={deleting}
                    className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50 flex items-center justify-center gap-2 transition">
                    {deleting && <Loader2 size={13} className="animate-spin" />} Xóa
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div initial={{ opacity: 0, y: 50, x: '-50%' }} animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 50, x: '-50%' }}
            className={`fixed bottom-8 left-1/2 z-[300] px-6 py-3 rounded-xl shadow-2xl flex items-center gap-2 font-medium text-sm
              ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'} text-white`}>
            {toast.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// ── PersonFormModal (create/edit director or actor) ───────────────────────
function PersonFormModal({ item, singularLabel, endpoint, idKey, color, onClose, onSaved }) {
  const [name, setName]               = useState(item?.name || '');
  const [birthYear, setBirthYear]     = useState(item?.birth_year ? String(item.birth_year) : '');
  const [nationality, setNationality] = useState(item?.nationality || '');
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return setError('Tên không được để trống.');
    setLoading(true); setError('');
    try {
      const payload = {
        name: name.trim(),
        birth_year: birthYear ? parseInt(birthYear) : null,
        nationality: nationality.trim() || null,
      };
      if (item) {
        await api.put(`${endpoint}${item[idKey]}`, payload);
      } else {
        await api.post(endpoint, payload);
      }
      onSaved();
    } catch (err) { setError(err.message || 'Đã xảy ra lỗi.'); }
    setLoading(false);
  };

  const accentColor = color === 'blue' ? 'from-blue-600 to-blue-700' : 'from-violet-600 to-purple-600';

  return (
    <>
      <motion.div className="fixed inset-0 z-[210] bg-black/80 backdrop-blur-sm"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose} />
      <motion.div className="fixed inset-0 z-[211] flex items-center justify-center p-4 pointer-events-none"
        initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.92 }}>
        <div className="pointer-events-auto w-full max-w-md bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
          onClick={e => e.stopPropagation()}>
          <div className={`h-1 w-full bg-gradient-to-r ${accentColor}`} />
          <div className="px-6 pt-5 pb-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-bold text-white">
                {item ? `Sửa ${singularLabel}` : `Thêm ${singularLabel} mới`}
              </h3>
              <button onClick={onClose} className="text-gray-400 hover:text-white transition">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Họ và tên <span className="text-red-400">*</span></label>
                <input value={name} onChange={e => setName(e.target.value)}
                  placeholder="Ví dụ: Christopher Nolan" className={inputCls} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Năm sinh</label>
                  <input type="number" value={birthYear} onChange={e => setBirthYear(e.target.value)}
                    placeholder="1970" min="1900" max="2010" className={inputCls} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Quốc tịch</label>
                  <input value={nationality} onChange={e => setNationality(e.target.value)}
                    placeholder="Mỹ, Anh..." className={inputCls} />
                </div>
              </div>
              {error && (
                <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  {error}
                </p>
              )}
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={onClose}
                  className="flex-1 py-2.5 rounded-lg text-sm text-gray-400 bg-white/5 border border-white/10 hover:bg-white/10 transition">
                  Hủy
                </button>
                <button type="submit" disabled={loading}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-semibold text-white bg-gradient-to-r ${accentColor}
                              disabled:opacity-50 flex items-center justify-center gap-2 transition hover:opacity-90`}>
                  {loading && <Loader2 size={14} className="animate-spin" />}
                  {item ? 'Cập nhật' : 'Thêm mới'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </motion.div>
    </>
  );
}

function TabBtn({ active, onClick, icon, label }) {
  return (
    <button onClick={onClick}
      className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-medium border transition-all
        ${active
          ? 'bg-violet-600/20 text-violet-300 border-violet-500/40 shadow shadow-violet-900/20'
          : 'bg-white/5 text-gray-500 border-white/10 hover:text-gray-300 hover:bg-white/8'}`}>
      {icon}{label}
    </button>
  );
}
