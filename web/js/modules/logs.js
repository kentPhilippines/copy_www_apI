const LogsModule = {
    async init(app) {
        this.app = app;
        this.autoScroll = true;
        this.ws = null;
        this.initControls(app);
        await this.loadLogs(app);
    },

    initControls(app) {
        const refreshBtn = document.getElementById('refreshLogsBtn');
        const autoScrollBtn = document.getElementById('autoScrollBtn');
        const logTypeSelect = document.getElementById('logType');
        const logContent = document.getElementById('logContent');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadLogs(app));
        }

        if (autoScrollBtn) {
            autoScrollBtn.addEventListener('click', () => {
                this.autoScroll = !this.autoScroll;
                autoScrollBtn.classList.toggle('active', this.autoScroll);
            });
        }

        if (logTypeSelect) {
            logTypeSelect.addEventListener('change', () => {
                this.closeWebSocket();
                this.loadLogs(app);
            });
        }

        if (logContent) {
            logContent.addEventListener('scroll', () => {
                const { scrollTop, scrollHeight, clientHeight } = logContent;
                this.autoScroll = Math.abs(scrollHeight - clientHeight - scrollTop) < 1;
                if (autoScrollBtn) {
                    autoScrollBtn.classList.toggle('active', this.autoScroll);
                }
            });
        }
    },

    async loadLogs(app) {
        const logContent = document.getElementById('logContent');
        const logType = document.getElementById('logType').value;
        const lines = document.getElementById('logLines').value;

        try {
            const logs = await api.getLogs(logType, lines);
            logContent.textContent = logs.join('\n');
            
            if (this.autoScroll) {
                logContent.scrollTop = logContent.scrollHeight;
            }

            // 启动WebSocket连接
            this.startWebSocket(logType);

        } catch (error) {
            app.showError('加载日志失败: ' + error.message);
        }
    },

    startWebSocket(logType) {
        this.closeWebSocket();

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${api.baseURL.split('/api/')[0]}/api/v1/nginx/logs/ws/${logType}`;
        
        this.ws = new WebSocket(wsUrl);
        const logContent = document.getElementById('logContent');

        this.ws.onmessage = (event) => {
            logContent.textContent += event.data + '\n';
            if (this.autoScroll) {
                logContent.scrollTop = logContent.scrollHeight;
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.app.showError('日志连接失败');
        };

        this.ws.onclose = () => {
            console.log('WebSocket连接已关闭');
            // 5秒后尝试重连
            setTimeout(() => this.startWebSocket(logType), 5000);
        };
    },

    closeWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
};

window.LogsModule = LogsModule; 