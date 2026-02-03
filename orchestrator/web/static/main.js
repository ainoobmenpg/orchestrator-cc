/**
 * orchestrator-cc Dashboard
 *
 * WebSocketによるリアルタイムダッシュボード
 */

// ============================================================================
// 設定
// ============================================================================

const CONFIG = {
    wsUrl: `ws://${window.location.host}/ws`,
    apiUrl: `/api`,
    reconnectDelay: 3000,
    maxReconnectAttempts: 10,
    messageBufferSize: 1000,
};

// ============================================================================
// グローバル状態
// ============================================================================

const state = {
    ws: null,
    reconnectAttempts: 0,
    reconnectTimer: null,
    agents: new Map(),
    messages: [],
    messageCount: { total: 0, thinking: 0, task: 0, result: 0 },
    isAutoScroll: true,
    showThinking: true,
    showTimestamp: false,
    pendingConfirm: null,
};

// ============================================================================
// WebSocketクライアント
// ============================================================================

class DashboardClient {
    constructor() {
        this.ws = null;
        this.messageHandlers = new Map();
        this.setupDefaultHandlers();
    }

    connect() {
        try {
            this.ws = new WebSocket(CONFIG.wsUrl);
            this.setupEventListeners();
        } catch (error) {
            console.error('WebSocket接続エラー:', error);
            this.handleReconnect();
        }
    }

    setupEventListeners() {
        if (!this.ws) return;

        this.ws.onopen = () => {
            console.log('WebSocket接続完了');
            state.reconnectAttempts = 0;
            updateConnectionStatus('connected');
            hideReconnectModal();

            // 初期データをリクエスト
            this.send({
                type: 'subscribe',
                channels: ['messages', 'thinking', 'status']
            });

            // エージェント状態をリクエスト
            this.fetchAgents();
            // 過去ログをリクエスト
            this.fetchRecentMessages();
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('メッセージ解析エラー:', error, event.data);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocketエラー:', error);
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket切断:', event.code, event.reason);
            updateConnectionStatus('disconnected');
            this.handleReconnect();
        };
    }

    handleMessage(message) {
        const handler = this.messageHandlers.get(message.type);
        if (handler) {
            handler(message);
        } else {
            console.warn('未処理のメッセージタイプ:', message.type, message);
        }
    }

    setupDefaultHandlers() {
        this.on('status', handleStatusMessage);
        this.on('message', handleAgentMessage);
        this.on('thinking', handleThinkingMessage);
        this.on('agents', handleAgentsMessage);
        this.on('error', handleErrorMessage);
        this.on('pong', handlePongMessage);
    }

    on(type, callback) {
        this.messageHandlers.set(type, callback);
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket未接続: メッセージ送信スキップ', data);
        }
    }

    async fetchAgents() {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/status`);
            if (response.ok) {
                const data = await response.json();
                handleAgentsMessage({ type: 'agents', agents: data.agents || [] });
            }
        } catch (error) {
            console.error('エージェント状態取得エラー:', error);
        }
    }

    async fetchRecentMessages(limit = 100) {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/messages?limit=${limit}`);
            if (response.ok) {
                const data = await response.json();
                const messages = data.messages || [];
                messages.forEach(msg => {
                    if (msg.type === 'task' || msg.type === 'result') {
                        handleAgentMessage(msg);
                    } else if (msg.type === 'thinking') {
                        handleThinkingMessage(msg);
                    }
                });
            }
        } catch (error) {
            console.error('過去ログ取得エラー:', error);
        }
    }

    handleReconnect() {
        if (state.reconnectAttempts >= CONFIG.maxReconnectAttempts) {
            showNotification('再接続を諦めました。ページをリロードしてください。', 'error');
            return;
        }

        state.reconnectAttempts++;
        showReconnectModal(state.reconnectAttempts);

        state.reconnectTimer = setTimeout(() => {
            console.log(`再接続試行 ${state.reconnectAttempts}/${CONFIG.maxReconnectAttempts}`);
            this.connect();
        }, CONFIG.reconnectDelay);
    }

    disconnect() {
        if (state.reconnectTimer) {
            clearTimeout(state.reconnectTimer);
        }
        if (this.ws) {
            this.ws.onclose = null;
            this.ws.close();
        }
    }
}

// ============================================================================
// メッセージハンドラー
// ============================================================================

function handleStatusMessage(message) {
    const { agent, status } = message;
    const agentInfo = state.agents.get(agent);
    if (agentInfo) {
        agentInfo.status = status;
        renderAgent(agent);
    }
}

function handleAgentMessage(message) {
    const { timestamp, from_agent, to_agent, content, type = 'task' } = message;

    // メッセージカウント更新
    state.messageCount.total++;
    state.messageCount[type === 'task' ? 'task' : 'result']++;

    addMessageToDom({
        timestamp,
        type,
        from: from_agent,
        to: to_agent,
        content,
    });

    updateMessageStats();
}

function handleThinkingMessage(message) {
    const { timestamp, agent, content } = message;

    state.messageCount.total++;
    state.messageCount.thinking++;

    addMessageToDom({
        timestamp,
        type: 'thinking',
        agent,
        content,
    });

    updateMessageStats();
}

function handleAgentsMessage(message) {
    const { agents } = message;

    // エージェント状態を更新
    agents.forEach(agent => {
        const existing = state.agents.get(agent.name);
        const info = {
            name: agent.name,
            role: agent.role || 'agent',
            status: agent.status || 'unknown',
            lastActivity: agent.lastActivity || null,
            taskCount: agent.taskCount || 0,
        };

        if (!existing) {
            state.agents.set(agent.name, info);
            addAgentToDom(info);
        } else {
            state.agents.set(agent.name, info);
            renderAgent(agent.name);
        }
    });

    // クラスタ名を更新
    updateClusterName(message.clusterName || 'orchestrator-cc');
}

function handleErrorMessage(message) {
    showNotification(message.content || 'エラーが発生しました', 'error');
}

function handlePongMessage(message) {
    // Pingに対するPong応答
    console.debug('Pong received');
}

// ============================================================================
// UIレンダリング
// ============================================================================

function addAgentToDom(agent) {
    const agentList = document.getElementById('agent-list');

    // ローディングメッセージを削除
    const loading = agentList.querySelector('.loading');
    if (loading) {
        loading.remove();
    }

    const agentDiv = document.createElement('div');
    agentDiv.className = 'agent-card';
    agentDiv.id = `agent-${agent.name}`;
    agentDiv.innerHTML = renderAgentHtml(agent);

    agentList.appendChild(agentDiv);
}

function renderAgent(agentName) {
    const agentInfo = state.agents.get(agentName);
    if (!agentInfo) return;

    const agentDiv = document.getElementById(`agent-${agentName}`);
    if (agentDiv) {
        agentDiv.innerHTML = renderAgentHtml(agentInfo);
    }
}

function renderAgentHtml(agent) {
    const statusIcons = {
        running: '🟢',
        idle: '🟡',
        stopped: '🔴',
        error: '❌',
        unknown: '⚪',
    };

    const statusLabels = {
        running: '実行中',
        idle: '待機中',
        stopped: '停止',
        error: 'エラー',
        unknown: '不明',
    };

    const icon = statusIcons[agent.status] || statusIcons.unknown;
    const statusLabel = statusLabels[agent.status] || '不明';

    return `
        <div class="agent-icon">${icon}</div>
        <div class="agent-info">
            <div class="agent-name">${escapeHtml(agent.name)}</div>
            <div class="agent-role">${escapeHtml(agent.role)}</div>
            <div class="agent-status">${statusLabel}</div>
        </div>
    `;
}

function addMessageToDom(message) {
    const container = document.getElementById('messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${message.type}`;

    // 思考ログで非表示設定ならスキップ
    if (message.type === 'thinking' && !state.showThinking) {
        messageDiv.style.display = 'none';
    }

    messageDiv.innerHTML = renderMessageHtml(message);
    container.appendChild(messageDiv);

    // メッセージ数制限
    while (container.children.length > CONFIG.messageBufferSize) {
        container.removeChild(container.firstChild);
    }

    // 自動スクロール
    if (state.isAutoScroll) {
        scrollToBottom();
    }
}

function renderMessageHtml(message) {
    const timestamp = message.timestamp ? formatTime(message.timestamp) : '';
    const showTime = state.showTimestamp && timestamp;

    if (message.type === 'thinking') {
        return `
            ${showTime ? `<span class="message-timestamp">${escapeHtml(timestamp)}</span>` : ''}
            <span class="message-agent thinking-agent">${escapeHtml(message.agent)}</span>
            <span class="message-label">[思考]</span>
            <span class="message-content">${escapeHtml(message.content)}</span>
        `;
    }

    return `
        ${showTime ? `<span class="message-timestamp">${escapeHtml(timestamp)}</span>` : ''}
        <span class="message-agent">${escapeHtml(message.from || '?')}</span>
        <span class="message-arrow">→</span>
        <span class="message-to">${escapeHtml(message.to || '?')}</span>
        <span class="message-type">[${message.type}]</span>
        <span class="message-content">${escapeHtml(message.content)}</span>
    `;
}

function updateConnectionStatus(status) {
    const statusDiv = document.getElementById('connection-status');
    const statusText = statusDiv.querySelector('.status-text');

    statusDiv.className = `connection-status status-${status}`;

    const labels = {
        connected: '接続中',
        disconnected: '切断中',
        connecting: '接続中...',
    };

    statusText.textContent = labels[status] || status;
}

function updateClusterName(name) {
    const nameSpan = document.getElementById('cluster-name');
    if (nameSpan) {
        nameSpan.textContent = `クラスタ: ${escapeHtml(name)}`;
    }
}

function updateMessageStats() {
    const countDiv = document.getElementById('message-count');
    countDiv.textContent = `${state.messageCount.total}件`;
}

// ============================================================================
// ユーティリティ関数
// ============================================================================

function formatTime(isoString) {
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
        return isoString;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    const container = document.getElementById('messages');
    container.scrollTop = container.scrollHeight;
}

// ============================================================================
// 通知/モーダル
// ============================================================================

function showNotification(message, type = 'info') {
    const notification = document.getElementById('error-notification');
    const messageSpan = notification.querySelector('.notification-message');

    notification.className = `notification ${type}`;
    messageSpan.textContent = message;
    notification.classList.remove('hidden');

    // 3秒後に自動非表示
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

function hideNotification() {
    const notification = document.getElementById('error-notification');
    notification.classList.add('hidden');
}

function showReconnectModal(attempt) {
    const modal = document.getElementById('reconnect-modal');
    const progress = document.getElementById('reconnect-progress');
    const text = document.getElementById('reconnect-text');

    const percent = (attempt / CONFIG.maxReconnectAttempts) * 100;
    progress.style.width = `${percent}%`;
    text.textContent = `再接続中... (${attempt}/${CONFIG.maxReconnectAttempts})`;

    modal.classList.remove('hidden');
}

function hideReconnectModal() {
    const modal = document.getElementById('reconnect-modal');
    modal.classList.add('hidden');
}

function showConfirmModal(title, message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const titleEl = document.getElementById('confirm-title');
    const messageEl = document.getElementById('confirm-message');
    const okBtn = document.getElementById('confirm-ok');
    const cancelBtn = document.getElementById('confirm-cancel');

    titleEl.textContent = title;
    messageEl.textContent = message;

    state.pendingConfirm = onConfirm;

    modal.classList.remove('hidden');

    // ボタンハンドラーを設定
    okBtn.onclick = () => {
        modal.classList.add('hidden');
        if (state.pendingConfirm) {
            state.pendingConfirm();
            state.pendingConfirm = null;
        }
    };

    cancelBtn.onclick = () => {
        modal.classList.add('hidden');
        state.pendingConfirm = null;
    };
}

function hideConfirmModal() {
    const modal = document.getElementById('confirm-modal');
    modal.classList.add('hidden');
    state.pendingConfirm = null;
}

async function restartCluster() {
    showConfirmModal(
        'クラスタ再起動',
        'クラスタを再起動します。よろしいですか？',
        async () => {
            try {
                const response = await fetch(`${CONFIG.apiUrl}/cluster/restart`, {
                    method: 'POST',
                });
                const data = await response.json();
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(data.message || 'クラスタを再起動しました', 'success');
                }
            } catch (error) {
                showNotification('クラスタの再起動に失敗しました', 'error');
                console.error('Restart error:', error);
            }
        }
    );
}

async function shutdownCluster() {
    showConfirmModal(
        'クラスタ停止',
        'クラスタを完全に停止します。この操作は取り消せません。よろしいですか？',
        async () => {
            try {
                const response = await fetch(`${CONFIG.apiUrl}/cluster/shutdown`, {
                    method: 'POST',
                });
                const data = await response.json();
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(data.message || 'クラスタを停止しました', 'success');
                }
            } catch (error) {
                showNotification('クラスタの停止に失敗しました', 'error');
                console.error('Shutdown error:', error);
            }
        }
    );
}

// ============================================================================
// イベントリスナー
// ============================================================================

function setupEventListeners() {
    // 思考ログ表示切り替え
    document.getElementById('show-thinking').addEventListener('change', (e) => {
        state.showThinking = e.target.checked;
        document.querySelectorAll('.message-thinking').forEach(el => {
            el.style.display = state.showThinking ? '' : 'none';
        });
    });

    // 自動スクロール切り替え
    document.getElementById('auto-scroll').addEventListener('change', (e) => {
        state.isAutoScroll = e.target.checked;
    });

    // タイムスタンプ表示切り替え
    document.getElementById('show-timestamp').addEventListener('change', (e) => {
        state.showTimestamp = e.target.checked;
        document.querySelectorAll('.message-timestamp').forEach(el => {
            el.style.display = state.showTimestamp ? '' : 'none';
        });
    });

    // ログクリア
    document.getElementById('clear-messages').addEventListener('click', () => {
        document.getElementById('messages').innerHTML = '';
        state.messages = [];
        state.messageCount = { total: 0, thinking: 0, task: 0, result: 0 };
        updateMessageStats();
    });

    // エクスポート
    document.getElementById('export-messages').addEventListener('click', () => {
        const messages = Array.from(document.querySelectorAll('.message:not(.message-thinking [style*="display: none"])'));
        const data = messages.map(el => el.textContent).join('\n');
        const blob = new Blob([data], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `messages-${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // エージェント更新
    document.getElementById('refresh-agents').addEventListener('click', () => {
        dashboardClient.fetchAgents();
    });

    // クラスタ再起動
    document.getElementById('restart-cluster').addEventListener('click', restartCluster);

    // クラスト停止
    document.getElementById('shutdown-cluster').addEventListener('click', shutdownCluster);

    // 通知を閉じる
    document.querySelector('.notification-close').addEventListener('click', hideNotification);

    // Ping送信（30秒ごと）
    setInterval(() => {
        if (dashboardClient.ws && dashboardClient.ws.readyState === WebSocket.OPEN) {
            dashboardClient.send({ type: 'ping' });
        }
    }, 30000);
}

// ============================================================================
// 初期化
// ============================================================================

let dashboardClient;

function init() {
    console.log('orchestrator-cc Dashboard 初期化...');

    // イベントリスナー設定
    setupEventListeners();

    // WebSocketクライアント起動
    dashboardClient = new DashboardClient();
    dashboardClient.connect();

    console.log('orchestrator-cc Dashboard 起動完了');
}

// DOM読み込み完了後に初期化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// ページアンロード時にWebSocketを切断
window.addEventListener('beforeunload', () => {
    if (dashboardClient) {
        dashboardClient.disconnect();
    }
});
