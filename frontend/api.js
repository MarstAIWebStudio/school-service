const API_URL = 'https://school-service-v23r.onrender.com';

// 토큰 관리
const Auth = {
    getToken: () => localStorage.getItem('token'),
    getUser: () => JSON.parse(localStorage.getItem('user') || '{}'),
    setSession: (token, user) => {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
    },
    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login.html';
    },
    isLoggedIn: () => !!localStorage.getItem('token')
};

// API 호출 기본 함수
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = Auth.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || '오류 발생');
    return data;
}

// API 함수들
const API = {
    // 회원가입
    register: (username, password, email) =>
        apiCall('/api/register', 'POST', { username, password, email }),

    // 로그인
    login: async (username, password) => {
        const data = await apiCall('/api/login', 'POST', { username, password });
        Auth.setSession(data.token, { username: data.username, role: data.role });
        return data;
    },

    // 내 정보
    me: () => apiCall('/api/me'),

    // 포인트 지급/차감 (운영자)
    adjustPoints: (userId, amount, reason) =>
        apiCall('/api/admin/points', 'POST', { user_id: userId, amount, reason }),

    // 상품 목록
    getItems: () => apiCall('/api/items'),

    // 상품 추가 (운영자)
    addItem: (name, description, price, stock) =>
        apiCall('/api/admin/items', 'POST', { name, description, price, stock }),

    // 공지사항 목록
    getNotices: () => apiCall('/api/notices'),

    // 공지사항 등록 (운영자)
    addNotice: (title, content, isPinned) =>
        apiCall('/api/admin/notices', 'POST', { title, content, is_pinned: isPinned }),

    // 제작 요청
    createRequest: (title, description) =>
        apiCall('/api/requests', 'POST', { title, description }),

    // 귓속말 링크 생성 (운영자)
    createWhisper: (userId, message) =>
        apiCall('/api/admin/whisper', 'POST', { user_id: userId, message }),

    // 귓속말 읽기
    readWhisper: (token) => apiCall(`/api/whisper/${token}`)
};