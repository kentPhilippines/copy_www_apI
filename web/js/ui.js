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

function showDialog(title, content, options = {}) {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'dialog-overlay';
        
        const width = options.width || 'auto';
        const buttons = options.buttons || ['确定', '取消'];

        dialog.innerHTML = `
            <div class="dialog" style="width: ${width}">
                <div class="dialog-header">
                    <h3>${title}</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="dialog-content"></div>
                ${buttons.length > 0 ? `
                    <div class="dialog-footer">
                        ${buttons.map(btn => `
                            <button class="btn ${btn === '取消' ? 'btn-secondary' : 'btn-primary'}">${btn}</button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;

        // 添加内容
        dialog.querySelector('.dialog-content').appendChild(
            content instanceof Element ? content : document.createTextNode(content)
        );

        // 添加事件处理
        dialog.querySelector('.close-btn').onclick = () => {
            dialog.remove();
            resolve(false);
        };

        // 按钮事件
        const footer = dialog.querySelector('.dialog-footer');
        if (footer) {
            footer.querySelectorAll('.btn').forEach(btn => {
                btn.onclick = () => {
                    dialog.remove();
                    resolve(btn.textContent);
                };
            });
        }

        document.body.appendChild(dialog);
        return dialog;
    });
}