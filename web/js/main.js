const api = new API();
let currentPage = 'sites';

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // 初始化API地址
    const apiUrlInput = document.getElementById('api-url');
    apiUrlInput.value = api.baseURL;
    apiUrlInput.addEventListener('change', (e) => {
        api.setBaseURL(e.target.value);
    });

    // 初始化导航
    initNavigation();
    
    // 加载初始页面
    await updateNginxStatus();
    loadPage('sites');
}

function initNavigation() {
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const page = e.target.dataset.page;
            
            // 更新活动状态
            document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
            e.target.classList.add('active');
            
            await loadPage(page);
        });
    });
}

async function updateNginxStatus() {
    try {
        const status = await api.getNginxStatus();
        UI.updateNginxStatus(status);
    } catch (error) {
        UI.showToast('获取Nginx状态失败: ' + error.message, 'error');
    }
}

async function loadPage(page) {
    currentPage = page;
    const mainContent = document.getElementById('main-content');
    
    try {
        switch (page) {
            case 'sites':
                mainContent.innerHTML = await createSitesPage();
                break;
            case 'ssl':
                mainContent.innerHTML = await createSSLPage();
                break;
            case 'config':
                mainContent.innerHTML = await createConfigPage();
                break;
            case 'logs':
                mainContent.innerHTML = await createLogsPage();
                break;
        }
    } catch (error) {
        UI.showToast('加载页面失败: ' + error.message, 'error');
    }
}

// 页面内容生成函数...
// (根据需要添加其他页面的内容生成函数)
// 创建站点管理页面
async function createSitesPage() {
    return `
        <div class="card">
            <h2>添加新站点</h2>
            <form id="add-site-form" onsubmit="handleAddSite(event)">
                <div class="form-group">
                    <label>域名</label>
                    <input type="text" name="domain" required placeholder="example.com">
                </div>
                <div class="form-group">
                    <label>端口</label>
                    <input type="number" name="port" value="80" required>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="ssl">
                        启用SSL
                    </label>
                </div>
                <button type="submit" class="btn btn-primary">添加站点</button>
            </form>
        </div>
        <div class="card">
            <h2>站点列表</h2>
            <div id="sites-list">
                <div class="loading"></div>
            </div>
        </div>
    `;
}

// 创建SSL证书页面
async function createSSLPage() {
    return `
        <div class="card">
            <h2>SSL证书管理</h2>
            <form id="ssl-form" onsubmit="handleSSLRequest(event)">
                <div class="form-group">
                    <label>域名</label>
                    <input type="text" name="domain" required placeholder="example.com">
                </div>
                <div class="form-group">
                    <button type="submit" class="btn btn-primary">申请证书</button>
                    <button type="button" class="btn btn-warning" onclick="handleSSLRenew(event)">续期证书</button>
                </div>
            </form>
        </div>
        <div class="card">
            <h2>证书列表</h2>
            <div id="ssl-list">
                <div class="loading"></div>
            </div>
        </div>
    `;
}

// 创建配置管理页面
async function createConfigPage() {
    const status = await api.getNginxStatus();
    return `
        <div class="card">
            <h2>Nginx状态</h2>
            <div class="status-info">
                <p>版本: ${status.version}</p>
                <p>配置测试: ${status.config_test}</p>
                <p>进程数: ${status.processes.length}</p>
                <p>CPU使用率: ${status.resources.cpu_percent.toFixed(2)}%</p>
                <p>内存使用率: ${status.resources.memory_percent.toFixed(2)}%</p>
                <p>连接数: ${status.resources.connections}</p>
            </div>
        </div>
        <div class="card">
            <h2>配置操作</h2>
            <div class="button-group">
                <button onclick="handleTestConfig()" class="btn btn-primary">测试配置</button>
                <button onclick="handleReloadConfig()" class="btn btn-warning">重载配置</button>
            </div>
        </div>
    `;
}

// 创建日志查看页面
async function createLogsPage() {
    return `
        <div class="card">
            <h2>Nginx日志</h2>
            <div class="form-group">
                <select id="log-type" onchange="handleLogTypeChange(event)">
                    <option value="access">访问日志</option>
                    <option value="error">错误日志</option>
                </select>
            </div>
            <div class="form-group">
                <label>行数</label>
                <input type="number" id="log-lines" value="100" min="1" max="1000">
                <button onclick="handleRefreshLogs()" class="btn btn-primary">刷新</button>
            </div>
            <pre id="log-content" class="log-content"></pre>
        </div>
    `;
}

// 事件处理函数
async function handleAddSite(event) {
    event.preventDefault();
    const form = event.target;
    const data = {
        domain: form.domain.value,
        port: parseInt(form.port.value),
        ssl: form.ssl.checked
    };

    try {
        UI.setLoading(form.querySelector('button'), true);
        const response = await api.createSite(data);
        UI.showToast(response.message, 'success');
        loadPage('sites');
    } catch (error) {
        UI.showToast(error.message, 'error');
    } finally {
        UI.setLoading(form.querySelector('button'), false);
    }
}

async function handleSSLRequest(event) {
    event.preventDefault();
    const form = event.target;
    const domain = form.domain.value;

    try {
        UI.setLoading(form.querySelector('button'), true);
        const response = await api.createSSL(domain);
        UI.showToast(response.message, 'success');
    } catch (error) {
        UI.showToast(error.message, 'error');
    } finally {
        UI.setLoading(form.querySelector('button'), false);
    }
}

async function handleSSLRenew(event) {
    const form = event.target.closest('form');
    const domain = form.domain.value;

    try {
        UI.setLoading(event.target, true);
        const response = await api.renewSSL(domain);
        UI.showToast(response.message, 'success');
    } catch (error) {
        UI.showToast(error.message, 'error');
    } finally {
        UI.setLoading(event.target, false);
    }
}

async function handleTestConfig() {
    try {
        const response = await api.testConfig();
        UI.showToast(response.message, response.success ? 'success' : 'error');
    } catch (error) {
        UI.showToast(error.message, 'error');
    }
}

async function handleReloadConfig() {
    try {
        const response = await api.reloadConfig();
        UI.showToast(response.message, response.success ? 'success' : 'error');
        await updateNginxStatus();
    } catch (error) {
        UI.showToast(error.message, 'error');
    }
}

async function handleLogTypeChange(event) {
    await handleRefreshLogs();
}

async function handleRefreshLogs() {
    const logType = document.getElementById('log-type').value;
    const lines = document.getElementById('log-lines').value;
    const logContent = document.getElementById('log-content');

    try {
        const logs = await api.getLogs(logType, lines);
        logContent.textContent = logs.join('\n');
    } catch (error) {
        UI.showToast(error.message, 'error');
    }
}