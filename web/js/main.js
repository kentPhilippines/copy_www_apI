const api = new API();

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    updateNginxStatus();
});

// 初始化应用
function initializeApp() {
    // 初始化API地址
    const apiUrlInput = document.getElementById('api-url');
    apiUrlInput.value = api.baseURL;
    apiUrlInput.addEventListener('change', (e) => {
        api.setBaseURL(e.target.value);
    });

    // 初始化页面切换
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = e.target.getAttribute('href').slice(1);
            switchPage(targetId);
        });
    });

    // 初始化表单提交
    initForms();

    // 初始化站点列表
    updateSitesList();

    // 每60秒更新一次站点列表
    setInterval(updateSitesList, 60000);
}

// 切换页面
function switchPage(pageId) {
    // 更新导航状态
    document.querySelectorAll('nav a').forEach(a => {
        a.classList.remove('active');
        if (a.getAttribute('href') === `#${pageId}`) {
            a.classList.add('active');
        }
    });

    // 更新页面显示
    document.querySelectorAll('.page').forEach(page => {
        page.style.display = page.id === pageId ? 'block' : 'none';
    });
}

// 初始化表单提交
function initForms() {
    // 站点添加表单
    const addSiteForm = document.getElementById('add-site-form');
    if (addSiteForm) {
        addSiteForm.addEventListener('submit', handleAddSite);
    }

    // SSL证书表单
    const sslForm = document.getElementById('ssl-form');
    if (sslForm) {
        sslForm.addEventListener('submit', handleSSLRequest);
    }
}

// 更新Nginx状态
async function updateNginxStatus() {
    try {
        const status = await api.getNginxStatus();
        updateStatusDisplay(status);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 更新状态显示
function updateStatusDisplay(status) {
    // 更新状态徽章
    const runningBadge = document.getElementById('nginx-running');
    if (runningBadge) {
        runningBadge.className = `status-badge ${status.running ? 'status-running' : 'status-stopped'}`;
        runningBadge.textContent = status.running ? '运行中' : '已停止';
    }

    // 更新版本和配置信息
    const elements = {
        'nginx-version': status.version,
        'config-test-status': status.config_test,
        'cpu-usage': `${status.resources.cpu_percent.toFixed(2)}%`,
        'memory-usage': `${status.resources.memory_percent.toFixed(2)}%`,
        'connection-count': status.resources.connections
    };

    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    // 更新进程表
    const processTableBody = document.getElementById('process-table')?.getElementsByTagName('tbody')[0];
    if (processTableBody) {
        processTableBody.innerHTML = status.processes.map(proc => `
            <tr>
                <td>${proc.pid}</td>
                <td><span class="status-badge ${proc.status === 'sleeping' ? 'status-running' : 'status-stopped'}">${proc.status}</span></td>
                <td>${proc.pid === status.processes[0].pid ? '主进程' : '工作进程'}</td>
            </tr>
        `).join('');
    }
}

// 显示提示信息
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

// 添加站点列表更新函数
async function updateSitesList() {
    try {
        const sites = await api.getSites();
        const tableBody = document.getElementById('sites-table-body');
        if (tableBody) {
            tableBody.innerHTML = sites.map(site => `
                <tr>
                    <td>${site.domain}</td>
                    <td>${site.port}</td>
                    <td>
                        <span class="status-badge ${site.ssl ? 'status-running' : 'status-stopped'}">
                            ${site.ssl ? '启用' : '禁用'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-danger" onclick="handleDeleteSite('${site.domain}')">删除</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        showToast('获取站点列表失败: ' + error.message, 'error');
    }
}

// 添加站点处理函数
async function handleAddSite(event) {
    event.preventDefault();
    const form = event.target;
    const data = {
        domain: form.domain.value,
        port: parseInt(form.port.value),
        ssl: form.ssl.checked
    };

    try {
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="loading"></span> 添加中...';

        const response = await api.createSite(data);
        showToast(response.message, 'success');
        form.reset();
        await updateSitesList();  // 更新站点列表
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = false;
        submitButton.textContent = '添加站点';
    }
}

// 添加删除站点处理函数
async function handleDeleteSite(domain) {
    if (confirm(`确定要删除站点 ${domain} 吗？`)) {
        try {
            const response = await api.deleteSite(domain);
            showToast(response.message, 'success');
            await updateSitesList();  // 更新站点列表
        } catch (error) {
            showToast(error.message, 'error');
        }
    }
}

// SSL证书申请处理函数
async function handleSSLRequest(event) {
    event.preventDefault();
    const form = event.target;
    const domain = form.domain.value;

    try {
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="loading"></span> 申请中...';

        const response = await api.createSSL(domain);
        showToast(response.message, 'success');
        form.reset();
        await updateSSLList();  // 如果有证书列表，更新它
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = false;
        submitButton.textContent = '申请证书';
    }
}

// SSL证书续期处理函数
async function handleSSLRenew(event) {
    const form = event.target.closest('form');
    const domain = form.domain.value;

    if (!domain) {
        showToast('请输入域名', 'error');
        return;
    }

    try {
        const button = event.target;
        button.disabled = true;
        button.innerHTML = '<span class="loading"></span> 续期中...';

        const response = await api.renewSSL(domain);
        showToast(response.message, 'success');
        await updateSSLList();  // 如果有证书列表，更新它
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        const button = event.target;
        button.disabled = false;
        button.textContent = '续期证书';
    }
}

// SSL证书列表更新函数（如果需要的话）
async function updateSSLList() {
    try {
        const sslList = await api.getSSLList();  // 需要在 API 类中添加这个方法
        const tableBody = document.getElementById('ssl-table-body');
        if (tableBody && sslList) {
            tableBody.innerHTML = sslList.map(cert => `
                <tr>
                    <td>${cert.domain}</td>
                    <td>${new Date(cert.expiry).toLocaleDateString()}</td>
                    <td>
                        <span class="status-badge ${cert.valid ? 'status-running' : 'status-stopped'}">
                            ${cert.valid ? '有效' : '已过期'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-warning" onclick="handleSSLRenew(event)" data-domain="${cert.domain}">续期</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        showToast('获取证书列表失败: ' + error.message, 'error');
    }
}

// 配置测试处理函数
async function handleTestConfig() {
    try {
        const response = await api.testConfig();
        showToast(response.message, response.success ? 'success' : 'error');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 配置重载处理函数
async function handleReloadConfig() {
    try {
        const response = await api.reloadConfig();
        showToast(response.message, response.success ? 'success' : 'error');
        await updateNginxStatus();  // 重新获取Nginx状态
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 日志类型切换处理函数
async function handleLogTypeChange(event) {
    await handleRefreshLogs();
}

// 日志刷新处理函数
async function handleRefreshLogs() {
    const logType = document.getElementById('log-type').value;
    const lines = document.getElementById('log-lines').value;
    const logContent = document.getElementById('log-content');

    try {
        const logs = await api.getLogs(logType, lines);  // 需要在 API 类中添加这个方法
        if (logs) {
            logContent.textContent = logs.join('\n');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}