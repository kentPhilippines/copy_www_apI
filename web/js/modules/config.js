const ConfigModule = {
    async init(app) {
        this.initButtons(app);
        await this.updateStatus(app);
        setInterval(() => this.updateStatus(app), 10000);
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
        const statusBadge = document.getElementById('nginxRunningStatus');
        if (statusBadge) {
            statusBadge.className = `status-badge ${status.running ? 'running' : 'stopped'}`;
            statusBadge.textContent = status.running ? '运行中' : '已停止';
        }

        const workerCount = document.getElementById('workerCount');
        if (workerCount) {
            workerCount.textContent = status.processes.length;
        }

        const connectionCount = document.getElementById('connectionCount');
        if (connectionCount) {
            const totalConnections = status.processes.reduce((sum, p) => sum + p.connections, 0);
            connectionCount.textContent = totalConnections;
        }

        const versionInfo = document.getElementById('nginxVersion');
        if (versionInfo) {
            versionInfo.textContent = status.version;
        }

        const processTable = document.getElementById('processTable');
        if (processTable) {
            const tbody = processTable.querySelector('tbody');
            tbody.innerHTML = status.processes.map(proc => `
                <tr>
                    <td>${proc.pid}</td>
                    <td>${proc.type}</td>
                    <td>${proc.status}</td>
                    <td>${proc.cpu}%</td>
                    <td>${utils.formatFileSize(proc.memory)}</td>
                    <td>${proc.connections}</td>
                </tr>
            `).join('');
        }
    },

    async testConfig(app) {
        try {
            const result = document.getElementById('configTestResult');
            result.style.display = 'block';
            result.className = 'config-test-result';
            result.textContent = '测试配置中...';

            const response = await api.testConfig();
            
            if (response.success) {
                result.className = 'config-test-result success';
                result.textContent = '配置测试通过！';
            } else {
                result.className = 'config-test-result error';
                result.textContent = response.message;
            }
        } catch (error) {
            app.showError('测试配置失败: ' + error.message);
        }
    },

    async reloadConfig(app) {
        if (!confirm('确定要重载Nginx配置吗？')) return;
        
        try {
            const response = await api.reloadConfig();
            if (response.success) {
                app.showSuccess('配置重载成功');
                await this.updateStatus(app);
            } else {
                app.showError(response.message);
            }
        } catch (error) {
            app.showError('重载配置失败: ' + error.message);
        }
    },

    async restartNginx(app) {
        if (!confirm('确定要重启Nginx服务吗？这可能会导致短暂的服务中断。')) return;
        
        try {
            const response = await api.restartNginx();
            if (response.success) {
                app.showSuccess('Nginx重启成功');
                await this.updateStatus(app);
            } else {
                app.showError(response.message);
            }
        } catch (error) {
            app.showError('重启Nginx失败: ' + error.message);
        }
    }
};

window.ConfigModule = ConfigModule; 