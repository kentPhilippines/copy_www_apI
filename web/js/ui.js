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
        const statusElement = document.getElementById('nginx-status');
        statusElement.innerHTML = `
            <span class="status-badge ${status.running ? 'status-running' : 'status-stopped'}">
                ${status.running ? '运行中' : '已停止'}
            </span>
            <span>版本: ${status.version || 'Unknown'}</span>
        `;
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