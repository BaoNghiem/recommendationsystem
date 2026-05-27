import axios from 'axios';

// ============================================================
// Axios Instance - Tự động gắn JWT Token & Xử lý lỗi mạng
// ============================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    // withCredentials: false — dùng Authorization Bearer header thay thế
    // (true sẽ xung đột với allow_origins=["*"] trong CORS backend)
    withCredentials: false,
});

// ── Request Interceptor: Tự động đính kèm Bearer Token ─────
instance.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        console.error('[Axios Request Error]', error.message);
        return Promise.reject(error);
    }
);

// ── Response Interceptor: Xử lý lỗi mạng & 401 ────────────
instance.interceptors.response.use(
    // Thành công: trả response bình thường
    (response) => response,

    // Lỗi: chuyển đổi thành thông báo thân thiện
    (error) => {
        // === Network Error (CORS blocked, server down, DNS fail) ===
        if (!error.response) {
            const friendlyMessage =
                '🔌 Không thể kết nối đến server. ' +
                'Kiểm tra xem Backend (FastAPI) đã chạy tại ' +
                API_BASE_URL + ' chưa.';

            console.error('[Network Error]', error.message);
            console.info('💡 Gợi ý: Chạy `uvicorn src.api.main:app --reload` ở thư mục gốc project');

            // Tạo error object thân thiện thay vì để browser chặn
            const networkError = new Error(friendlyMessage);
            networkError.isNetworkError = true;
            networkError.originalError = error;
            return Promise.reject(networkError);
        }

        const { status, data } = error.response;

        // === 401 Unauthorized: Token hết hạn hoặc không hợp lệ ===
        if (status === 401) {
            console.warn('[Auth] Token hết hạn hoặc không hợp lệ. Đăng xuất...');
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');

            // Dispatch custom event để AuthContext lắng nghe
            window.dispatchEvent(new CustomEvent('auth:logout', {
                detail: { reason: 'token_expired' }
            }));
        }

        // === 403 Forbidden ===
        if (status === 403) {
            console.warn('[Auth] Không có quyền truy cập:', data?.detail);
        }

        // === 500+ Server Error ===
        if (status >= 500) {
            console.error('[Server Error]', data?.detail || 'Lỗi server không xác định.');
        }

        // Chuẩn hóa error message từ FastAPI
        const apiError = new Error(
            data?.detail || data?.message || `Lỗi ${status}: Yêu cầu không thành công.`
        );
        apiError.status = status;
        apiError.data = data;
        apiError.isApiError = true;

        return Promise.reject(apiError);
    }
);

export default instance;
