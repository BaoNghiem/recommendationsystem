import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/axios';
import ProtectedRoute from '../../components/ProtectedRoute';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Search, ChevronLeft, ChevronRight, Users, Loader2, AlertCircle,
  CheckCircle, ShieldCheck, ShieldOff, Lock, Unlock, Trash2, Filter,
  UserCircle, Crown, Clock, Mail
} from 'lucide-react';

// ── Main export (wrapped in ProtectedRoute) ─────────────────
export default function UserManagement() {
  return (
    <ProtectedRoute requiredRole="admin">
      <UserManagementInner />
    </ProtectedRoute>
  );
}

function UserManagementInner() {
  const [users, setUsers]             = useState([]);
  const [loading, setLoading]         = useState(true);
  const [page, setPage]               = useState(1);
  const [totalPages, setTotalPages]   = useState(1);
  const [total, setTotal]             = useState(0);
  const [search, setSearch]           = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [filterType, setFilterType]   = useState('');   // '' | 'legacy' | 'real'
  const LIMIT = 20;

  // Delete confirm
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting]         = useState(false);

  // Toast
  const [toast, setToast] = useState(null);
  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // ── Fetch Users ───────────────────────────────────────────
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, limit: LIMIT };
      if (search) params.q = search;
      if (filterType) params.account_type = filterType;
      const res = await api.get('/admin/users/', { params });
      setUsers(res.data.users);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      console.error('[Admin Users]', err.message);
      showToast(err.message, 'error');
    }
    setLoading(false);
  }, [page, search, filterType]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  // ── Search ────────────────────────────────────────────────
  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  };
  const clearSearch = () => { setSearchInput(''); setSearch(''); setPage(1); };

  // ── Filter change ─────────────────────────────────────────
  const handleFilter = (type) => {
    setFilterType(prev => prev === type ? '' : type);
    setPage(1);
  };

  // ── Toggle role ───────────────────────────────────────────
  const toggleRole = async (userId, currentRole) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    try {
      const res = await api.patch(`/admin/users/${userId}/role`, { role: newRole });
      showToast(res.data.message);
      fetchUsers();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // ── Toggle active ─────────────────────────────────────────
  const toggleActive = async (userId, currentActive) => {
    try {
      const res = await api.patch(`/admin/users/${userId}/active`, { is_active: !currentActive });
      showToast(res.data.message);
      fetchUsers();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // ── Delete user ───────────────────────────────────────────
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await api.delete(`/admin/users/${deleteTarget.user_id}`);
      showToast(res.data.message);
      setDeleteTarget(null);
      fetchUsers();
    } catch (err) {
      showToast(err.message, 'error');
    }
    setDeleting(false);
  };

  // ── Pagination ────────────────────────────────────────────
  const gotoPage = (p) => { if (p >= 1 && p <= totalPages) setPage(p); };

  const pageNums = [];
  const maxVisible = 5;
  let start = Math.max(1, page - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages, start + maxVisible - 1);
  if (end - start + 1 < maxVisible) start = Math.max(1, end - maxVisible + 1);
  for (let i = start; i <= end; i++) pageNums.push(i);

  // ── Helper: badge styles ──────────────────────────────────
  const roleBadge = (role) => role === 'admin'
    ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    : 'bg-blue-500/15 text-blue-400 border-blue-500/20';

  const typeBadge = (type) => type === 'real'
    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20'
    : 'bg-gray-500/10 text-gray-500 border-gray-500/15';

  const activeDot = (active) => active
    ? 'bg-emerald-400 shadow-emerald-400/40'
    : 'bg-red-400 shadow-red-400/40';

  // ── Filter stats ──────────────────────────────────────────
  const filterLabel = filterType === 'legacy' ? 'Legacy Users'
    : filterType === 'real' ? 'New Users' : 'Tất cả';

  // ── RENDER ────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 pt-6 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600
                            flex items-center justify-center shadow-lg shadow-violet-900/30">
              <Users size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold">Quản lý Người dùng</h1>
              <p className="text-xs text-gray-500">
                {total.toLocaleString()} tài khoản · Đang xem: {filterLabel}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Filter buttons */}
            <div className="flex items-center gap-1.5 mr-2">
              <Filter size={13} className="text-gray-500" />
              <button
                onClick={() => handleFilter('legacy')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                  ${filterType === 'legacy'
                    ? 'bg-gray-500/20 text-gray-300 border-gray-500/40'
                    : 'bg-white/5 text-gray-500 border-white/5 hover:border-white/15 hover:text-gray-400'}`}
              >
                <Clock size={11} className="inline mr-1 -mt-0.5" />
                Legacy
              </button>
              <button
                onClick={() => handleFilter('real')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                  ${filterType === 'real'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                    : 'bg-white/5 text-gray-500 border-white/5 hover:border-white/15 hover:text-gray-400'}`}
              >
                <UserCircle size={11} className="inline mr-1 -mt-0.5" />
                New Users
              </button>
            </div>

            {/* Search */}
            <form onSubmit={handleSearch} className="flex items-center gap-2">
              <div className="relative">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="text"
                  placeholder="Tìm email..."
                  value={searchInput}
                  onChange={e => setSearchInput(e.target.value)}
                  className="bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2
                             text-sm text-white placeholder-gray-500 outline-none w-48
                             focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition"
                />
              </div>
              {search && (
                <button type="button" onClick={clearSearch}
                  className="text-xs text-gray-400 hover:text-white transition">
                  Xóa
                </button>
              )}
            </form>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 pb-8">
        <div className="bg-zinc-900/80 border border-white/5 rounded-xl overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-[60px_1fr_90px_90px_70px_110px] gap-3 px-5 py-3
                          bg-white/5 text-xs text-gray-400 font-semibold uppercase tracking-wider">
            <span>ID</span>
            <span>Email</span>
            <span className="text-center">Loại</span>
            <span className="text-center">Role</span>
            <span className="text-center">Trạng thái</span>
            <span className="text-center">Thao tác</span>
          </div>

          {/* Rows */}
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-500">
              <Loader2 size={24} className="animate-spin mr-3" />
              Đang tải...
            </div>
          ) : users.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-500">
              <Users size={40} className="mb-3 opacity-30" />
              <p>Không tìm thấy người dùng nào.</p>
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {users.map((u, i) => (
                <motion.div
                  key={u.user_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.015 }}
                  className="grid grid-cols-[60px_1fr_90px_90px_70px_110px] gap-3 px-5 py-3
                             items-center hover:bg-white/[0.03] transition group"
                >
                  {/* ID */}
                  <span className="text-sm text-gray-500 font-mono">#{u.user_id}</span>

                  {/* Email */}
                  <div className="flex items-center gap-2 min-w-0">
                    <Mail size={13} className="text-gray-600 shrink-0" />
                    <span className="text-sm text-white truncate">{u.email}</span>
                  </div>

                  {/* Account Type */}
                  <div className="flex justify-center">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold
                                     border ${typeBadge(u.account_type)}`}>
                      {u.account_type === 'real' ? 'New' : 'Legacy'}
                    </span>
                  </div>

                  {/* Role */}
                  <div className="flex justify-center">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold
                                     border flex items-center gap-1 ${roleBadge(u.role)}`}>
                      {u.role === 'admin' && <Crown size={9} />}
                      {u.role}
                    </span>
                  </div>

                  {/* Active status */}
                  <div className="flex justify-center">
                    <div className={`w-2.5 h-2.5 rounded-full shadow-sm ${activeDot(u.is_active)}`}
                         title={u.is_active ? 'Hoạt động' : 'Đã khóa'} />
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-center gap-1
                                  opacity-40 group-hover:opacity-100 transition">
                    {/* Toggle role */}
                    <button
                      onClick={() => toggleRole(u.user_id, u.role)}
                      className={`p-1.5 rounded-lg transition text-xs
                        ${u.role === 'admin'
                          ? 'hover:bg-blue-500/10 text-blue-400'
                          : 'hover:bg-amber-500/10 text-amber-400'}`}
                      title={u.role === 'admin' ? 'Hạ xuống User' : 'Nâng lên Admin'}
                    >
                      {u.role === 'admin' ? <ShieldOff size={14} /> : <ShieldCheck size={14} />}
                    </button>

                    {/* Toggle active */}
                    <button
                      onClick={() => toggleActive(u.user_id, u.is_active)}
                      className={`p-1.5 rounded-lg transition text-xs
                        ${u.is_active
                          ? 'hover:bg-red-500/10 text-red-400'
                          : 'hover:bg-emerald-500/10 text-emerald-400'}`}
                      title={u.is_active ? 'Khóa tài khoản' : 'Mở khóa'}
                    >
                      {u.is_active ? <Lock size={14} /> : <Unlock size={14} />}
                    </button>

                    {/* Delete — chỉ hiện cho real users */}
                    {u.account_type === 'real' && (
                      <button
                        onClick={() => setDeleteTarget(u)}
                        className="p-1.5 rounded-lg hover:bg-red-500/10 text-red-400 transition"
                        title="Xóa tài khoản"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 bg-white/[0.02] border-t border-white/5">
              <p className="text-xs text-gray-500">
                Trang {page}/{totalPages} · {total.toLocaleString()} users
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
                        ? 'bg-violet-600 text-white shadow shadow-violet-900/30'
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

      {/* Delete Confirmation Modal */}
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
                <p className="text-sm text-gray-400 mb-1">
                  Bạn có chắc muốn xóa tài khoản:
                </p>
                <p className="text-sm text-white font-semibold mb-1">
                  "{deleteTarget.email}"
                </p>
                <p className="text-xs text-gray-500 mb-5">
                  ID #{deleteTarget.user_id} — Tất cả ratings liên quan cũng sẽ bị xóa.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setDeleteTarget(null)}
                    disabled={deleting}
                    className="flex-1 py-2.5 rounded-lg text-sm font-medium text-gray-400
                               bg-white/5 border border-white/10 hover:bg-white/10 transition"
                  >
                    Hủy
                  </button>
                  <button
                    onClick={confirmDelete}
                    disabled={deleting}
                    className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white
                               bg-red-600 hover:bg-red-500
                               disabled:opacity-50 transition-all
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

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 50, x: '-50%' }}
            className={`fixed bottom-8 left-1/2 z-[300] px-6 py-3 rounded-xl shadow-2xl
                        flex items-center gap-2 font-medium text-sm
                        ${toast.type === 'success'
                          ? 'bg-green-600 text-white'
                          : 'bg-red-600 text-white'}`}
          >
            {toast.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
