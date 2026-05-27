import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X, Mail, Lock, Eye, EyeOff, Film, Loader2, CheckCircle, AlertCircle, MailCheck, RefreshCw, ArrowLeft, KeyRound, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

// ── Backdrop ───────────────────────────────────────────────
const Backdrop = ({ onClick }) => (
  <motion.div
    className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    onClick={onClick}
  />
);

// ── Input Field ────────────────────────────────────────────
const Field = ({ icon: Icon, type, placeholder, value, onChange, rightEl }) => (
  <div className="relative flex items-center">
    <Icon size={18} className="absolute left-3 text-gray-400 pointer-events-none" />
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      required
      className="w-full bg-white/5 border border-white/10 rounded-lg py-3 pl-10 pr-10
                 text-white placeholder-gray-500 text-sm outline-none
                 focus:border-red-500 focus:ring-1 focus:ring-red-500/40 transition"
    />
    {rightEl && <span className="absolute right-3">{rightEl}</span>}
  </div>
);

// ── Verify Pending Screen ──────────────────────────────────
function VerifyPending({ email, password, onBack, onClose }) {
  const [resending, setResending] = useState(false);
  const [resendFeedback, setResendFeedback] = useState(null);

  const handleResend = async () => {
    setResending(true);
    setResendFeedback(null);
    try {
      await api.post('/auth/resend-verification', { email, password });
      setResendFeedback({ type: 'success', msg: 'Email xac thuc da duoc gui lai!' });
    } catch (err) {
      setResendFeedback({ type: 'error', msg: err.response?.data?.detail || 'Loi gui lai email.' });
    }
    setResending(false);
  };

  return (
    <div className="px-8 pt-8 pb-10 text-center">
      {/* Animated mail icon */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', damping: 15, delay: 0.1 }}
        className="mx-auto w-16 h-16 rounded-full bg-green-500/10 border-2 border-green-500/30
                   flex items-center justify-center mb-5"
      >
        <MailCheck size={32} className="text-green-400" />
      </motion.div>

      <h2 className="text-xl font-bold text-white mb-2">Kiem tra hop thu cua ban</h2>
      <p className="text-gray-400 text-sm leading-relaxed mb-2">
        Chung toi da gui link xac thuc den:
      </p>
      <p className="text-white font-semibold text-base bg-white/5 rounded-lg px-4 py-2.5
                    border border-white/10 inline-block mb-4">
        {email}
      </p>
      <p className="text-gray-500 text-xs leading-relaxed mb-6">
        Click vao link trong email de kich hoat tai khoan.<br/>
        Nho kiem tra ca <strong className="text-gray-400">thu rac (Spam)</strong> nhe!<br/>
        Link co hieu luc trong <strong className="text-gray-400">24 gio</strong>.
      </p>

      {/* Resend button */}
      <button
        onClick={handleResend}
        disabled={resending}
        className="flex items-center justify-center gap-2 mx-auto px-5 py-2.5 rounded-lg
                   text-sm font-medium text-gray-300 bg-white/5 border border-white/10
                   hover:bg-white/10 hover:text-white transition
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {resending ? <Loader2 size={15} className="animate-spin" /> : <RefreshCw size={15} />}
        Gui lai email
      </button>

      {/* Resend feedback */}
      <AnimatePresence>
        {resendFeedback && (
          <motion.div
            initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className={`mt-3 flex items-center justify-center gap-2 text-xs ${
              resendFeedback.type === 'success' ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {resendFeedback.type === 'success' ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
            {resendFeedback.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Back to login */}
      <div className="mt-6 pt-5 border-t border-white/5">
        <button
          onClick={onBack}
          className="text-sm text-red-400 hover:text-red-300 hover:underline transition"
        >
          ← Da xac thuc? Dang nhap ngay
        </button>
      </div>
    </div>
  );
}


// ── Forgot Password Screen ─────────────────────────────────
function ForgotPasswordScreen({ onBack }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFeedback(null);
    try {
      const res = await api.post('/auth/forgot-password', { email });
      setSent(true);
      setFeedback({ type: 'success', msg: res.data.message });
    } catch (err) {
      setFeedback({ type: 'error', msg: err.message || 'Da xay ra loi. Thu lai sau.' });
    }
    setLoading(false);
  };

  return (
    <div className="px-8 pt-8 pb-10">
      {/* Logo */}
      <div className="flex items-center gap-2 mb-6">
        <div className="w-9 h-9 rounded-xl bg-red-600 flex items-center justify-center">
          <Film size={20} className="text-white" />
        </div>
        <span className="text-white font-bold text-xl tracking-tight">Recommender System</span>
      </div>

      {sent ? (
        /* ── Success State ── */
        <div className="text-center py-4">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', damping: 15 }}
            className="mx-auto w-16 h-16 rounded-full bg-green-500/10 border-2 border-green-500/30
                       flex items-center justify-center mb-5"
          >
            <MailCheck size={32} className="text-green-400" />
          </motion.div>

          <h2 className="text-xl font-bold text-white mb-3">Kiem tra hop thu</h2>
          <p className="text-gray-400 text-sm leading-relaxed mb-2">
            {feedback?.msg}
          </p>
          <p className="text-gray-500 text-xs leading-relaxed mb-6">
            Nho kiem tra ca <strong className="text-gray-400">thu rac (Spam)</strong>.<br/>
            Link co hieu luc trong <strong className="text-gray-400">15 phut</strong>.
          </p>

          <div className="pt-5 border-t border-white/5">
            <button
              onClick={onBack}
              className="flex items-center gap-2 mx-auto text-sm text-red-400 hover:text-red-300 transition"
            >
              <ArrowLeft size={14} />
              Quay lai dang nhap
            </button>
          </div>
        </div>
      ) : (
        /* ── Form State ── */
        <>
          <h2 className="text-2xl font-bold text-white mb-1">Quen mat khau?</h2>
          <p className="text-gray-400 text-sm mb-7">
            Nhap email da dang ky. Chung toi se gui link dat lai mat khau.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Field
              icon={Mail} type="email" placeholder="Email cua ban"
              value={email} onChange={(e) => setEmail(e.target.value)}
            />

            {/* Feedback */}
            <AnimatePresence>
              {feedback && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2
                    ${feedback.type === 'success'
                      ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                      : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}
                >
                  {feedback.type === 'success'
                    ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
                  {feedback.msg}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg font-semibold text-white text-sm
                         bg-gradient-to-r from-red-600 to-rose-600
                         hover:from-red-500 hover:to-rose-500
                         disabled:opacity-60 disabled:cursor-not-allowed
                         transition-all shadow-lg shadow-red-900/30
                         flex items-center justify-center gap-2"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              <KeyRound size={16} />
              Gui link dat lai mat khau
            </button>
          </form>

          {/* Back to login */}
          <div className="mt-6 pt-5 border-t border-white/5 text-center">
            <button
              onClick={onBack}
              className="flex items-center gap-2 mx-auto text-sm text-red-400 hover:text-red-300 transition"
            >
              <ArrowLeft size={14} />
              Quay lai dang nhap
            </button>
          </div>
        </>
      )}
    </div>
  );
}


// ── Main Modal ─────────────────────────────────────────────
export default function LoginModal({ onClose }) {
  const { login, register } = useAuth();

  // 'login' | 'register' | 'verify-pending' | 'forgot-password'
  const [mode, setMode]           = useState('login');
  const [email, setEmail]         = useState('');
  const [password, setPassword]   = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [showPw, setShowPw]       = useState(false);
  const [showConfirmPw, setShowConfirmPw] = useState(false);
  const [loading, setLoading]     = useState(false);
  const [feedback, setFeedback]   = useState(null);
  const [pendingEmail, setPendingEmail] = useState('');
  const [pendingPassword, setPendingPassword] = useState('');

  const reset = () => {
    setEmail(''); setPassword(''); setConfirmPw(''); setFeedback(null); setLoading(false);
  };

  const switchMode = (m) => { setMode(m); reset(); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFeedback(null);

    // Kiem tra xac nhan mat khau khi dang ky
    if (mode === 'register') {
      if (password !== confirmPw) {
        setFeedback({ type: 'error', msg: 'Mat khau xac nhan khong khop!' });
        setLoading(false);
        return;
      }
      if (password.length < 6) {
        setFeedback({ type: 'error', msg: 'Mat khau phai co it nhat 6 ky tu.' });
        setLoading(false);
        return;
      }
    }

    try {
      if (mode === 'login') {
        await login(email, password);
        setFeedback({ type: 'success', msg: 'Dang nhap thanh cong! 🎉' });
        setTimeout(onClose, 900);
      } else {
        const res = await register(email, password);
        // Chuyen sang man verify-pending
        setPendingEmail(email);
        setPendingPassword(password);
        setMode('verify-pending');
      }
    } catch (err) {
      setFeedback({ type: 'error', msg: err.message || 'Da xay ra loi. Thu lai sau.' });
    } finally {
      setLoading(false);
    }
  };

  const handleBackFromVerify = () => {
    setMode('login');
    setEmail(pendingEmail);
    setPassword('');
    setFeedback(null);
  };

  return (
    <>
      <Backdrop onClick={onClose} />

      <motion.div
        className="fixed inset-0 z-[201] flex items-center justify-center p-4 pointer-events-none"
        initial={{ opacity: 0, scale: 0.92, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 20 }}
        transition={{ type: 'spring', damping: 22, stiffness: 300 }}
      >
        <div
          className="pointer-events-auto w-full max-w-md relative
                     bg-gradient-to-br from-zinc-900 via-zinc-900 to-zinc-800
                     border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header gradient bar */}
          <div className="h-1 w-full bg-gradient-to-r from-red-600 via-rose-500 to-orange-500" />

          {/* Close */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition z-10"
          >
            <X size={20} />
          </button>

          {/* ── Verify Pending Screen ─── */}
          {mode === 'verify-pending' ? (
            <VerifyPending
              email={pendingEmail}
              password={pendingPassword}
              onBack={handleBackFromVerify}
              onClose={onClose}
            />

          /* ── Forgot Password Screen ─── */
          ) : mode === 'forgot-password' ? (
            <ForgotPasswordScreen
              onBack={() => switchMode('login')}
            />

          ) : (
            /* ── Login / Register Form ─── */
            <div className="px-8 pt-8 pb-10">
              {/* Logo */}
              <div className="flex items-center gap-2 mb-6">
                <div className="w-9 h-9 rounded-xl bg-red-600 flex items-center justify-center">
                  <Film size={20} className="text-white" />
                </div>
                <span className="text-white font-bold text-xl tracking-tight">Recommender System</span>
              </div>

              {/* Title */}
              <h2 className="text-2xl font-bold text-white mb-1">
                {mode === 'login' ? 'Dang nhap' : 'Tao tai khoan'}
              </h2>
              <p className="text-gray-400 text-sm mb-7">
                {mode === 'login'
                  ? 'Chao mung tro lai! Dang nhap de nhan goi y phim ca nhan.'
                  : 'Tham gia de AI goi y phim theo so thich cua ban.'}
              </p>

              {/* Tab switcher */}
              <div className="flex bg-white/5 rounded-lg p-1 mb-6">
                {['login', 'register'].map((m) => (
                  <button
                    key={m}
                    onClick={() => switchMode(m)}
                    className={`flex-1 py-2 rounded-md text-sm font-medium transition
                      ${mode === m
                        ? 'bg-red-600 text-white shadow'
                        : 'text-gray-400 hover:text-white'}`}
                  >
                    {m === 'login' ? 'Dang nhap' : 'Dang ky'}
                  </button>
                ))}
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <Field
                  icon={Mail} type="email" placeholder="Email cua ban"
                  value={email} onChange={(e) => setEmail(e.target.value)}
                />
                <Field
                  icon={Lock}
                  type={showPw ? 'text' : 'password'}
                  placeholder={mode === 'register' ? 'Mat khau (toi thieu 6 ky tu)' : 'Mat khau'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  rightEl={
                    <button type="button" onClick={() => setShowPw(p => !p)}
                      className="text-gray-400 hover:text-white transition">
                      {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  }
                />

                {/* Xac nhan mat khau (chi hien khi dang ky) */}
                {mode === 'register' && (
                  <Field
                    icon={ShieldCheck}
                    type={showConfirmPw ? 'text' : 'password'}
                    placeholder="Xac nhan mat khau"
                    value={confirmPw}
                    onChange={(e) => setConfirmPw(e.target.value)}
                    rightEl={
                      <button type="button" onClick={() => setShowConfirmPw(p => !p)}
                        className="text-gray-400 hover:text-white transition">
                        {showConfirmPw ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    }
                  />
                )}

                {/* Forgot password link (only show on login mode) */}
                {mode === 'login' && (
                  <div className="flex justify-end -mt-1">
                    <button
                      type="button"
                      onClick={() => switchMode('forgot-password')}
                      className="text-xs text-gray-500 hover:text-red-400 transition"
                    >
                      Quen mat khau?
                    </button>
                  </div>
                )}

                {/* Feedback */}
                <AnimatePresence>
                  {feedback && (
                    <motion.div
                      initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                      className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2
                        ${feedback.type === 'success'
                          ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                          : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}
                    >
                      {feedback.type === 'success'
                        ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
                      {feedback.msg}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-lg font-semibold text-white text-sm
                             bg-gradient-to-r from-red-600 to-rose-600
                             hover:from-red-500 hover:to-rose-500
                             disabled:opacity-60 disabled:cursor-not-allowed
                             transition-all shadow-lg shadow-red-900/30
                             flex items-center justify-center gap-2"
                >
                  {loading && <Loader2 size={16} className="animate-spin" />}
                  {mode === 'login' ? 'Dang nhap' : 'Tao tai khoan'}
                </button>
              </form>

              {/* Note cho legacy user */}
              {mode === 'login' && (
                <p className="mt-5 text-xs text-gray-500 text-center">
                  User mau (ID 1-6040) khong the dang nhap —{' '}
                  <button onClick={() => switchMode('register')} className="text-red-400 hover:underline">
                    Dang ky tai khoan moi
                  </button>
                </p>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </>
  );
}
