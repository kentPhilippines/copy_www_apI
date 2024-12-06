class App {
    constructor() {
        // 定义可用页面
        this.pages = {
            sites: '站点管理',
            config: '配置管理',
            logs: '日志查看'
        };
        
        this.currentPage = 'sites';
        this.initElements();
        this.initEvents();
        this.initialize();
    }

    initElements() {
        this.apiUrlInput = document.getElementById('apiUrl');
        this.navMenu = document.getElementById('nav-menu');
        this.mainContent = document.getElementById('main-content');
        this.status = document.getElementById('status');

        // 设置API地址输入框的初始值
        this.apiUrlInput.value = api.baseURL;
    }

    initEvents() {
        // API地址变更事件
        this.apiUrlInput.addEventListener('change', (e) => {
            api.setBaseURL(e.target.value);
            this.loadCurrentPage();
        });

        // 导航点击事件
        this.navMenu.addEventListener('click', (e) => {
            if (e.target.tagName === 'A') {
                e.preventDefault();
                const page = e.target.getAttribute('href').slice(1);
                this.switchPage(page);
            }
        });

        // 监听浏览器前进后退
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.page) {
                this.switchPage(e.state.page, false);
            }
        });
    }

    async initialize() {
        // 从URL hash初始化页面
        const hash = window.location.hash.slice(1);
        if (hash && this.pages[hash]) {
            this.currentPage = hash;
        }

        // 加载初始页面
        await this.loadCurrentPage();

        // 开始定时更新状态
        this.startStatusUpdates();
    }

    async loadCurrentPage() {
        this.showLoading();
        try {
            // 清空主内容区域
            this.mainContent.innerHTML = '';
            
            // 根据当前页面加载对应内容
            switch (this.currentPage) {
                case 'sites':
                    await this.loadSitesPage();
                    break;
                case 'config':
                    await this.loadConfigPage();
                    break;
                case 'logs':
                    await this.loadLogsPage();
                    break;
            }
        } catch (error) {
            this.showError('加载页面失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(overlay);
    }

    hideLoading() {
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    showMessage(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    async startStatusUpdates() {
        try {
            const status = await api.getNginxStatus();
            this.updateStatusDisplay(status);
        } catch (error) {
            console.error('获取状态失败:', error);
        }

        // 每30秒更新一次状态
        setInterval(async () => {
            try {
                const status = await api.getNginxStatus();
                this.updateStatusDisplay(status);
            } catch (error) {
                console.error('更新状态失败:', error);
            }
        }, 30000);
    }

    updateStatusDisplay(status) {
        if (this.status) {
            this.status.className = `status ${status.running ? 'running' : 'stopped'}`;
            this.status.textContent = status.running ? '运行中' : '已停止';
        }
    }

    async switchPage(pageId, updateHistory = true) {
        if (!this.pages[pageId]) return;
        
        this.currentPage = pageId;
        
        // 更新导航状态
        this.navMenu.querySelectorAll('a').forEach(a => {
            a.classList.toggle('active', a.getAttribute('href') === `#${pageId}`);
        });

        // 更新浏览器历史
        if (updateHistory) {
            history.pushState({ page: pageId }, '', `#${pageId}`);
        }

        // 加载页面内容
        await this.loadCurrentPage();
    }

    async loadSitesPage() {
        const container = document.createElement('div');
        container.className = 'page sites-page';

        // 添加新站点卡片
        container.innerHTML = `
            <div class="card">
                <h2>添加新站点</h2>
                <form id="addSiteForm">
                    <div class="form-group">
                        <label>域名</label>
                        <input type="text" name="domain" required placeholder="example.com">
                    </div>
                    <div class="form-group">
                        <label>部署类型</label>
                        <select name="deploy_type">
                            <option value="static">静态站点</option>
                            <option value="php">PHP站点</option>
                            <option value="node">Node.js站点</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="enable_ssl">
                            启用SSL
                        </label>
                    </div>
                    <div class="form-group ssl-email" style="display: none;">
                        <label>SSL证书邮箱</label>
                        <input type="email" name="ssl_email" placeholder="your@email.com">
                    </div>
                    <button type="submit" class="btn">添加站点</button>
                </form>
            </div>

            <div class="card">
                <h2>站点列表</h2>
                <div id="sitesList">
                    <div class="loading"></div>
                </div>
            </div>
        `;

        this.mainContent.appendChild(container);

        // 初始化表单事件
        this.initAddSiteForm();

        // 加载站点列表
        await this.loadSitesList();
    }

    async loadSitesList() {
        const container = document.getElementById('sitesList');
        if (!container) return;

        try {
            const response = await api.getSites();
            
            if (!response.sites || response.sites.length === 0) {
                container.innerHTML = '<p class="empty">暂无站点</p>';
                return;
            }

            const table = document.createElement('table');
            table.className = 'table';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>域名</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${response.sites.map(site => this.renderSiteRow(site)).join('')}
                </tbody>
            `;

            container.innerHTML = '';
            container.appendChild(table);

        } catch (error) {
            container.innerHTML = `<p class="error">加载站点列表失败: ${error.message}</p>`;
        }
    }

    renderSiteRow(site) {
        return `
            <tr>
                <td>
                    <div class="site-domain">
                        <strong>${this.escapeHtml(site.domain)}</strong>
                        ${site.ssl_enabled ? '<span class="badge ssl">SSL</span>' : ''}
                    </div>
                </td>
                <td>
                    <span class="status-badge ${site.status === 'active' ? 'running' : 'stopped'}">
                        ${site.status === 'active' ? '运行中' : '已停止'}
                    </span>
                </td>
                <td>
                    <div class="button-group">
                        <button class="btn btn-sm" onclick="app.viewSiteDetails('${site.domain}')">
                            详情
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="app.configureMirror('${site.domain}')">
                            镜像配置
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="app.confirmDeleteSite('${site.domain}')">
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    initAddSiteForm() {
        const form = document.getElementById('addSiteForm');
        if (!form) return;

        const sslCheckbox = form.querySelector('input[name="enable_ssl"]');
        const sslEmailGroup = form.querySelector('.ssl-email');

        // SSL选项切换
        sslCheckbox.addEventListener('change', () => {
            sslEmailGroup.style.display = sslCheckbox.checked ? 'block' : 'none';
            sslEmailGroup.querySelector('input').required = sslCheckbox.checked;
        });

        // 表单提交
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;

            try {
                const formData = new FormData(form);
                const data = {
                    domain: formData.get('domain'),
                    deploy_type: formData.get('deploy_type'),
                    enable_ssl: formData.get('enable_ssl') === 'on',
                    ssl_email: formData.get('ssl_email')
                };

                await api.createSite(data);
                form.reset();
                sslEmailGroup.style.display = 'none';
                await this.loadSitesList();
                this.showSuccess('站点添加成功');
            } catch (error) {
                this.showError(error.message);
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async loadConfigPage() {
        const container = document.createElement('div');
        container.className = 'page config-page';

        container.innerHTML = `
            <div class="card">
                <h2>Nginx状态</h2>
                <div class="status-info">
                    <div class="info-grid">
                        <div class="info-item">
                            <label>运行状态</label>
                            <span id="nginxRunningStatus" class="status-badge">检查中...</span>
                        </div>
                        <div class="info-item">
                            <label>工作进程数</label>
                            <span id="workerCount">-</span>
                        </div>
                        <div class="info-item">
                            <label>当前连接数</label>
                            <span id="connectionCount">-</span>
                        </div>
                        <div class="info-item">
                            <label>版本信息</label>
                            <span id="nginxVersion">-</span>
                        </div>
                        <div class="info-item">
                            <label>运行时间</label>
                            <span id="nginxUptime">-</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>进程信息</h2>processTable
                <div class="process-info">
                    <table class="table" id="processTable">
                        <thead>
                            <tr>
                                <th>PID</th>
                                <th>类型</th>
                                <th>状态</th>
                                <th>CPU</th>
                                <th>内存</th>
                                <th>连接数</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td colspan="6" class="text-center">加载中...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2>资源使用</h2>
                <div class="resource-info">
                    <div class="info-grid">
                        <div class="info-item">
                            <label>CPU使用率</label>
                            <span id="cpuUsage">-</span>
                        </div>
                        <div class="info-item">
                            <label>内存使用率</label>
                            <span id="memoryUsage">-</span>
                        </div>
                        <div class="info-item">
                            <label>磁盘使用</label>
                            <span id="diskUsage">-</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>配置操作</h2>
                <div class="button-group">
                    <button id="testConfigBtn" class="btn">测试配置</button>
                    <button id="reloadConfigBtn" class="btn btn-warning">重载配置</button>
                </div>
                <pre id="configTestResult" class="config-test-result" style="display: none;"></pre>
            </div>
        `;

        this.mainContent.appendChild(container);

        // 初始化事件
        this.initConfigPage();
        
        // 加载初始数据
        await this.updateConfigStatus();
    }

    async initConfigPage() {
        const testBtn = document.getElementById('testConfigBtn');
        const reloadBtn = document.getElementById('reloadConfigBtn');
        const resultPre = document.getElementById('configTestResult');

        testBtn.addEventListener('click', async () => {
            testBtn.disabled = true;
            testBtn.textContent = '测试中...';
            resultPre.style.display = 'none';

            try {
                const result = await api.testConfig();
                resultPre.textContent = result.message;
                resultPre.style.display = 'block';
                resultPre.className = 'config-test-result ' + (result.success ? 'success' : 'error');
                if (result.success) {
                    this.showSuccess('配置测试通过');
                } else {
                    this.showError('配置测试失败');
                }
            } catch (error) {
                this.showError(error.message);
            } finally {
                testBtn.disabled = false;
                testBtn.textContent = '测试配置';
            }
        });

        reloadBtn.addEventListener('click', async () => {
            if (!confirm('确定要重载Nginx配置吗？')) return;

            reloadBtn.disabled = true;
            reloadBtn.textContent = '载中...';

            try {
                const result = await api.reloadConfig();
                if (result.success) {
                    this.showSuccess('配置重载成功');
                    await this.updateConfigStatus();
                } else {
                    this.showError(result.message || '配置重载失败');
                }
            } catch (error) {
                this.showError(error.message);
            } finally {
                reloadBtn.disabled = false;
                reloadBtn.textContent = '重载配置';
            }
        });
    }

    async updateConfigStatus() {
        try {
            const status = await api.getNginxStatus();
            
            // 更新状态显示
            document.getElementById('nginxRunningStatus').className = 
                `status-badge ${status.running ? 'running' : 'stopped'}`;
            document.getElementById('nginxRunningStatus').textContent = 
                status.running ? '运行中' : '已停止';
            
            document.getElementById('workerCount').textContent = 
                status.resources?.worker_count || '-';
            document.getElementById('connectionCount').textContent = 
                status.resources?.connections || '-';
            
            document.getElementById('cpuUsage').textContent = 
                `${status.resources?.cpu_percent || 0}%`;
            document.getElementById('memoryUsage').textContent = 
                `${status.resources?.memory_percent || 0}%`;
            document.getElementById('diskUsage').textContent = 
                `${this.formatBytes(status.resources?.disk?.used || 0)} / ${this.formatBytes(status.resources?.disk?.total || 0)}`;
                //processTable

            // 更新进程信息表格
            const processTable = document.getElementById('processTable').querySelector('tbody');
            if (processTable && status.processes) {
                processTable.innerHTML = status.processes.map(proc => `
                    <tr>
                        <td>${proc.pid}</td>
                        <td>${proc.type}</td>
                        <td>${proc.status}</td>
                        <td>${proc.cpu_percent?.toFixed(1) || '-'}%</td>
                        <td>${proc.memory_percent?.toFixed(1) || '-'}%</td>
                        <td>${proc.connections || '-'}</td>
                    </tr>
                `).join('');
            }

            // 更新版本信息和运行时间
            document.getElementById('nginxVersion').textContent = status.version;
            document.getElementById('nginxUptime').textContent = status.resources.uptime;
        } catch (error) {
            console.error('更新态失败:', error);
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async confirmDeleteSite(domain) {
        if (!confirm(`确定要删除站点 ${domain} 吗？此操作不可恢复！`)) {
            return;
        }

        try {
            await api.deleteSite(domain);
            this.showSuccess(`站点 ${domain} 已删除`);
            await this.loadSitesList();
        } catch (error) {
            this.showError(`删除站点失败: ${error.message}`);
        }
    }

    async viewSiteDetails(domain) {
        try {
            const site = await api.getSite(domain);
            
            // 创建模态框显示详情
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${domain} 详情</h3>
                        <button class="close-btn">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="details-grid">
                            <div class="details-section">
                                <h4>基本信息</h4>
                                <div class="details-item">
                                    <label>状态</label>
                                    <span class="status-badge ${site.status === 'active' ? 'running' : 'stopped'}">
                                        ${site.status === 'active' ? '运行中' : '已停止'}
                                    </span>
                                </div>
                                <div class="details-item">
                                    <label>SSL</label>
                                    <span>${site.ssl_enabled ? '已启用' : '未启用'}</span>
                                </div>
                            </div>

                            <div class="details-section">
                                <h4>路径配置</h4>
                                <div class="details-item">
                                    <label>配置文件</label>
                                    <span class="file-path">${site.config_file}</span>
                                </div>
                                <div class="details-item">
                                    <label>根目录</label>
                                    <span class="file-path ${!site.root_exists ? 'not-exists' : ''}">
                                        ${site.root_path}
                                    </span>
                                </div>
                            </div>

                            ${site.ssl_enabled ? `
                                <div class="details-section">
                                    <h4>SSL证书</h4>
                                    <div class="details-item">
                                        <label>证书文件</label>
                                        <span class="file-path">${site.ssl_info.cert_path}</span>
                                    </div>
                                    <div class="details-item">
                                        <label>密钥文件</label>
                                        <span class="file-path">${site.ssl_info.key_path}</span>
                                    </div>
                                </div>
                            ` : ''}

                            <div class="details-section">
                                <h4>访问地址</h4>
                                <div class="access-urls">
                                    ${site.access_urls.http.map(url => `
                                        <a href="${url}" target="_blank" class="url-link">
                                            <span class="protocol">HTTP</span>
                                            ${url.replace('http://', '')}
                                        </a>
                                    `).join('')}
                                    ${site.access_urls.https.map(url => `
                                        <a href="${url}" target="_blank" class="url-link">
                                            <span class="protocol secure">HTTPS</span>
                                            ${url.replace('https://', '')}
                                        </a>
                                    `).join('')}
                                </div>
                            </div>

                            <div class="details-section">
                                <h4>日志文件</h4>
                                <div class="details-item">
                                    <label>访问日志</label>
                                    <span class="file-path">${site.logs.access_log}</span>
                                    <button class="btn btn-sm" onclick="app.viewLogs('${domain}', 'access')">
                                        查看日志
                                    </button>
                                </div>
                                <div class="details-item">
                                    <label>错日志</label>
                                    <span class="file-path">${site.logs.error_log}</span>
                                    <button class="btn btn-sm" onclick="app.viewLogs('${domain}', 'error')">
                                        查看日志
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // 关闭按钮事件
            modal.querySelector('.close-btn').onclick = () => {
                modal.remove();
            };

            // 点击背景关闭
            modal.onclick = (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            };
        } catch (error) {
            this.showError(`加载站点详情失败: ${error.message}`);
        }
    }

    async viewLogs(domain, type) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${domain} ${type === 'access' ? '访问' : '错误'}日志</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="log-controls">
                        <div class="form-group">
                            <label>显示行数</label>
                            <input type="number" id="logLines" value="100" min="1" max="1000">
                        </div>
                        <div class="button-group">
                            <button id="refreshLogsBtn" class="btn">刷新</button>
                            <button id="autoScrollBtn" class="btn active">自动滚动</button>
                        </div>
                    </div>
                    <div class="log-content-wrapper">
                        <pre id="logContent" class="log-content">加载中...</pre>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const logContent = modal.querySelector('#logContent');
        const linesInput = modal.querySelector('#logLines');
        const refreshBtn = modal.querySelector('#refreshLogsBtn');
        const autoScrollBtn = modal.querySelector('#autoScrollBtn');
        let autoScroll = true;
        let ws = null;

        // 加载日志内容
        const loadLogs = async () => {
            try {
                const lines = parseInt(linesInput.value);
                const logs = await api.getLogs(type, lines, domain);
                logContent.textContent = logs.join('\n');
                if (autoScroll) {
                    logContent.scrollTop = logContent.scrollHeight;
                }
            } catch (error) {
                logContent.textContent = '加载日志失败: ' + error.message;
            }
        };

        // 初始化WebSocket连接
        const initWebSocket = () => {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${api.baseURL.split('://')[1]}/nginx/logs/ws/${type}?domain=${domain}`;
            ws = new WebSocket(wsUrl);

            ws.onmessage = (event) => {
                logContent.textContent += event.data + '\n';
                if (autoScroll) {
                    logContent.scrollTop = logContent.scrollHeight;
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket连接已关闭');
                // 5秒后尝试重连
                setTimeout(initWebSocket, 5000);
            };
        };

        // 绑定事件
        refreshBtn.onclick = loadLogs;
        autoScrollBtn.onclick = () => {
            autoScroll = !autoScroll;
            autoScrollBtn.classList.toggle('active', autoScroll);
        };

        // 关闭按钮事件
        modal.querySelector('.close-btn').onclick = () => {
            if (ws) {
                ws.close();
            }
            modal.remove();
        };

        // 点击背景关闭
        modal.onclick = (e) => {
            if (e.target === modal) {
                if (ws) {
                    ws.close();
                }
                modal.remove();
            }
        };

        // 加载初始日志
        await loadLogs();
        
        // 启动WebSocket实时更新
        initWebSocket();
    }

    async configureMirror(domain) {
        try {
            // 先获取当前站点信息和镜像状态
            const site = await api.getSite(domain);
            const mirrorStatus = await api.getMirrorStatus(domain);
            
            const modal = document.createElement('div');
            modal.className = 'modal';
            
            // 如果已经存在镜像，显示镜像信息
            if (mirrorStatus.exists) {
                modal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>${domain} 镜像站信息</h3>
                            <button class="close-btn">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div class="mirror-info">
                                <div class="info-section">
                                    <h4>基本信息</h4>
                                    <div class="info-item">
                                        <label>目标站点</label>
                                        <span>${mirrorStatus.target_domain}</span>
                                    </div>
                                    <div class="info-item">
                                        <label>镜像时间</label>
                                        <span>${mirrorStatus.mirror_time}</span>
                                    </div>
                                    <div class="info-item">
                                        <label>文件数量</label>
                                        <span>${mirrorStatus.files_count} 个文件</span>
                                    </div>
                                </div>
                                <div class="info-section">
                                    <h4>配置信息</h4>
                                    <div class="info-item">
                                        <label>站点地图</label>
                                        <span>${mirrorStatus.sitemap ? '已生成' : '未生成'}</span>
                                    </div>
                                    <div class="info-item">
                                        <label>TDK替换</label>
                                        <span>${mirrorStatus.tdk ? '已替换' : '未替换'}</span>
                                    </div>
                                </div>
                                <div class="button-group mt-4">
                                    <button class="btn btn-warning" onclick="app.refreshMirror('${domain}')">
                                        刷新镜像
                                    </button>
                                    <button class="btn btn-danger" onclick="app.deleteMirror('${domain}')">
                                        删除镜像
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                // 显示新建镜像表单
                modal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>${domain} 镜像配置</h3>
                            <button class="close-btn">&times;</button>
                        </div>
                        <div class="modal-body">
                            <form id="mirrorForm" class="mirror-form">
                                <div class="form-group">
                                    <label>目标域名 <span class="required">*</span></label>
                                    <input type="text" name="target_domain" required placeholder="target.com">
                                    <div class="hint">请输入要镜像的目标网站域名</div>
                                </div>
                                <div class="form-group">
                                    <label>目标存放路径</label>
                                    <input type="text" name="target_path" required 
                                        value="${site.root_path}" 
                                        readonly
                                        title="使用当前站点根目录">
                                    <div class="hint">镜像内容将存放在当前站点根目录</div>
                                </div>
                                <div class="form-group">
                                    <label>镜像选项</label>
                                    <div class="checkbox-group">
                                        <label>
                                            <input type="checkbox" name="overwrite">
                                            覆盖已存在的文件
                                        </label>
                                    </div>
                                    <div class="checkbox-group">
                                        <label>
                                            <input type="checkbox" name="sitemap">
                                            生成站点地图
                                        </label>
                                    </div>
                                    <div class="checkbox-group">
                                        <label>
                                            <input type="checkbox" name="tdk">
                                            替换TDK信息
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group tdk-rules" style="display: none;">
                                    <label>TDK替换规则</label>
                                    <textarea name="tdk_rules" rows="4" placeholder='{"title": "新标题", "keywords": "新关键词", "description": "新描述"}'></textarea>
                                    <div class="hint">请使用JSON格式配置要替换的标题、关键词和描述</div>
                                </div>
                                <div class="button-group">
                                    <button type="submit" class="btn">开始镜像</button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;
            }

            document.body.appendChild(modal);
            
            // TDK选项切换
            const tdkCheckbox = modal.querySelector('input[name="tdk"]');
            const tdkRulesGroup = modal.querySelector('.tdk-rules');
            tdkCheckbox.addEventListener('change', () => {
                tdkRulesGroup.style.display = tdkCheckbox.checked ? 'block' : 'none';
            });

            // 表单提交
            const form = modal.querySelector('#mirrorForm');
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = '处理中...';

                try {
                    const formData = new FormData(form);
                    const data = {
                        domain: domain,
                        target_domain: formData.get('target_domain'),
                        target_path: formData.get('target_path'),
                        overwrite: formData.get('overwrite') === 'on',
                        sitemap: formData.get('sitemap') === 'on',
                        tdk: formData.get('tdk') === 'on',
                        tdk_rules: formData.get('tdk') ? JSON.parse(formData.get('tdk_rules')) : null
                    };

                    await api.mirrorSite(data);
                    this.showSuccess('镜像配置成功');
                    modal.remove();
                } catch (error) {
                    this.showError(error.message);
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '开始镜像';
                }
            });

            // 关闭按钮事件
            modal.querySelector('.close-btn').onclick = () => modal.remove();
            modal.onclick = (e) => {
                if (e.target === modal) modal.remove();
            };
        } catch (error) {
            this.showError(`加载镜像配置失败: ${error.message}`);
        }
    }

    // 刷新镜像
    async refreshMirror(domain) {
        if (!confirm('确定要刷新镜像站点吗？这将重新下载所有资源。')) {
            return;
        }
        
        try {
            await api.refreshMirror(domain);
            this.showSuccess('镜像刷新成功');
            document.querySelector('.modal').remove();
        } catch (error) {
            this.showError(`刷新镜像失败: ${error.message}`);
        }
    }

    // 删除镜像
    async deleteMirror(domain) {
        if (!confirm('确定要删除镜像站点吗？此操作不可恢复！')) {
            return;
        }
        
        try {
            await api.deleteMirror(domain);
            this.showSuccess('镜像删除成功');
            document.querySelector('.modal').remove();
        } catch (error) {
            this.showError(`删除镜像失败: ${error.message}`);
        }
    }
}

// 当DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});