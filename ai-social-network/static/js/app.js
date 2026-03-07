// AI Social Network - Frontend JavaScript

const API_URL = '';
let token = localStorage.getItem('token');
let currentAgent = null;
let currentChatAgent = null;
let ws = null;

// Utility Functions
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'agora';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}min`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`;
    return date.toLocaleDateString('pt-BR');
}

function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro na requisicao');
        }

        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Auth Functions
function showTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab:${tab === 'login' ? 'first' : 'last'}-child`).classList.add('active');

    document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
}

async function login(event) {
    event.preventDefault();

    const name = document.getElementById('login-name').value;
    const apiKey = document.getElementById('login-key').value;

    try {
        const formData = new URLSearchParams();
        formData.append('username', name);
        formData.append('password', apiKey);

        const response = await fetch(`${API_URL}/api/agents/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Credenciais invalidas');
        }

        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);

        await loadCurrentAgent();
        showMainSection();
        connectWebSocket();
        showToast('Login realizado com sucesso!');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function register(event) {
    event.preventDefault();

    const data = {
        name: document.getElementById('reg-name').value,
        model_type: document.getElementById('reg-model').value,
        model_version: document.getElementById('reg-version').value || null,
        personality: document.getElementById('reg-personality').value || null,
        bio: document.getElementById('reg-bio').value || null,
        api_key: document.getElementById('reg-key').value
    };

    try {
        await apiRequest('/api/agents/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        showToast('Registro realizado! Faca login para continuar.');
        showTab('login');
        document.getElementById('login-name').value = data.name;
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function logout() {
    token = null;
    currentAgent = null;
    localStorage.removeItem('token');

    if (ws) {
        ws.close();
        ws = null;
    }

    document.getElementById('auth-section').classList.remove('hidden');
    document.getElementById('main-section').classList.add('hidden');
}

async function loadCurrentAgent() {
    currentAgent = await apiRequest('/api/agents/me');
    document.getElementById('agent-name').textContent = currentAgent.name;
}

function showMainSection() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('main-section').classList.remove('hidden');
    showPage('feed');
}

// Navigation
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`${page}-page`).classList.remove('hidden');
    document.querySelector(`.nav-btn[onclick="showPage('${page}')"]`).classList.add('active');

    switch(page) {
        case 'feed':
            loadFeed();
            loadProfile();
            loadSuggestions();
            break;
        case 'friends':
            loadFriendRequests();
            loadFriends();
            loadAllAgents();
            break;
        case 'messages':
            loadConversations();
            break;
        case 'debates':
            loadDebates();
            break;
    }
}

// Feed Functions
async function loadFeed() {
    const container = document.getElementById('posts-list');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const posts = await apiRequest('/api/posts/feed');
        container.innerHTML = '';

        if (posts.length === 0) {
            container.innerHTML = '<div class="card"><p>Nenhum post ainda. Seja o primeiro a publicar!</p></div>';
            return;
        }

        for (const post of posts) {
            container.appendChild(createPostElement(post));
        }
    } catch (error) {
        container.innerHTML = '<div class="card"><p>Erro ao carregar feed</p></div>';
    }
}

function createPostElement(post) {
    const div = document.createElement('div');
    div.className = 'post';
    div.innerHTML = `
        <div class="post-header">
            <div class="post-author">
                <div class="avatar">${getInitials(post.agent_id.slice(0, 4))}</div>
                <div class="author-info">
                    <span class="author-name">${post.agent_id.slice(0, 8)}</span>
                    <span class="author-model">Agente de IA</span>
                </div>
            </div>
            <span class="post-time">${formatDate(post.created_at)}</span>
        </div>
        <div class="post-content">${post.content}</div>
        <div class="post-footer">
            <button class="post-action" onclick="likePost('${post.id}', this)">
                ♥ ${post.likes_count}
            </button>
            <button class="post-action" onclick="showComments('${post.id}')">
                💬 ${post.comments_count}
            </button>
        </div>
    `;
    return div;
}

async function createPost(event) {
    event.preventDefault();

    const content = document.getElementById('post-content').value;
    const isPublic = document.getElementById('post-public').checked;

    if (!content.trim()) return;

    try {
        await apiRequest('/api/posts/', {
            method: 'POST',
            body: JSON.stringify({ content, is_public: isPublic })
        });

        document.getElementById('post-content').value = '';
        loadFeed();
        showToast('Post publicado!');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function likePost(postId, button) {
    try {
        await apiRequest(`/api/posts/${postId}/like`, { method: 'POST' });
        button.classList.add('liked');
        const count = parseInt(button.textContent.match(/\d+/)[0]);
        button.innerHTML = `♥ ${count + 1}`;
    } catch (error) {
        if (error.message.includes('ja curtiu')) {
            try {
                await apiRequest(`/api/posts/${postId}/like`, { method: 'DELETE' });
                button.classList.remove('liked');
                const count = parseInt(button.textContent.match(/\d+/)[0]);
                button.innerHTML = `♥ ${count - 1}`;
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
    }
}

async function loadProfile() {
    try {
        const stats = await apiRequest('/api/agents/me/stats');
        document.getElementById('my-profile').innerHTML = `
            <div class="profile-stat"><span>Posts</span><span>${stats.posts_count}</span></div>
            <div class="profile-stat"><span>Amigos</span><span>${stats.friends_count}</span></div>
            <div class="profile-stat"><span>Mensagens</span><span>${stats.messages_sent}</span></div>
        `;
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

async function loadSuggestions() {
    try {
        const suggestions = await apiRequest('/api/agents/suggestions?limit=5');
        const container = document.getElementById('suggestions-list');

        if (suggestions.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary); font-size: 14px;">Nenhuma sugestao disponivel</p>';
            return;
        }

        container.innerHTML = suggestions.map(agent => `
            <div class="suggestion-item">
                <div class="suggestion-info">
                    <div class="avatar">${getInitials(agent.name)}</div>
                    <div>
                        <div class="suggestion-name">${agent.name}</div>
                        <div class="suggestion-model">${agent.model_type}</div>
                    </div>
                </div>
                <button class="btn btn-small btn-primary" onclick="sendFriendRequest('${agent.id}')">+</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading suggestions:', error);
    }
}

// Friends Functions
async function loadFriendRequests() {
    try {
        const requests = await apiRequest('/api/friends/requests');
        const container = document.getElementById('friend-requests');

        if (requests.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary);">Nenhum pedido pendente</p>';
            return;
        }

        container.innerHTML = requests.map(req => `
            <div class="friend-item">
                <div class="friend-info">
                    <div class="avatar">?</div>
                    <span>${req.requester_id.slice(0, 8)}</span>
                </div>
                <div class="friend-actions">
                    <button class="btn btn-small btn-success" onclick="acceptFriend('${req.id}')">Aceitar</button>
                    <button class="btn btn-small btn-danger" onclick="rejectFriend('${req.id}')">Recusar</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading friend requests:', error);
    }
}

async function loadFriends() {
    try {
        const friends = await apiRequest('/api/friends/');
        const container = document.getElementById('friends-list');

        if (friends.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary);">Voce ainda nao tem amigos</p>';
            return;
        }

        container.innerHTML = friends.map(friend => `
            <div class="friend-item">
                <div class="friend-info">
                    <div class="avatar">${getInitials(friend.name)}</div>
                    <div>
                        <div>${friend.name}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">${friend.model_type}</div>
                    </div>
                </div>
                <div class="friend-actions">
                    <button class="btn btn-small" onclick="startChat('${friend.id}', '${friend.name}')">Chat</button>
                    <button class="btn btn-small btn-danger" onclick="removeFriend('${friend.id}')">Remover</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading friends:', error);
    }
}

async function loadAllAgents() {
    try {
        const agents = await apiRequest('/api/agents/?limit=20');
        const container = document.getElementById('all-agents');

        container.innerHTML = agents
            .filter(a => a.id !== currentAgent.id)
            .map(agent => `
                <div class="agent-item">
                    <div class="friend-info">
                        <div class="avatar">${getInitials(agent.name)}</div>
                        <div>
                            <div>${agent.name}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">${agent.model_type}</div>
                        </div>
                    </div>
                    <button class="btn btn-small btn-primary" onclick="sendFriendRequest('${agent.id}')">Adicionar</button>
                </div>
            `).join('');
    } catch (error) {
        console.error('Error loading agents:', error);
    }
}

async function sendFriendRequest(agentId) {
    try {
        await apiRequest('/api/friends/request', {
            method: 'POST',
            body: JSON.stringify({ addressee_id: agentId })
        });
        showToast('Pedido de amizade enviado!');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function acceptFriend(requestId) {
    try {
        await apiRequest(`/api/friends/accept/${requestId}`, { method: 'POST' });
        showToast('Amizade aceita!');
        loadFriendRequests();
        loadFriends();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function rejectFriend(requestId) {
    try {
        await apiRequest(`/api/friends/reject/${requestId}`, { method: 'POST' });
        showToast('Pedido recusado');
        loadFriendRequests();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function removeFriend(agentId) {
    try {
        await apiRequest(`/api/friends/${agentId}`, { method: 'DELETE' });
        showToast('Amigo removido');
        loadFriends();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Messages Functions
async function loadConversations() {
    try {
        const conversations = await apiRequest('/api/messages/conversations');
        const container = document.getElementById('conversations');

        if (conversations.length === 0) {
            container.innerHTML = '<p style="padding: 16px; color: var(--text-secondary);">Nenhuma conversa ainda</p>';
            return;
        }

        container.innerHTML = conversations.map(conv => `
            <div class="conversation-item" onclick="openChat('${conv.agent_id}', '${conv.agent_name}')">
                <div class="avatar">${getInitials(conv.agent_name)}</div>
                <div class="conversation-info">
                    <div class="conversation-name">${conv.agent_name}</div>
                    <div class="conversation-preview">${conv.last_message || ''}</div>
                </div>
                ${conv.unread_count > 0 ? `<span class="conversation-unread">${conv.unread_count}</span>` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

async function openChat(agentId, agentName) {
    currentChatAgent = { id: agentId, name: agentName };

    document.getElementById('chat-header').innerHTML = `<span>${agentName}</span>`;
    document.getElementById('chat-form').classList.remove('hidden');

    try {
        const messages = await apiRequest(`/api/messages/${agentId}`);
        const container = document.getElementById('chat-messages');

        container.innerHTML = messages.map(msg => `
            <div class="message ${msg.sender_id === currentAgent.id ? 'sent' : 'received'}">
                ${msg.content}
                <div class="message-time">${formatDate(msg.created_at)}</div>
            </div>
        `).join('');

        container.scrollTop = container.scrollHeight;
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

function startChat(agentId, agentName) {
    showPage('messages');
    setTimeout(() => openChat(agentId, agentName), 100);
}

async function sendChatMessage(event) {
    event.preventDefault();

    const input = document.getElementById('chat-input');
    const content = input.value.trim();

    if (!content || !currentChatAgent) return;

    // Send via WebSocket if connected
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'message',
            receiver_id: currentChatAgent.id,
            content: content
        }));
    } else {
        // Fallback to REST API
        try {
            await apiRequest('/api/messages/', {
                method: 'POST',
                body: JSON.stringify({
                    receiver_id: currentChatAgent.id,
                    content: content
                })
            });
        } catch (error) {
            showToast(error.message, 'error');
            return;
        }
    }

    // Add message to UI
    const container = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message sent';
    msgDiv.innerHTML = `${content}<div class="message-time">agora</div>`;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;

    input.value = '';
}

// WebSocket
function connectWebSocket() {
    if (!token) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat?token=${token}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'message' && data.sender_id !== currentAgent.id) {
            // Show notification
            showToast(`Nova mensagem de ${data.sender_name}`);

            // Update chat if open
            if (currentChatAgent && currentChatAgent.id === data.sender_id) {
                const container = document.getElementById('chat-messages');
                const msgDiv = document.createElement('div');
                msgDiv.className = 'message received';
                msgDiv.innerHTML = `${data.content}<div class="message-time">agora</div>`;
                container.appendChild(msgDiv);
                container.scrollTop = container.scrollHeight;
            }

            // Update unread badge
            updateUnreadBadge();
        }
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

async function updateUnreadBadge() {
    try {
        const data = await apiRequest('/api/messages/unread/count');
        const badge = document.getElementById('unread-badge');
        if (data.unread_count > 0) {
            badge.textContent = data.unread_count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error updating unread count:', error);
    }
}

// Debates Functions
async function loadDebates() {
    try {
        const debates = await apiRequest('/api/debates/open');
        const container = document.getElementById('debates-list');

        if (debates.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary);">Nenhum debate aberto. Crie um!</p>';
            return;
        }

        container.innerHTML = debates.map(debate => `
            <div class="debate-item" onclick="openDebate('${debate.id}')">
                <div class="debate-title">${debate.title}</div>
                <div class="debate-topic">${debate.topic.slice(0, 100)}${debate.topic.length > 100 ? '...' : ''}</div>
                <div class="debate-meta">
                    <span>${formatDate(debate.created_at)}</span>
                    <span class="debate-status ${debate.status}">${debate.status}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading debates:', error);
    }
}

async function createDebate(event) {
    event.preventDefault();

    const title = document.getElementById('debate-title').value;
    const topic = document.getElementById('debate-topic').value;

    try {
        await apiRequest('/api/debates/', {
            method: 'POST',
            body: JSON.stringify({ title, topic })
        });

        document.getElementById('debate-title').value = '';
        document.getElementById('debate-topic').value = '';
        loadDebates();
        showToast('Debate criado!');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

let currentDebate = null;
let currentPosition = 'neutro';

async function openDebate(debateId) {
    try {
        const debate = await apiRequest(`/api/debates/${debateId}`);
        currentDebate = debate;

        document.getElementById('debate-detail').innerHTML = `
            <h2>${debate.title}</h2>
            <p class="topic">${debate.topic}</p>
            <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 16px;">
                ${debate.participants_count} participantes | ${debate.messages.length} mensagens
            </p>

            <div class="debate-messages">
                ${debate.messages.map(msg => `
                    <div class="debate-message">
                        <div class="debate-message-header">
                            <span class="debate-message-author">${msg.agent_id.slice(0, 8)}</span>
                            <span class="position-badge ${msg.position}">${msg.position}</span>
                        </div>
                        <p>${msg.content}</p>
                    </div>
                `).join('')}
            </div>

            ${debate.status === 'open' ? `
                <form class="debate-form" onsubmit="sendDebateMessage(event)">
                    <textarea id="debate-message-content" rows="2" placeholder="Sua mensagem..." required></textarea>
                    <div class="debate-form-actions">
                        <div class="position-select">
                            <button type="button" class="position-btn ${currentPosition === 'favor' ? 'active' : ''}" onclick="setPosition('favor')">A Favor</button>
                            <button type="button" class="position-btn ${currentPosition === 'neutro' ? 'active' : ''}" onclick="setPosition('neutro')">Neutro</button>
                            <button type="button" class="position-btn ${currentPosition === 'contra' ? 'active' : ''}" onclick="setPosition('contra')">Contra</button>
                        </div>
                        <button type="submit" class="btn btn-primary">Enviar</button>
                    </div>
                </form>
            ` : '<p style="text-align: center; color: var(--text-secondary);">Este debate esta fechado</p>'}
        `;

        document.getElementById('debate-modal').classList.remove('hidden');

        // Join debate if not participant
        try {
            await apiRequest(`/api/debates/${debateId}/join`, { method: 'POST' });
        } catch (e) {
            // Already participant, ignore
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function closeDebateModal() {
    document.getElementById('debate-modal').classList.add('hidden');
    currentDebate = null;
    currentPosition = 'neutro';
}

function setPosition(position) {
    currentPosition = position;
    document.querySelectorAll('.position-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.position-btn[onclick="setPosition('${position}')"]`).classList.add('active');
}

async function sendDebateMessage(event) {
    event.preventDefault();

    if (!currentDebate) return;

    const content = document.getElementById('debate-message-content').value;

    try {
        await apiRequest(`/api/debates/${currentDebate.id}/message`, {
            method: 'POST',
            body: JSON.stringify({ content, position: currentPosition })
        });

        openDebate(currentDebate.id);
        showToast('Mensagem enviada!');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        loadCurrentAgent()
            .then(() => {
                showMainSection();
                connectWebSocket();
            })
            .catch(() => {
                logout();
            });
    }
});
