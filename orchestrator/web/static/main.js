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
    heartbeatInterval: 15000,  // 15秒ごとにping送信（接続維持のため短縮）
    heartbeatTimeout: 30000,    // 30秒 pongがない場合、接続切れと判断
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
    // システムログ用状態
    systemLogs: [],
    systemLogAutoScroll: true,
    // チーム監視用状態
    teams: new Map(),
    selectedTeam: null,
    teamMessages: [],
    teamTasks: [],
    thinkingLogs: [],
};

// ============================================================================
// WebSocketクライアント
// ============================================================================

class DashboardClient {
    constructor() {
        this.ws = null;
        this.messageHandlers = new Map();
        this.heartbeatTimer = null;
        this.lastPongTime = null;
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

            // heartbeatを開始
            this.startHeartbeat();

            // システムログに接続完了を記録
            addSystemLog('success', 'ダッシュボードに接続しました');

            // 初期データをリクエスト
            this.send({
                type: 'subscribe',
                channels: ['messages', 'thinking', 'status']
            });

            // エージェント状態をリクエスト
            this.fetchAgents();
            // 過去ログをリクエスト
            this.fetchRecentMessages();
            // チーム一覧をリクエスト
            this.fetchTeams();
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
            this.stopHeartbeat();
            updateConnectionStatus('disconnected');

            // システムログに切断を記録
            addSystemLog('warning', `サーバーとの接続が切断されました (code: ${event.code})`);

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
        this.on('connected', handleConnectedMessage);
        this.on('subscribed', handleSubscribedMessage);
        this.on('status', handleStatusMessage);
        this.on('message', handleAgentMessage);
        this.on('thinking', handleThinkingMessage);
        this.on('agents', handleAgentsMessage);
        this.on('error', handleErrorMessage);
        this.on('pong', handlePongMessage);
        this.on('system_log', handleSystemLogMessage);
        this.on('cluster_event', handleClusterEventMessage);
        // チーム監視用ハンドラー
        this.on('team_created', handleTeamCreatedMessage);
        this.on('team_deleted', handleTeamDeletedMessage);
        this.on('team_updated', handleTeamUpdatedMessage);
        this.on('team_message', handleTeamMessage);
        this.on('thinking_log', handleThinkingLogMessage);
        this.on('tasks_updated', handleTasksUpdatedMessage);
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
            const response = await fetch(`${CONFIG.apiUrl}/agents`);
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
            // 404はクラスタ未起動時の正常な状態、無視
            else if (response.status === 404) {
                console.debug('クラスタメッセージエンドポイントなし（Agent Teamsモード）');
            }
        } catch (error) {
            console.error('過去ログ取得エラー:', error);
        }
    }

    async fetchTeams() {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/teams`);
            if (response.ok) {
                const data = await response.json();
                const teams = data.teams || [];
                teams.forEach(team => {
                    state.teams.set(team.name, team);
                });
                updateTeamSelector();
            }
        } catch (error) {
            console.error('チーム一覧取得エラー:', error);
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
        this.stopHeartbeat();
        if (state.reconnectTimer) {
            clearTimeout(state.reconnectTimer);
        }
        if (this.ws) {
            this.ws.onclose = null;
            this.ws.close();
        }
    }

    startHeartbeat() {
        this.stopHeartbeat();  // 既存のタイマーをクリア
        this.lastPongTime = Date.now();

        this.heartbeatTimer = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                // ping送信
                this.send({ type: 'ping', timestamp: Date.now() });

                // タイムアウトチェック
                const timeSinceLastPong = Date.now() - this.lastPongTime;
                if (timeSinceLastPong > CONFIG.heartbeatTimeout) {
                    console.warn('heartbeat timeout - 接続が切れた可能性があります');
                    this.ws.close();  // 接続を閉じて再接続をトリガー
                }
            }
        }, CONFIG.heartbeatInterval);

        console.log(`heartbeat開始 (${CONFIG.heartbeatInterval}ms間隔)`);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
            console.log('heartbeat停止');
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

    // アイドル通知をフィルタリング（ノイズ軽減）
    if (type === 'idle_notification') {
        return;
    }

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

    // 要約カードを更新
    updateSummaryCards();
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

    // 要約カードを更新
    updateSummaryCards();
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

    // 要約カードを更新
    updateSummaryCards();
}

function handleErrorMessage(message) {
    showNotification(message.content || 'エラーが発生しました', 'error');
}

function handlePongMessage(message) {
    // Pingに対するPong応答
    console.debug('Pong received');
    if (typeof dashboardClient !== 'undefined' && dashboardClient) {
        dashboardClient.lastPongTime = Date.now();
    }
}

function handleConnectedMessage(message) {
    // 接続確立応答
    console.debug('Connected:', message.message);
}

function handleSubscribedMessage(message) {
    // 購読確定応答
    console.debug('Subscribed:', message.channels);
}

function handleSystemLogMessage(message) {
    const { timestamp, level, content } = message;
    addSystemLogToDom({
        timestamp,
        level: level || 'info',
        content,
    });
}

function handleClusterEventMessage(message) {
    const { event, data } = message;
    let level = 'info';
    let content = '';

    switch (event) {
        case 'cluster_start':
            level = 'success';
            content = 'クラスタを起動しました';
            break;
        case 'cluster_stop':
            level = 'warning';
            content = 'クラスタを停止しました';
            break;
        case 'cluster_restart_start':
            level = 'info';
            content = 'クラスタの再起動を開始しました...';
            break;
        case 'cluster_restart_complete':
            level = 'success';
            content = 'クラスタの再起動が完了しました';
            break;
        case 'cluster_restart_failed':
            level = 'error';
            content = `クラスタの再起動に失敗しました: ${data?.error || '不明なエラー'}`;
            break;
        case 'agent_started':
            level = 'success';
            content = `エージェント ${data?.agent} を起動しました`;
            break;
        case 'agent_stopped':
            level = 'warning';
            content = `エージェント ${data?.agent} を停止しました`;
            break;
        case 'agent_error':
            level = 'error';
            content = `エージェント ${data?.agent} でエラーが発生: ${data?.error || '不明なエラー'}`;
            break;
        default:
            level = 'info';
            content = `クラスタイベント: ${event}`;
    }

    addSystemLogToDom({
        timestamp: new Date().toISOString(),
        level,
        content,
    });
}

// ============================================================================
// チーム監視メッセージハンドラー
// ============================================================================

function handleTeamCreatedMessage(message) {
    const { teamName, team } = message;
    state.teams.set(teamName, team);
    updateTeamSelector();
    addSystemLog('success', `チームが作成されました: ${teamName}`);
}

function handleTeamDeletedMessage(message) {
    const { teamName } = message;
    state.teams.delete(teamName);
    if (state.selectedTeam === teamName) {
        state.selectedTeam = null;
    }
    updateTeamSelector();
    addSystemLog('warning', `チームが削除されました: ${teamName}`);
}

function handleTeamUpdatedMessage(message) {
    const { teamName, team } = message;
    state.teams.set(teamName, team);
    addSystemLog('info', `チームが更新されました: ${teamName}`);
}

function handleTeamMessage(message) {
    const { teamName, message: msg } = message;

    if (state.selectedTeam !== teamName) {
        return;
    }

    // アイドル通知はフィルタリング
    if (msg.message_type === 'idle_notification' || msg.type === 'idle_notification') {
        return;
    }

    // contentがJSONの場合はパースして整形
    let processedMsg = { ...msg };
    if (msg.content) {
        try {
            // JSON文字列の場合はパース
            if (msg.content.trim().startsWith('{')) {
                const contentData = JSON.parse(msg.content);
                // task_assignmentメッセージを整形
                if (contentData.type === 'task_assignment') {
                    processedMsg.content = `📋 タスク割り当て: #${contentData.taskId}「${contentData.subject}」`;
                    processedMsg.rawData = contentData;
                }
                // idle_notificationはスキップ
                else if (contentData.type === 'idle_notification') {
                    return;
                }
                // その他のJSONは簡略表示
                else {
                    processedMsg.content = `[${contentData.type || 'message'}]`;
                    processedMsg.rawData = contentData;
                }
            }
        } catch (e) {
            // JSONでない場合はそのまま
        }
    }

    state.teamMessages.push(processedMsg);
    addTeamMessageToDom(processedMsg);
    updateMessageStats();

    // 要約カードを更新
    updateSummaryCards();
}

function handleThinkingLogMessage(message) {
    const { teamName, log } = message;

    if (state.selectedTeam !== teamName) {
        return;
    }

    state.thinkingLogs.push(log);
    addThinkingLogToDom(log);
}

function handleTasksUpdatedMessage(message) {
    const { teamName, tasks } = message;
    addSystemLog('info', `タスクが更新されました: ${teamName} (${tasks.length}件)`);

    // 要約カードを更新
    updateSummaryCards();
}

// ============================================================================
// チーム監視UI
// ============================================================================

function updateTeamSelector() {
    const select = document.getElementById('team-select');
    if (!select) return;

    const currentValue = select.value;
    select.innerHTML = '<option value="">-- チームを選択 --</option>';

    state.teams.forEach((team, teamName) => {
        const option = document.createElement('option');
        option.value = teamName;
        option.textContent = teamName;
        select.appendChild(option);
    });

    // 選択を復元
    if (currentValue && state.teams.has(currentValue)) {
        select.value = currentValue;
    }
}

function addTeamMessageToDom(message) {
    const container = document.getElementById('messages');
    if (!container) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-team';

    const timestamp = message.timestamp ? formatTime(message.timestamp) : '';
    const showTime = state.showTimestamp && timestamp;

    messageDiv.innerHTML = `
        ${showTime ? `<span class="message-timestamp">${escapeHtml(timestamp)}</span>` : ''}
        <span class="message-agent">${escapeHtml(message.sender || '?')}</span>
        <span class="message-arrow">→</span>
        <span class="message-to">${escapeHtml(message.recipient || '全体')}</span>
        <span class="message-content">${formatMessageContent(message.content, message.message_type || 'team')}</span>
    `;

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

function addThinkingLogToDom(log) {
    const container = document.getElementById('thinking-logs');
    if (!container) return;

    const logDiv = document.createElement('div');
    logDiv.className = `thinking-log thinking-${log.category}`;

    const emotionIcons = {
        confusion: '🤔',
        satisfaction: '😊',
        focus: '🎯',
        concern: '⚠️',
        neutral: '',
    };

    // timestampがnullの場合は空文字に
    const timestamp = log.timestamp ? formatTime(log.timestamp) : '';
    const emotionIcon = emotionIcons[log.emotion] || '';

    // タスク詳細がある場合は追加表示
    const taskDetails = log.taskDetails
        ? `<span class="task-status-badge">${escapeHtml(log.taskDetails.status)}</span>`
        : '';

    logDiv.innerHTML = `
        ${timestamp ? `<span class="thinking-time">${escapeHtml(timestamp)}</span>` : ''}
        <span class="thinking-agent">${escapeHtml(log.agentName)}</span>
        ${taskDetails}
        ${emotionIcon ? `<span class="thinking-emotion">${emotionIcon}</span>` : ''}
        <span class="thinking-content">${escapeHtml(log.content)}</span>
    `;

    container.appendChild(logDiv);

    // ログ数制限
    while (container.children.length > 500) {
        container.removeChild(container.firstChild);
    }

    // 自動スクロール
    if (state.isAutoScroll) {
        container.scrollTop = container.scrollHeight;
    }
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
        <span class="message-content">${formatMessageContent(message.content, message.type)}</span>
    `;
}

// メッセージコンテンツを整形する
function formatMessageContent(content, messageType) {
    // JSON文字列の場合は整形して表示
    try {
        if (content && typeof content === 'string' && content.trim().startsWith('{')) {
            const parsed = JSON.parse(content);

            // idle_notificationは空文字列にして非表示
            if (parsed.type === 'idle_notification') {
                return '<span class="idle-notification"></span>';
            }

            // task_assignmentメッセージの場合は特別に整形
            if (parsed.type === 'task_assignment') {
                return `
                    <div class="task-assignment">
                        <strong>📋 タスク割り当て:</strong>
                        <div class="task-details">
                            <div><strong>ID:</strong> #${escapeHtml(parsed.taskId || '?')}</div>
                            <div><strong>件名:</strong> ${escapeHtml(parsed.subject || '')}</div>
                        </div>
                    </div>
                `;
            }
            // その他のJSONは整形して表示
            const formatted = JSON.stringify(parsed, null, 2);
            return `<pre class="json-content">${escapeHtml(formatted)}</pre>`;
        }
    } catch (e) {
        // JSON解析エラーの場合はそのまま表示
    }
    return escapeHtml(content);
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

function scrollToSystemLogBottom() {
    const container = document.getElementById('system-log');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function addSystemLogToDom(logEntry) {
    const container = document.getElementById('system-log');
    if (!container) return;

    const entryDiv = document.createElement('div');
    entryDiv.className = `system-log-entry ${logEntry.level}`;

    const icons = {
        info: 'ℹ️',
        success: '✅',
        warning: '⚠️',
        error: '❌',
    };

    const time = logEntry.timestamp ? formatTime(logEntry.timestamp) : '';
    const icon = icons[logEntry.level] || icons.info;

    entryDiv.innerHTML = `
        <span class="system-log-icon">${icon}</span>
        <span class="system-log-time">${escapeHtml(time)}</span>
        <span class="system-log-level">${logEntry.level.toUpperCase()}</span>
        <span class="system-log-message">${escapeHtml(logEntry.content)}</span>
    `;

    container.appendChild(entryDiv);

    // ログ数制限
    while (container.children.length > 500) {
        container.removeChild(container.firstChild);
    }

    // 自動スクロール
    if (state.systemLogAutoScroll) {
        scrollToSystemLogBottom();
    }

    // 要約カードを更新
    updateSummaryCards();
}

function addSystemLog(level, content) {
    addSystemLogToDom({
        timestamp: new Date().toISOString(),
        level,
        content,
    });
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
    // 確認モーダルを表示
    showConfirmModal(
        'クラスタ再起動',
        'クラスタを再起動します。よろしいですか？',
        async () => {
            const btn = document.getElementById('restart-cluster');
            const originalContent = btn.innerHTML;

            // ボタンを無効化してスピナー表示
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span><span>再起動中...</span>';

            // システムログに記録
            addSystemLog('info', 'クラスタの再起動を開始します...');

            try {
                const response = await fetch(`${CONFIG.apiUrl}/cluster/restart`, {
                    method: 'POST',
                });
                const data = await response.json();

                if (data.error) {
                    showNotification(data.error, 'error');
                    addSystemLog('error', `再起動失敗: ${data.error}`);
                } else {
                    showNotification(data.message || 'クラスタを再起動しました', 'success');
                    addSystemLog('success', data.message || 'クラスタの再起動が完了しました');
                    // エージェント状態を更新
                    if (dashboardClient) {
                        setTimeout(() => dashboardClient.fetchAgents(), 2000);
                    }
                }
            } catch (error) {
                const errorMsg = 'クラスタの再起動に失敗しました';
                showNotification(errorMsg, 'error');
                addSystemLog('error', `${errorMsg}: ${error.message}`);
                console.error('Restart error:', error);
            } finally {
                // ボタンを元に戻す
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        }
    );
}

async function shutdownCluster() {
    // 確認モーダルを表示
    showConfirmModal(
        'クラスタ停止',
        'クラスタを完全に停止します。この操作は取り消せません。よろしいですか？',
        async () => {
            const btn = document.getElementById('shutdown-cluster');
            const originalContent = btn.innerHTML;

            // ボタンを無効化してスピナー表示
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span><span>停止中...</span>';

            // システムログに記録
            addSystemLog('warning', 'クラスタの停止を開始します...');

            try {
                const response = await fetch(`${CONFIG.apiUrl}/cluster/shutdown`, {
                    method: 'POST',
                });
                const data = await response.json();

                if (data.error) {
                    showNotification(data.error, 'error');
                    addSystemLog('error', `停止失敗: ${data.error}`);
                } else {
                    showNotification(data.message || 'クラスタを停止しました', 'success');
                    addSystemLog('success', data.message || 'クラスタの停止が完了しました');
                    // エージェント状態を更新
                    if (dashboardClient) {
                        setTimeout(() => dashboardClient.fetchAgents(), 1000);
                    }
                }
            } catch (error) {
                const errorMsg = 'クラスタの停止に失敗しました';
                showNotification(errorMsg, 'error');
                addSystemLog('error', `${errorMsg}: ${error.message}`);
                console.error('Shutdown error:', error);
            } finally {
                // ボタンを元に戻す
                btn.disabled = false;
                btn.innerHTML = originalContent;
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

    // クラスタ停止
    document.getElementById('shutdown-cluster').addEventListener('click', shutdownCluster);

    // システムログ自動スクロール切り替え
    document.getElementById('system-log-auto-scroll').addEventListener('change', (e) => {
        state.systemLogAutoScroll = e.target.checked;
    });

    // システムログクリア
    document.getElementById('clear-system-log').addEventListener('click', () => {
        const container = document.getElementById('system-log');
        if (container) {
            container.innerHTML = '';
            state.systemLogs = [];
        }
    });

    // 通知を閉じる
    document.querySelector('.notification-close').addEventListener('click', hideNotification);

    // エージェントパネルの折りたたみ
    const toggleAgentsBtn = document.getElementById('toggle-agents');
    const agentPanel = document.getElementById('agent-panel');
    if (toggleAgentsBtn && agentPanel) {
        toggleAgentsBtn.addEventListener('click', () => {
            agentPanel.classList.toggle('collapsed');
            // 折りたたみ状態をローカルストレージに保存
            localStorage.setItem('agentPanelCollapsed', agentPanel.classList.contains('collapsed'));
        });

        // ローカルストレージから状態を復元
        const savedState = localStorage.getItem('agentPanelCollapsed');
        if (savedState === 'true') {
            agentPanel.classList.add('collapsed');
        }
    }

    // チーム選択
    const teamSelect = document.getElementById('team-select');
    if (teamSelect) {
        teamSelect.addEventListener('change', async (e) => {
            state.selectedTeam = e.target.value || null;

            // チームが選択されたらデータを取得
            if (state.selectedTeam) {
                await loadTeamData(state.selectedTeam);
            } else {
                // 選択解除時はクリア
                document.getElementById('messages').innerHTML = '';
                document.getElementById('thinking-logs').innerHTML = '';
                state.teamMessages = [];
                state.thinkingLogs = [];
            }
        });
    }

    // 思考ログエージェントフィルター
    const thinkingFilter = document.getElementById('thinking-agent-filter');
    if (thinkingFilter) {
        thinkingFilter.addEventListener('change', (e) => {
            filterThinkingLogs(e.target.value);
        });
    }
}

// チームデータの読み込み
async function loadTeamData(teamName) {
    try {
        // メッセージを取得
        const messagesResponse = await fetch(`${CONFIG.apiUrl}/teams/${teamName}/messages`);
        if (messagesResponse.ok) {
            const data = await messagesResponse.json();
            const rawMessages = data.messages || [];

            // メッセージをフィルタリング・整形
            state.teamMessages = rawMessages
                .filter(msg => msg.message_type !== 'idle_notification' && msg.type !== 'idle_notification')
                .map(msg => {
                    // contentがJSONの場合はパースして整形
                    if (msg.content && msg.content.trim().startsWith('{')) {
                        try {
                            const contentData = JSON.parse(msg.content);
                            if (contentData.type === 'task_assignment') {
                                return {
                                    ...msg,
                                    content: `📋 タスク割り当て: #${contentData.taskId}「${contentData.subject}」`,
                                    rawData: contentData
                                };
                            }
                        } catch (e) {
                            // パース失敗は元のcontentを使用
                        }
                    }
                    return msg;
                });

            document.getElementById('messages').innerHTML = '';
            state.teamMessages.forEach(msg => addTeamMessageToDom(msg));

            // メッセージ数を更新
            state.messageCount.total = state.teamMessages.length;
        }

        // タスクを取得（タスクボードとタイムラインに表示）
        const tasksResponse = await fetch(`${CONFIG.apiUrl}/teams/${teamName}/tasks`);
        if (tasksResponse.ok) {
            const data = await tasksResponse.json();
            const tasks = data.tasks || [];

            // タスクを保存
            state.teamTasks = tasks;

            // タスクボードを更新
            renderTaskBoard(tasks);

            // タイムラインを更新
            renderTimeline(teamName, tasks, state.teamMessages);

            // タスク統計を更新
            updateTaskStats(tasks);
        }

        addSystemLog('success', `チームデータを読み込みました: ${teamName}`);

        // 要約カードを更新
        updateSummaryCards();
    } catch (error) {
        console.error('Team data load error:', error);
        addSystemLog('error', `チームデータの読み込みに失敗しました: ${error.message}`);
    }
}

// 思考ログエージェントフィルターの更新
function updateThinkingAgentFilter() {
    const filter = document.getElementById('thinking-agent-filter');
    if (!filter) return;

    // 既存のオプションをクリア（最初の要素は残す）
    while (filter.options.length > 1) {
        filter.remove(1);
    }

    // エージェント名を収集
    const agents = new Set();
    state.thinkingLogs.forEach(log => {
        if (log.agentName) {
            agents.add(log.agentName);
        }
    });

    // オプションを追加
    agents.forEach(agent => {
        const option = document.createElement('option');
        option.value = agent;
        option.textContent = agent;
        filter.appendChild(option);
    });
}

// 思考ログのフィルタリング
function filterThinkingLogs(agentName) {
    const container = document.getElementById('thinking-logs');
    if (!container) return;

    const logs = container.children;
    for (let i = 0; i < logs.length; i++) {
        const log = logs[i];
        const logAgent = log.querySelector('.thinking-agent');
        if (logAgent) {
            const shouldShow = !agentName || logAgent.textContent === agentName;
            log.style.display = shouldShow ? '' : 'none';
        }
    }
}

// ============================================================================
// タブ機能
// ============================================================================

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    const summaryCards = document.querySelectorAll('.summary-card');

    // タブボタンのクリックイベント
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // アクティブクラスの切り替え
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            tabPanels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === `tab-${targetTab}`) {
                    panel.classList.add('active');
                }
            });

            // 状態を保存
            localStorage.setItem('activeTab', targetTab);
        });
    });

    // 要約カードのクリックイベント（対応するタブを開く）
    summaryCards.forEach(card => {
        card.addEventListener('click', () => {
            const targetTab = card.dataset.targetTab;
            switchToTab(targetTab);
        });
    });

    // 保存された状態を復元
    const savedTab = localStorage.getItem('activeTab');
    if (savedTab) {
        switchToTab(savedTab);
    }
}

function switchToTab(tabName) {
    const button = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (button) {
        button.click();
    }
}

// ============================================================================
// 要約カード更新機能
// ============================================================================

function updateSummaryCards() {
    // エージェント状態
    const agentsArray = Array.from(state.agents.values());
    const activeAgents = agentsArray.filter(a => a.status === 'running').length;
    const totalAgents = agentsArray.length;
    const agentsValue = document.getElementById('summary-agents');
    if (agentsValue) {
        agentsValue.textContent = totalAgents > 0 ? `${activeAgents}/${totalAgents}` : '-';
    }

    // タスク状態
    const pending = state.teamTasks.filter(t => t.status === 'pending').length;
    const inProgress = state.teamTasks.filter(t => t.status === 'in_progress').length;
    const completed = state.teamTasks.filter(t => t.status === 'completed').length;
    const tasksValue = document.getElementById('summary-tasks');
    if (tasksValue) {
        tasksValue.textContent = state.teamTasks.length > 0
            ? `${pending}/${inProgress}/${completed}`
            : '-';
    }

    // メッセージ数
    const messagesValue = document.getElementById('summary-messages');
    if (messagesValue) {
        messagesValue.textContent = state.messageCount.total || 0;
    }

    // システム状態
    const hasErrors = state.systemLogs.some(l => l.level === 'error');
    const systemCard = document.querySelector('.system-card');
    const systemValue = document.getElementById('summary-system');
    if (systemValue && systemCard) {
        if (hasErrors) {
            systemValue.textContent = 'エラー';
            systemCard.classList.add('alert');
        } else {
            systemValue.textContent = '正常';
            systemCard.classList.remove('alert');
        }
    }
}

// ============================================================================
// 初期化
// ============================================================================

let dashboardClient;

function init() {
    console.log('orchestrator-cc Dashboard 初期化...');

    // タブ機能を初期化
    setupTabs();

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

// ============================================================================
// タスクボード機能 (Phase 2)
// ============================================================================

function renderTaskBoard(tasks) {
    const columns = {
        pending: document.getElementById('tasks-pending'),
        'in_progress': document.getElementById('tasks-in-progress'),
        completed: document.getElementById('tasks-completed')
    };

    // 各カラムをクリア
    Object.values(columns).forEach(col => {
        if (col) col.innerHTML = '';
    });

    // タスクをカラムに追加
    tasks.forEach(task => {
        const column = columns[task.status];
        if (!column) return;

        const card = document.createElement('div');
        card.className = 'task-card';
        card.dataset.taskId = task.taskId;

        const ownerName = task.owner ? task.owner.split('@')[0] : '未割り当て';

        // 依存関係表示
        let dependenciesHtml = '';
        if (task.blockedBy && task.blockedBy.length > 0) {
            dependenciesHtml = '<div class="task-card-dependencies">';
            dependenciesHtml += '<span>⚠️ 依存:</span>';
            task.blockedBy.forEach(depId => {
                dependenciesHtml += `<span class="task-dependency">#${depId}</span>`;
            });
            dependenciesHtml += '</div>';
        }

        card.innerHTML = `
            <div class="task-card-header">
                <span class="task-card-id">#${task.taskId}</span>
                <span class="task-card-owner">${ownerName}</span>
            </div>
            <div class="task-card-subject">${escapeHtml(task.subject)}</div>
            <div class="task-card-description">${escapeHtml((task.description || '').substring(0, 100))}${task.description && task.description.length > 100 ? '...' : ''}</div>
            ${dependenciesHtml}
        `;

        column.appendChild(card);
    });
}

function updateTaskStats(tasks) {
    const stats = {
        pending: tasks.filter(t => t.status === 'pending').length,
        'in_progress': tasks.filter(t => t.status === 'in_progress').length,
        completed: tasks.filter(t => t.status === 'completed').length
    };

    const pendingCount = document.getElementById('task-pending-count');
    const progressCount = document.getElementById('task-progress-count');
    const completedCount = document.getElementById('task-completed-count');

    if (pendingCount) pendingCount.textContent = `⏳ ${stats.pending}`;
    if (progressCount) progressCount.textContent = `🔄 ${stats['in_progress']}`;
    if (completedCount) completedCount.textContent = `✅ ${stats.completed}`;
}

// ============================================================================
// タイムライン機能 (Phase 3)
// ============================================================================

function renderTimeline(teamName, tasks, messages) {
    const timelineContainer = document.getElementById('timeline');
    if (!timelineContainer) return;

    timelineContainer.innerHTML = '<div class="timeline"></div>';
    const timeline = timelineContainer.querySelector('.timeline');

    // イベントを収集
    const events = [];

    // タスクイベント
    tasks.forEach(task => {
        const ownerName = task.owner ? task.owner.split('@')[0] : '未割り当て';
        events.push({
            type: 'task',
            status: task.status,
            agent: ownerName,
            content: `${task.subject}`,
            timestamp: 'タスク'  // タスクはタイムスタンプなし
        });
    });

    // メッセージイベント（最新10件）
    messages.slice(-10).forEach(msg => {
        if (msg.message_type !== 'idle_notification') {
            events.push({
                type: 'message',
                agent: msg.sender || '?',
                content: (msg.content || '').substring(0, 50),
                timestamp: msg.timestamp || ''
            });
        }
    });

    // タイムラインに表示
    events.forEach(event => {
        const item = document.createElement('div');
        item.className = `timeline-item ${event.type} ${event.status || ''}`;

        const timeLabel = event.timestamp && event.timestamp !== 'タスク'
            ? formatTime(event.timestamp)
            : (event.status === 'completed' ? '完了' : '進行中');

        item.innerHTML = `
            <div class="timeline-time">${escapeHtml(timeLabel)}</div>
            <div class="timeline-content">
                <div class="timeline-agent">${escapeHtml(event.agent)}</div>
                <div class="timeline-message">${escapeHtml(event.content)}</div>
            </div>
        `;

        timeline.appendChild(item);
    });
}
