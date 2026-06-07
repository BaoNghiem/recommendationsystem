import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Video, UserCircle, Globe, Calendar } from 'lucide-react';

/**
 * PersonInfoModal — Hiển thị thông tin đạo diễn / diễn viên.
 * Props:
 *   person: { type: 'director'|'actor', id: int, name: str, birth_year: int, nationality: str, ... }
 *   onClose: callback
 */
export default function PersonInfoModal({ person, onClose }) {
  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!person) return null;

  const isDirector = person.type === 'director';
  const accentColor = isDirector ? 'from-blue-600 to-blue-800' : 'from-violet-600 to-purple-800';
  const Icon = isDirector ? Video : UserCircle;

  const modalContent = (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        style={{ zIndex: 10000 }} // Cao hon MovieDetailModal
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
      />

      <motion.div
        className="fixed inset-0 flex items-center justify-center p-4 pointer-events-none"
        style={{ zIndex: 10001 }}
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ type: 'spring', damping: 20, stiffness: 300 }}
      >
        <div
          className="pointer-events-auto w-full max-w-sm bg-zinc-900 border border-white/10
                     rounded-2xl shadow-2xl overflow-hidden flex flex-col"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className={`relative bg-gradient-to-br ${accentColor} px-6 pt-6 pb-5 flex-shrink-0`}>
            <button
              onClick={onClose}
              className="absolute top-4 right-4 w-7 h-7 rounded-full bg-black/30
                         flex items-center justify-center text-gray-300
                         hover:text-white hover:bg-black/50 transition"
            >
              <X size={14} />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center shadow-inner">
                <Icon size={24} className="text-white" />
              </div>
              <div>
                <p className="text-xs text-white/70 uppercase tracking-wider font-semibold mb-0.5">
                  {isDirector ? 'Đạo diễn' : 'Diễn viên'}
                </p>
                <h2 className="text-lg font-bold text-white leading-tight pr-4">
                  {person.name}
                </h2>
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="px-6 py-5 space-y-4">
            <div className="bg-white/5 rounded-xl p-4 border border-white/10 space-y-3">
              <div className="flex items-center gap-3">
                <Calendar size={16} className="text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Năm sinh</p>
                  <p className="text-sm text-white font-medium">{person.birth_year || 'Đang cập nhật'}</p>
                </div>
              </div>
              <div className="h-px bg-white/10" />
              <div className="flex items-center gap-3">
                <Globe size={16} className="text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Quốc tịch</p>
                  <p className="text-sm text-white font-medium">{person.nationality || 'Đang cập nhật'}</p>
                </div>
              </div>
              {!isDirector && person.character_name && (
                <>
                  <div className="h-px bg-white/10" />
                  <div className="flex items-center gap-3">
                    <UserCircle size={16} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Vai diễn trong phim</p>
                      <p className="text-sm text-white font-medium">{person.character_name}</p>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-white/5 flex justify-end bg-zinc-950">
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
    </AnimatePresence>
  );

  return createPortal(modalContent, document.body);
}
