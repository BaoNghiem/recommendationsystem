import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lock, Eye, EyeOff, Loader2, CheckCircle, AlertCircle,
  KeyRound, Film, AlertTriangle, ShieldCheck, Mail, MailCheck, RefreshCw
} from 'lucide-react';
import api from '../api/axios';

/**
 * ResetPasswordPage — Trang dat lai mat khau khi user click link tu email.
 * Nhan prop `token` (JWT reset token) va `onDone` callback khi hoan tat.
 *
 * Xu ly 3 trang thai:
 *   1. Form nhap mat khau moi (binh thuong)
 *   2. Token het han → hien form gui lai link moi
 *   3. Thanh cong → hien nut dang nhap
 */
export default function ResetPasswordPage({ token, onDone }) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPw, setConfirmPw]     = useState('');
  const [showPw, setShowPw]           = useState(false);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const [success, setSuccess]         = useState(false);

  // Token het han state
  const [tokenExpired, setTokenExpired] = useState(false);
  const [resendEmail, setResendEmail]   = useState('');
  const [resending, setResending]       = useState(false);
  const [resendDone, setResendDone]     = useState(false);
  const [resendError, setResendError]   = useState('');

  const validate = () => {
    if (newPassword.length < 6) return 'Mat khau phai co it nhat 6 ky tu.';
    if (newPassword !== confirmPw) return 'Xac nhan mat khau khong khop.';
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }

    setLoading(true);
    setError('');
    try {
      const res = await api.post('/auth/reset-password', {
        token: token,
        new_password: newPassword,
      });
      setSuccess(true);
    } catch (err) {
      const msg = err.message || '';
      // Phat hien token het han hoac khong hop le
      if (msg.includes('het han') || msg.includes('khong hop le') || err.status === 400) {
        setTokenExpired(true);
      } else {
        setError(msg || 'Dat lai mat khau that bai.');
      }
    }
    setLoading(false);
  };

  // Gui lai link dat lai mat khau
  const handleResendLink = async (e) => {
    e.preventDefault();
    if (!resendEmail.trim()) { setResendError('Vui long nhap email.'); return; }
    setResending(true);
    setResendError('');
    try {
      await api.post('/auth/forgot-password', { email: resendEmail.trim() });
      setResendDone(true);
    } catch (err) {
      setResendError(err.message || 'Khong the gui email. Thu lai sau.');
    }
    setResending(false);
  };

  // Invalid / missing token
  if (!token) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md w-full bg-zinc-900/80 border border-white/5 rounded-2xl p-8 text-center shadow-2xl"
        >
          <div className="w-16 h-16 rounded-full bg-red-500/10 border-2 border-red-500
                          flex items-center justify-center mx-auto mb-5">
            <AlertTriangle size={28} className="text-red-400" />
          </div>
          <h1 className="text-xl font-bold text-white mb-2">Link khong hop le</h1>
          <p className="text-gray-400 text-sm mb-6">
            Link dat lai mat khau khong hop le hoac da het han.
            Vui long yeu cau gui lai email dat lai mat khau.
          </p>
          <button
            onClick={onDone}
            className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl
                       font-semibold text-sm transition-all shadow-lg shadow-red-900/30
                       active:scale-95"
          >
            Ve trang chu
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="max-w-md w-full bg-zinc-900/80 border border-white/5 rounded-2xl overflow-hidden shadow-2xl"
      >
        {/* Gradient accent bar */}
        <div className="h-1 w-full bg-gradient-to-r from-red-600 via-rose-500 to-orange-500" />

        {tokenExpired ? (
          /* ── Token Expired State — Cho phep gui lai link moi ── */
          <div className="px-8 py-10 text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', damping: 15 }}
              className="w-16 h-16 rounded-full bg-amber-500/10 border-2 border-amber-500/30
                          flex items-center justify-center mx-auto mb-5"
            >
              <AlertTriangle size={28} className="text-amber-400" />
            </motion.div>

            <h1 className="text-xl font-bold text-white mb-2">Link da het han</h1>
            <p className="text-gray-400 text-sm leading-relaxed mb-6">
              Link dat lai mat khau chi co hieu luc trong <strong className="text-amber-400">15 phut</strong>.
              <br />Nhap email de nhan link moi.
            </p>

            {resendDone ? (
              /* Da gui thanh cong */
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-2 text-green-400">
                  <MailCheck size={20} />
                  <span className="font-medium text-sm">Email da duoc gui!</span>
                </div>
                <p className="text-gray-500 text-xs">
                  Kiem tra hop thu (va ca <strong className="text-gray-400">thu rac</strong>) de nhan link moi.
                  <br />Link moi co hieu luc trong <strong className="text-amber-400">15 phut</strong>.
                </p>
                <button
                  onClick={onDone}
                  className="mt-4 px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl
                             font-semibold text-sm transition-all shadow-lg shadow-red-900/30
                             active:scale-95"
                >
                  Ve trang chu
                </button>
              </div>
            ) : (
              /* Form nhap email de gui lai */
              <form onSubmit={handleResendLink} className="space-y-3">
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="email"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    placeholder="Nhap email da dang ky"
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-3 text-sm
                               text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none transition"
                  />
                </div>

                {/* Resend error */}
                <AnimatePresence>
                  {resendError && (
                    <motion.p
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="text-red-400 text-xs flex items-center gap-1.5"
                    >
                      <AlertCircle size={12} /> {resendError}
                    </motion.p>
                  )}
                </AnimatePresence>

                <button
                  type="submit"
                  disabled={resending}
                  className="w-full py-3 rounded-lg font-semibold text-sm text-white
                             bg-gradient-to-r from-red-600 to-rose-600
                             hover:from-red-500 hover:to-rose-500
                             disabled:opacity-50 disabled:cursor-not-allowed
                             transition-all shadow-lg shadow-red-900/20
                             flex items-center justify-center gap-2"
                >
                  {resending ? (
                    <><Loader2 size={16} className="animate-spin" /> Dang gui...</>
                  ) : (
                    <><RefreshCw size={16} /> Gui lai link dat lai mat khau</>
                  )}
                </button>

                <button
                  type="button"
                  onClick={onDone}
                  className="w-full text-sm text-gray-500 hover:text-gray-300 transition mt-2"
                >
                  ← Ve trang chu
                </button>
              </form>
            )}
          </div>

        ) : success ? (
          /* ── Success State ── */
          <div className="px-8 py-12 text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', damping: 15 }}
              className="w-20 h-20 rounded-full bg-green-500/10 border-2 border-green-500
                          flex items-center justify-center mx-auto mb-5"
            >
              <ShieldCheck size={36} className="text-green-400" />
            </motion.div>
            <h1 className="text-2xl font-bold text-white mb-3">
              Dat lai mat khau thanh cong!
            </h1>
            <p className="text-gray-400 text-sm leading-relaxed mb-6">
              Mat khau cua ban da duoc cap nhat. Bay gio ban co the
              dang nhap voi mat khau moi.
            </p>
            <button
              onClick={onDone}
              className="px-8 py-3 bg-gradient-to-r from-red-600 to-rose-600
                         hover:from-red-500 hover:to-rose-500
                         text-white rounded-xl font-semibold text-sm
                         transition-all shadow-lg shadow-red-900/30 active:scale-95
                         flex items-center justify-center gap-2 mx-auto"
            >
              <CheckCircle size={16} />
              Dang nhap ngay
            </button>
          </div>
        ) : (
          /* ── Form State ── */
          <div className="px-8 pt-8 pb-10">
            {/* Logo */}
            <div className="flex items-center gap-2 mb-6">
              <div className="w-9 h-9 rounded-xl bg-red-600 flex items-center justify-center">
                <Film size={20} className="text-white" />
              </div>
              <span className="text-white font-bold text-xl tracking-tight">Recommender System</span>
            </div>

            {/* Header */}
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 to-rose-500
                              flex items-center justify-center shadow-lg shadow-red-900/30">
                <KeyRound size={18} className="text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Dat lai mat khau</h1>
                <p className="text-xs text-gray-500">Nhap mat khau moi cho tai khoan cua ban</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 mt-6">
              {/* Error alert */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-red-500/10
                               border border-red-500/20 text-red-400 text-sm"
                  >
                    <AlertCircle size={14} />
                    {error}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* New password */}
              <div>
                <label className="block text-xs text-gray-400 mb-1.5 font-medium">Mat khau moi</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-10 py-3 text-sm
                               text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none
                               transition"
                    placeholder="It nhat 6 ky tu"
                    required
                  />
                  <button type="button" onClick={() => setShowPw(p => !p)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                    {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {newPassword && newPassword.length < 6 && (
                  <p className="text-[11px] text-amber-400 mt-1">Can them {6 - newPassword.length} ky tu nua</p>
                )}
              </div>

              {/* Confirm password */}
              <div>
                <label className="block text-xs text-gray-400 mb-1.5 font-medium">Xac nhan mat khau</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="password"
                    value={confirmPw}
                    onChange={(e) => setConfirmPw(e.target.value)}
                    className={`w-full bg-white/5 border rounded-lg pl-10 pr-4 py-3 text-sm
                               text-white placeholder-gray-600 focus:outline-none transition
                               ${confirmPw && confirmPw !== newPassword
                                 ? 'border-red-500/50 focus:border-red-500'
                                 : 'border-white/10 focus:border-red-500/50'}`}
                    placeholder="Nhap lai mat khau moi"
                    required
                  />
                </div>
                {confirmPw && confirmPw !== newPassword && (
                  <p className="text-[11px] text-red-400 mt-1">Mat khau khong khop</p>
                )}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-lg font-semibold text-sm text-white
                           bg-gradient-to-r from-red-600 to-rose-600
                           hover:from-red-500 hover:to-rose-500
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all shadow-lg shadow-red-900/20
                           flex items-center justify-center gap-2"
              >
                {loading ? (
                  <><Loader2 size={16} className="animate-spin" /> Dang xu ly...</>
                ) : (
                  <><ShieldCheck size={16} /> Dat lai mat khau</>
                )}
              </button>

              {/* Security note */}
              <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
                <AlertTriangle size={14} className="text-amber-400 shrink-0 mt-0.5" />
                <p className="text-[11px] text-gray-500 leading-relaxed">
                  Link dat lai mat khau chi co hieu luc trong <strong className="text-amber-400">15 phut</strong>.
                  Neu het han, vui long yeu cau gui lai email.
                </p>
              </div>
            </form>
          </div>
        )}
      </motion.div>
    </div>
  );
}
