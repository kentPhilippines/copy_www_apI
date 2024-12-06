const ConfigModule = {
    async init(app) {
        this.initButtons(app);
        await this.updateStatus(app);
    },

    initButtons(app) {
        const testBtn = document.getElementById('testConfigBtn');
        const reloadBtn = document.getElementById('reloadConfigBtn');
        const restartBtn = document.getElementById('restartNginxBtn');

        if (testBtn) {
            testBtn.addEventListener('click', () => this.testConfig(app));
        }
        if (reloadBtn) {
            reloadBtn.addEventListener('click', () => this.reloadConfig(app));
        }
        if (restartBtn) {
            restartBtn.addEventListener('click', () => this.restartNginx(app));
        }
    },

    async updateStatus(app) {
        try {
            const status = await api.getNginxStatus();
            this.updateStatusDisplay(status);
        } catch (error) {
            app.showError('获取状态失败: ' + error.message);
        }
    },

    updateStatusDisplay(status) {
        // 原updateConfigStatus方法的内容
    },

    async testConfig(app) {
        // 原testConfig方法的内容
    },

    async reloadConfig(app) {
        // 原reloadConfig方法的内容
    },

    async restartNginx(app) {
        // 原restartNginx方法的内容
    }
};

export default ConfigModule; 