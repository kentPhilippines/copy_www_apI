const LogsModule = {
    async init(app) {
        this.initControls(app);
        await this.loadLogs(app);
    },

    initControls(app) {
        const refreshBtn = document.getElementById('refreshLogsBtn');
        const autoScrollBtn = document.getElementById('autoScrollBtn');
        const logTypeSelect = document.getElementById('logType');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadLogs(app));
        }
        if (autoScrollBtn) {
            autoScrollBtn.addEventListener('click', () => this.toggleAutoScroll());
        }
        if (logTypeSelect) {
            logTypeSelect.addEventListener('change', () => this.loadLogs(app));
        }
    },

    async loadLogs(app) {
        // 原loadLogs方法的内容
    },

    toggleAutoScroll() {
        // 原toggleAutoScroll方法的内容
    }
};

export default LogsModule; 