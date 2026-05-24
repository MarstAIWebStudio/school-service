const AIZAMA_URL = 'https://school-service-v23r.onrender.com';

class AizamaApp {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.token = localStorage.getItem('aizama_token');
    }

    async #call(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
            'X-API-Key': this.apiKey
        };
        if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

        const res = await fetch(`${AIZAMA_URL}${endpoint}`, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || '오류 발생');
        return data;
    }

    // 인증
    auth = {
        // 회원가입
        register: async (username, password, email) => {
            return await this.#call('/api/register', 'POST', { username, password, email });
        },

        // 로그인
        login: async (username, password) => {
            const data = await this.#call('/api/login', 'POST', { username, password });
            this.token = data.token;
            localStorage.setItem('aizama_token', data.token);
            localStorage.setItem('aizama_user', JSON.stringify({
                username: data.username,
                role: data.role
            }));
            return data;
        },

        // 로그아웃
        logout: () => {
            this.token = null;
            localStorage.removeItem('aizama_token');
            localStorage.removeItem('aizama_user');
            window.location.href = '/login.html';
        },

        // 현재 유저
        currentUser: () => JSON.parse(localStorage.getItem('aizama_user') || 'null'),

        // 로그인 여부
        isLoggedIn: () => !!localStorage.getItem('aizama_token')
    };

    // 포인트
    points = {
        // 내 포인트 조회
        getBalance: async () => {
            const data = await this.#call('/api/me');
            return data.point_balance;
        },

        // 지급/차감 (운영자)
        adjust: async (userId, amount, reason) => {
            return await this.#call('/api/admin/points', 'POST', {
                user_id: userId, amount, reason
            });
        }
    };

    // 상품
    items = {
        // 목록 조회
        getAll: async () => await this.#call('/api/items'),

        // 추가 (운영자)
        add: async (name, description, price, stock) => {
            return await this.#call('/api/admin/items', 'POST', {
                name, description, price, stock
            });
        }
    };

    // 공지사항
    notices = {
        // 목록 조회
        getAll: async () => await this.#call('/api/notices'),

        // 등록 (운영자)
        add: async (title, content, isPinned = false) => {
            return await this.#call('/api/admin/notices', 'POST', {
                title, content, is_pinned: isPinned
            });
        }
    };

    // 제작 요청
    requests = {
        // 요청하기
        create: async (title, description) => {
            return await this.#call('/api/requests', 'POST', { title, description });
        }
    };

    // 귓속말
    whisper = {
        // 생성 (운영자)
        create: async (userId, message) => {
            return await this.#call('/api/admin/whisper', 'POST', {
                user_id: userId, message
            });
        },

        // 읽기
        read: async (token) => await this.#call(`/api/whisper/${token}`)
    };
}

// 초기화 함수
function initializeAizama(config) {
    return new AizamaApp(config.apiKey);
}