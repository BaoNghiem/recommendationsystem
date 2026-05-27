import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute — chỉ render children nếu đáp ứng điều kiện role.
 * Props:
 *   requiredRole: 'admin' | 'user' (mặc định 'user' — chỉ cần đăng nhập)
 *   fallback: JSX hiển thị khi không có quyền
 */
export default function ProtectedRoute({
  children,
  requiredRole = 'user',
  fallback = null,
}) {
  const { isLoggedIn, user, loading } = useAuth();

  if (loading) return null;

  if (!isLoggedIn) {
    return fallback ?? (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white">
        <div className="text-center space-y-3">
          <ShieldAlert size={48} className="mx-auto text-red-500" />
          <h2 className="text-xl font-bold">Bạn chưa đăng nhập</h2>
          <p className="text-gray-400 text-sm">Vui lòng đăng nhập để truy cập trang này.</p>
        </div>
      </div>
    );
  }

  if (requiredRole === 'admin' && user?.role !== 'admin') {
    return fallback ?? (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white">
        <div className="text-center space-y-3">
          <ShieldAlert size={48} className="mx-auto text-amber-500" />
          <h2 className="text-xl font-bold">Không có quyền truy cập</h2>
          <p className="text-gray-400 text-sm">
            Trang này chỉ dành cho <span className="text-amber-400 font-semibold">Admin</span>.
          </p>
        </div>
      </div>
    );
  }

  return children;
}
