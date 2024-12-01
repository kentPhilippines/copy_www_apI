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
    setInterval(updateSitesList, 6000);

    // 初始化Nginx状态
    updateNginxStatus();
    
    // 每10秒更新一次Nginx状态
    setInterval(updateNginxStatus, 2000);
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
        showToast('获取Nginx状态失败: ' + error.message, 'error');
    }
}

// 更新状态显示
function updateStatusDisplay(status) {
    // 更新运行状态
    const runningBadge = document.getElementById('nginx-running');
    if (runningBadge) {
        runningBadge.className = `status-badge ${status.running ? 'status-running' : 'status-stopped'}`;
        runningBadge.textContent = status.running ? '运行中' : '已停止';
    }

    // 更新版本和配置信息
    const elements = {
        'nginx-version': status.version,
        'config-test-status': status.config_test
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
                <td>
                    <span class="status-badge ${proc.status === 'sleeping' ? 'status-running' : 'status-stopped'}">
                        ${proc.status}
                    </span>
                </td>
                <td>${proc.type === 'master' ? '主进程' : '工作进程'}</td>
                <td>
                    <span class="process-cwd" title="${proc.cwd}">
                        ${proc.cwd}
                    </span>
                </td>
                <td>
                    ${proc.type === 'master' ? 
                        `<small class="process-cmd">${proc.cmdline}</small>` : 
                        `<small>CPU: ${proc.cpu_percent.toFixed(1)}% | 内存: ${proc.memory_percent.toFixed(1)}%</small>`
                    }
                </td>
            </tr>
        `).join('');
    }

    // 更新资源使用情况
    const resources = status.resources;
    const resourceElements = {
        'cpu-usage': `${resources.cpu_percent}%`,
        'memory-usage': `${resources.memory_percent}%`,
        'connection-count': resources.connections
    };

    for (const [id, value] of Object.entries(resourceElements)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    // 添加工作进程数量和运行时间（如果有的话）
    if (resources.worker_count !== undefined) {
        const workerCount = document.getElementById('worker-count');
        if (workerCount) {
            workerCount.textContent = resources.worker_count;
        }
    }

    if (resources.uptime) {
        const uptime = document.getElementById('uptime');
        if (uptime) {
            uptime.textContent = resources.uptime;
        }
    }

    // 更新网络流量图表
    updateNetworkChart(status.resources.network);
    
    // 更新磁盘使用图表
    updateDiskChart(status.resources.disk);

    // 更新资源使用��示
    document.getElementById('network-traffic').textContent = 
        `↑${formatBytes(status.resources.network.out_bytes)}/s ↓${formatBytes(status.resources.network.in_bytes)}/s`;
    
    document.getElementById('disk-usage').textContent = 
        `${formatBytes(status.resources.disk.used)} / ${formatBytes(status.resources.disk.total)}`;
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

// 更新站点列表函数
async function updateSitesList() {
    try {
        const sites = await api.getSites();
        const tableBody = document.getElementById('sites-table-body');
        if (tableBody) {
            tableBody.innerHTML = sites.map(site => `
                <tr>
                    <td>
                        <div class="site-domain">
                            <strong>${site.domain}</strong>
                            <span class="status-badge ${site.status === 'active' ? 'status-running' : 'status-stopped'}">
                                ${site.status}
                            </span>
                        </div>
                    </td>
                    <td>
                        <div class="access-urls">
                            ${site.access_urls.http.map(url => `
                                <a href="${url}" target="_blank" class="url-link">
                                    <span class="protocol">HTTP</span>
                                </a>
                            `).join('')}
                            ${site.access_urls.https ? site.access_urls.https.map(url => `
                                <a href="${url}" target="_blank" class="url-link">
                                    <span class="protocol secure">HTTPS</span>
                                </a>
                            `).join('') : ''}
                        </div>
                    </td>
                    <td>
                        <div class="button-group">
                            <button class="btn btn-sm btn-info" onclick="handleViewSiteDetails('${site.domain}')">
                                <i class="fas fa-info-circle">详情</i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="handleDeleteSite('${site.domain}')">
                                <i class="fas fa-trash">删除</i>
                            </button>
                        </div>
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
    const logType = event.target.value;
    const domain = document.getElementById('log-domain')?.value;
    
    // 清空日志内容
    const logContent = document.getElementById('log-content');
    logContent.textContent = '';

    // ��取初始日志内容
    await handleRefreshLogs();

    // 启动实时日志
    initLogWebSocket(logType, domain);
}

// 日志刷新处理函数
async function handleRefreshLogs() {
    const logType = document.getElementById('log-type').value;
    const lines = document.getElementById('log-lines').value;
    const logContent = document.getElementById('log-content');

    try {
        const logs = await api.getLogs(logType, lines);  // 要在 API 类中添加这个方法
        if (logs) {
            logContent.textContent = logs.join('\n');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 编辑站点处理函数
async function handleEditSite(domain) {
    try {
        // 获取站点信息
        const site = await api.getSite(domain);
        if (!site) {
            showToast('站点不存在', 'error');
            return;
        }

        // 创建编辑表单
        const form = document.createElement('form');
        form.className = 'edit-form';
        form.innerHTML = `
            <div class="form-group">
                <label>域名</label>
                <input type="text" name="domain" value="${site.domain}" readonly>
            </div>
            <div class="form-group">
                <label>根目录</label>
                <input type="text" name="root_path" value="${site.root_path}">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="ssl_enabled" ${site.ssl_enabled ? 'checked' : ''}>
                    启用SSL
                </label>
            </div>
            <div class="form-group">
                <label>自定义配置</label>
                <textarea name="custom_config" rows="5">${site.custom_config || ''}</textarea>
            </div>
        `;

        // 显示对话框
        const result = await showDialog('编辑站点', form);
        if (!result) return;

        // 获取表单数据
        const formData = new FormData(form);
        const updates = {
            root_path: formData.get('root_path'),
            ssl_enabled: formData.get('ssl_enabled') === 'on',
            custom_config: formData.get('custom_config')
        };

        // 发送更新请求
        const response = await api.updateSite(domain, updates);
        showToast(response.message, 'success');
        await updateSitesList();

    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 备份站点处理函数
async function handleBackupSite(domain) {
    try {
        const response = await api.backupSite(domain);
        if (response.success) {
            const backupInfo = response.data;
            showToast(`站点 ${domain} 备份成功\n备份路径: ${backupInfo.backup_path}`, 'success');
            
            // 可选：提供载备份的链接
            if (backupInfo.download_url) {
                const link = document.createElement('a');
                link.href = backupInfo.download_url;
                link.download = `${domain}_backup_${backupInfo.backup_time}.tar.gz`;
                link.click();
            }
        } else {
            showToast(response.message, 'error');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 示对话框的辅助函数
function showDialog(title, content) {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'dialog-overlay';
        dialog.innerHTML = `
            <div class="dialog">
                <div class="dialog-header">
                    <h3>${title}</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="dialog-content"></div>
                <div class="dialog-footer">
                    <button class="btn btn-primary save-btn">保存</button>
                    <button class="btn btn-secondary cancel-btn">取消</button>
                </div>
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
        dialog.querySelector('.cancel-btn').onclick = () => {
            dialog.remove();
            resolve(false);
        };
        dialog.querySelector('.save-btn').onclick = () => {
            dialog.remove();
            resolve(true);
        };

        document.body.appendChild(dialog);
    });
}

// 日志WebSocket连接
let logWebSocket = null;

// 初始化WebSocket连接
function initLogWebSocket(logType, domain = null) {
    // 关闭现有连接
    if (logWebSocket) {
        logWebSocket.close();
    }

    // 构建WebSocket URL
    const wsUrl = new URL(api.baseURL);
    wsUrl.protocol = wsUrl.protocol.replace('http', 'ws');
    wsUrl.pathname = `/api/v1/nginx/logs/ws/${logType}`;
    if (domain) {
        wsUrl.searchParams.append('domain', domain);
    }

    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 1000; // 1秒

    function connect() {
        // 创建新连接
        logWebSocket = new WebSocket(wsUrl.toString());
        const logContent = document.getElementById('log-content');

        logWebSocket.onmessage = (event) => {
            // 添加新日志行
            if (event.data.startsWith('错误:')) {
                showToast(event.data, 'error');
            } else {
                logContent.textContent += event.data + '\n';
                // 如果启用了自动滚动
                if (autoScroll) {
                    logContent.scrollTop = logContent.scrollHeight;
                }
            }
        };

        logWebSocket.onerror = (error) => {
            showToast('日志连接错误', 'error');
        };

        logWebSocket.onclose = () => {
            console.log('日志连接已关闭');
            // 尝试重连
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(connect, reconnectDelay * reconnectAttempts);
            } else {
                showToast('日志连接已断开，请刷新页面重试', 'error');
            }
        };

        logWebSocket.onopen = () => {
            console.log('日志连接已建立');
            reconnectAttempts = 0; // 重置重连计数
        };
    }

    connect();
}

// 修改日志类型切换处理函数
async function handleLogTypeChange(event) {
    const logType = event.target.value;
    const domain = document.getElementById('log-domain')?.value;
    
    // 清空日志内容
    const logContent = document.getElementById('log-content');
    logContent.textContent = '';

    // 获取初始日志内容
    await handleRefreshLogs();

    // 启动实时日志
    initLogWebSocket(logType, domain);
}

// 修改日志页面HTML
function initLogPage() {
    const logPage = document.getElementById('logs');
    if (logPage) {
        logPage.innerHTML = `
            <div class="card">
                <h2>Nginx日志</h2>
                <div class="form-group">
                    <select id="log-type" onchange="handleLogTypeChange(event)">
                        <option value="access">访问日志</option>
                        <option value="error">错误日志</option>
                    </select>
                    <select id="log-domain" onchange="handleLogTypeChange(event)">
                        <option value="">全局日志</option>
                        <!-- 站点列表将动态添加 -->
                    </select>
                </div>
                <div class="form-group">
                    <label>显示行数</label>
                    <input type="number" id="log-lines" value="100" min="1" max="10000">
                    <button onclick="handleRefreshLogs()" class="btn btn-primary">刷新</button>
                    <button onclick="clearLogs()" class="btn btn-secondary">清空</button>
                    <button onclick="toggleAutoScroll()" class="btn btn-info" id="auto-scroll-btn">自动滚动: 开</button>
                </div>
                <pre id="log-content" class="log-content"></pre>
            </div>
        `;

        // 更新站点列表
        updateLogDomainList();
    }
}

// 更新日志域名列表
async function updateLogDomainList() {
    try {
        const sites = await api.getSites();
        const domainSelect = document.getElementById('log-domain');
        if (domainSelect) {
            const options = sites.map(site => `
                <option value="${site.domain}">${site.domain}</option>
            `).join('');
            domainSelect.innerHTML = '<option value="">全局日志</option>' + options;
        }
    } catch (error) {
        showToast('获取站点列表失败', 'error');
    }
}

// 清空日志
function clearLogs() {
    const logContent = document.getElementById('log-content');
    if (logContent) {
        logContent.textContent = '';
    }
}

// 自动滚动控制
let autoScroll = true;
function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const btn = document.getElementById('auto-scroll-btn');
    if (btn) {
        btn.textContent = `自动滚动: ${autoScroll ? '开' : '关'}`;
    }
}

 

// 全局变量保存图表实例
let networkChart = null;
let diskChart = null;

// 更新网���流量图表
function updateNetworkChart(data) {
    const ctx = document.getElementById('networkUsageChart');
    if (!ctx) return;

    if (!networkChart) {
        networkChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.history.map(d => d.time),
                datasets: [
                    {
                        label: '入站流量',
                        data: data.history.map(d => d.in),
                        borderColor: '#36a2eb',
                        fill: false
                    },
                    {
                        label: '出站流量',
                        data: data.history.map(d => d.out),
                        borderColor: '#ff6384',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => formatBytes(value)
                        }
                    }
                }
            }
        });
    } else {
        networkChart.data.labels = data.history.map(d => d.time);
        networkChart.data.datasets[0].data = data.history.map(d => d.in);
        networkChart.data.datasets[1].data = data.history.map(d => d.out);
        networkChart.update();
    }
}

// 更新磁盘使用图表
function updateDiskChart(data) {
    const ctx = document.getElementById('diskUsageChart');
    if (!ctx) return;

    if (!diskChart) {
        diskChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['已使用', '可用'],
                datasets: [{
                    data: [data.used, data.free],
                    backgroundColor: ['#ff6384', '#36a2eb']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: context => formatBytes(context.raw)
                        }
                    }
                }
            }
        });
    } else {
        diskChart.data.datasets[0].data = [data.used, data.free];
        diskChart.update();
    }
}

// 格式化字节数
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 查看站点详情
async function handleViewSiteDetails(domain) {
    try {
        const site = await api.getSite(domain);
        if (!site) {
            showToast('站点不存在', 'error');
            return;
        }

        const content = document.createElement('div');
        content.className = 'site-details';
        content.innerHTML = `
            <div class="detail-section">
                <h4>基本信息</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>配置文件:</label>
                        <span class="file-path" title="${site.config_file}">${site.config_file}</span>
                    </div>
                    <div class="detail-item">
                        <label>根目录:</label>
                        <span class="file-path ${site.root_exists ? '' : 'not-exists'}" 
                              title="${site.root_path}">${site.root_path}</span>
                    </div>
                    <div class="detail-item">
                        <label>端口:</label>
                        <span>HTTP: ${site.ports.join(', ')} | HTTPS: ${site.ssl_ports.join(', ') || '无'}</span>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <h4>SSL证书</h4>
                ${site.ssl_enabled && site.ssl_info ? `
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>证书文件:</label>
                            <span class="file-path ${site.ssl_info.cert_exists ? '' : 'not-exists'}" 
                                  title="${site.ssl_info.cert_path}">${site.ssl_info.cert_path}</span>
                        </div>
                        <div class="detail-item">
                            <label>密钥文件:</label>
                            <span class="file-path ${site.ssl_info.key_exists ? '' : 'not-exists'}" 
                                  title="${site.ssl_info.key_path}">${site.ssl_info.key_path}</span>
                        </div>
                    </div>
                ` : '<p>未启用SSL</p>'}
            </div>

            <div class="detail-section">
                <h4>日志文件</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>访问日志:</label>
                        <span class="file-path" title="${site.logs.access_log}">${site.logs.access_log}</span>
                        <button class="btn btn-sm btn-info" onclick="viewLog('${domain}', 'access')">
                            查看日志
                        </button>
                    </div>
                    <div class="detail-item">
                        <label>错误日志:</label>
                        <span class="file-path" title="${site.logs.error_log}">${site.logs.error_log}</span>
                        <button class="btn btn-sm btn-info" onclick="viewLog('${domain}', 'error')">
                            查看日志
                        </button>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <h4>资源使用情况</h4>
                <div class="resource-charts">
                    <div class="chart-container">
                        <h5>网络流量</h5>
                        <canvas id="networkChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h5>磁盘使用</h5>
                        <canvas id="diskChart"></canvas>
                    </div>
                </div>
                <div class="resource-stats">
                    <div class="stat-item">
                        <label>总流量:</label>
                        <span>${formatBytes(site.stats?.total_traffic || 0)}</span>
                    </div>
                    <div class="stat-item">
                        <label>请求数:</label>
                        <span>${site.stats?.requests_count || 0}/分钟</span>
                    </div>
                    <div class="stat-item">
                        <label>磁盘使用:</label>
                        <span>${formatBytes(site.stats?.disk_usage || 0)} / ${formatBytes(site.stats?.disk_quota || 0)}</span>
                    </div>
                </div>
            </div>
        `;

        await showDialog(`站点详情 - ${domain}`, content);

        // 初始化图表
        if (site.stats) {
            initNetworkChart(site.stats.network_history);
            initDiskChart(site.stats.disk_usage, site.stats.disk_quota);
        }

    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 查看日志
async function viewLog(domain, type) {
    try {
        // 切换到日志页面
        switchPage('logs');
        
        // 设置日志类型和域名
        document.getElementById('log-type').value = type;
        const domainSelect = document.getElementById('log-domain');
        if (domainSelect) {
            domainSelect.value = domain;
        }
        
        // 刷新日志内容
        await handleRefreshLogs();
        
        // 启动实时日志
        initLogWebSocket(type, domain);
    } catch (error) {
        showToast(error.message, 'error');
    }
}