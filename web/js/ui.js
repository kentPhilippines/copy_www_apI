class UI {
    static showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type} show`;
        
        setTimeout(() => {
            toast.className = 'toast';
        }, 3000);
    }

    static setLoading(element, isLoading) {
        if (isLoading) {
            element.disabled = true;
            element.innerHTML = '<span class="loading"></span> 加载中...';
        } else {
            element.disabled = false;
            element.innerHTML = element.getAttribute('data-original-text') || element.innerHTML;
        }
    }

    static updateNginxStatus(status) {
        // 更新运行状态
        const runningBadge = document.getElementById('nginx-running');
        runningBadge.className = `status-badge ${status.running ? 'status-running' : 'status-stopped'}`;
        runningBadge.textContent = status.running ? '运行中' : '已停止';

        // 更新版本和配置测试
        document.getElementById('nginx-version').textContent = status.version;
        document.getElementById('config-test-status').textContent = status.config_test;

        // 更新进程表
        const processTableBody = document.getElementById('process-table').getElementsByTagName('tbody')[0];
        processTableBody.innerHTML = status.processes.map(proc => `
            <tr>
                <td>${proc.pid}</td>
                <td><span class="status-badge ${proc.status === 'sleeping' ? 'status-running' : 'status-stopped'}">${proc.status}</span></td>
                <td>${proc.pid === status.processes[0].pid ? '主进程' : '工作进程'}</td>
            </tr>
        `).join('');

        // 更新资源使用
        document.getElementById('cpu-usage').textContent = `${status.resources.cpu_percent.toFixed(2)}%`;
        document.getElementById('memory-usage').textContent = `${status.resources.memory_percent.toFixed(2)}%`;
        document.getElementById('connection-count').textContent = status.resources.connections;
    }

    static createSitesTable(sites = []) {
        return `
            <table class="table">
                <thead>
                    <tr>
                        <th>域名</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${sites.map(site => `
                        <tr>
                            <td>${site.domain}</td>
                            <td>
                                <span class="status-badge ${site.status === 'active' ? 'status-running' : 'status-stopped'}">
                                    ${site.status}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-danger" onclick="deleteSite('${site.domain}')">删除</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
}