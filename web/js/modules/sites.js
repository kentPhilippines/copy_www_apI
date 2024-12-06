const SitesModule = {
    async init(app) {
        await this.loadSitesList(app);
        this.initAddSiteForm(app);
    },

    async loadSitesList(app) {
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
                    ${response.sites.map(site => this.renderSiteRow(site, app)).join('')}
                </tbody>
            `;

            container.innerHTML = '';
            container.appendChild(table);

        } catch (error) {
            container.innerHTML = `<p class="error">加载站点列表失败: ${error.message}</p>`;
        }
    },

    initAddSiteForm(app) {
        const form = document.getElementById('addSiteForm');
        if (!form) return;

        const sslCheckbox = form.querySelector('input[name="enable_ssl"]');
        const sslEmailGroup = form.querySelector('.ssl-email');

        sslCheckbox.addEventListener('change', () => {
            sslEmailGroup.style.display = sslCheckbox.checked ? 'block' : 'none';
            sslEmailGroup.querySelector('input').required = sslCheckbox.checked;
        });

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
                await this.loadSitesList(app);
                app.showSuccess('站点添加成功');
            } catch (error) {
                app.showError(error.message);
            } finally {
                submitBtn.disabled = false;
            }
        });
    },

    renderSiteRow(site, app) {
        return `
            <tr>
                <td>
                    <div class="site-domain">
                        <strong>${utils.escapeHtml(site.domain)}</strong>
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
                        <button class="btn btn-sm" onclick="app.modules.sites.viewDetails('${site.domain}')">
                            详情
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="app.modules.sites.configureMirror('${site.domain}')">
                            镜像配置
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="app.modules.sites.confirmDelete('${site.domain}')">
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    async viewDetails(domain) {
        try {
            const site = await api.getSite(domain);
            const modal = document.createElement('div');
            modal.className = 'modal';
            
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${domain} 站点详情</h3>
                        <button class="close-btn">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="site-details">
                            <div class="info-section">
                                <h4>基本信息</h4>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <label>部署类型</label>
                                        <span>${site.deploy_type || '静态'}</span>
                                    </div>
                                    <div class="info-item">
                                        <label>运行状态</label>
                                        <span class="status-badge ${site.status === 'active' ? 'running' : 'stopped'}">
                                            ${site.status === 'active' ? '运行中' : '已停止'}
                                        </span>
                                    </div>
                                    <div class="info-item">
                                        <label>SSL状态</label>
                                        <span class="status-badge ${site.ssl_enabled ? 'ssl' : ''}">
                                            ${site.ssl_enabled ? 'SSL已启用' : 'SSL未启用'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div class="info-section">
                                <h4>路径信息</h4>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <label>站点根目录</label>
                                        <code>${site.root_path}</code>
                                    </div>
                                    <div class="info-item">
                                        <label>配置文件</label>
                                        <code>${site.config_file}</code>
                                    </div>
                                </div>
                            </div>

                            ${site.ssl_enabled ? `
                            <div class="info-section">
                                <h4>SSL证书信息</h4>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <label>证书路径</label>
                                        <code>${site.ssl_info?.cert_path}</code>
                                    </div>
                                    <div class="info-item">
                                        <label>密钥路径</label>
                                        <code>${site.ssl_info?.key_path}</code>
                                    </div>
                                </div>
                            </div>
                            ` : ''}

                            <div class="info-section">
                                <h4>访问地址</h4>
                                <div class="urls-list">
                                    ${site.access_urls?.http?.map(url => `
                                        <a href="${url}" target="_blank" class="url-link">
                                            ${url}
                                            <span class="icon">↗</span>
                                        </a>
                                    `).join('') || ''}
                                    ${site.access_urls?.https?.map(url => `
                                        <a href="${url}" target="_blank" class="url-link ssl">
                                            ${url}
                                            <span class="icon">↗</span>
                                        </a>
                                    `).join('') || ''}
                                </div>
                            </div>

                            <div class="info-section">
                                <h4>日志文件</h4>
                                <div class="info-grid">
                                    <div class="info-item">
                                        <label>访问日志</label>
                                        <code>${site.logs?.access_log}</code>
                                        <button class="btn btn-sm" onclick="app.modules.sites.viewLogs('${domain}', 'access')">
                                            查看日志
                                        </button>
                                    </div>
                                    <div class="info-item">
                                        <label>错误日志</label>
                                        <code>${site.logs?.error_log}</code>
                                        <button class="btn btn-sm" onclick="app.modules.sites.viewLogs('${domain}', 'error')">
                                            查看日志
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // 关闭按钮事件
            const closeBtn = modal.querySelector('.close-btn');
            if (closeBtn) {
                closeBtn.onclick = () => modal.remove();
            }

            // 点击背景关闭
            modal.onclick = (e) => {
                if (e.target === modal) modal.remove();
            };

        } catch (error) {
            app.showError(`加载站点详情失败: ${error.message}`);
        }
    },

    async viewLogs(domain, type) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${domain} - ${type === 'access' ? '访问日志' : '错误日志'}</h3>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="log-viewer">
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
            </div>
        `;

        document.body.appendChild(modal);

        // 初始化日志查看器
        const logContent = modal.querySelector('#logContent');
        const refreshBtn = modal.querySelector('#refreshLogsBtn');
        const autoScrollBtn = modal.querySelector('#autoScrollBtn');
        const linesInput = modal.querySelector('#logLines');
        let autoScroll = true;
        let ws = null;

        // 加载日志函数
        const loadLogs = async () => {
            try {
                const logs = await api.getLogs(type, linesInput.value, domain);
                logContent.textContent = logs.join('\n');
                if (autoScroll) {
                    logContent.scrollTop = logContent.scrollHeight;
                }
            } catch (error) {
                logContent.textContent = `加载日志失败: ${error.message}`;
            }
        };

        // 初始化WebSocket
        const initWebSocket = () => {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${api.baseURL.split('/api/')[0]}/api/v1/nginx/logs/ws/${type}?domain=${domain}`;
            
            ws = new WebSocket(wsUrl);

            ws.onmessage = (event) => {
                logContent.textContent += event.data + '\n';
                if (autoScroll) {
                    logContent.scrollTop = logContent.scrollHeight;
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                logContent.textContent += '\n连接错误，5秒后重试...\n';
            };

            ws.onclose = () => {
                console.log('WebSocket连接已关闭');
                setTimeout(initWebSocket, 5000);
            };
        };

        // 绑定事件
        refreshBtn.onclick = loadLogs;
        autoScrollBtn.onclick = () => {
            autoScroll = !autoScroll;
            autoScrollBtn.classList.toggle('active', autoScroll);
        };

        // 滚动事件
        logContent.onscroll = () => {
            const { scrollTop, scrollHeight, clientHeight } = logContent;
            autoScroll = Math.abs(scrollHeight - clientHeight - scrollTop) < 1;
            autoScrollBtn.classList.toggle('active', autoScroll);
        };

        // 关闭事件
        modal.querySelector('.close-btn').onclick = () => {
            if (ws) ws.close();
            modal.remove();
        };

        modal.onclick = (e) => {
            if (e.target === modal) {
                if (ws) ws.close();
                modal.remove();
            }
        };

        // 加载初始日志
        await loadLogs();
        
        // 启动WebSocket
        initWebSocket();
    },

    async confirmDelete(domain) {
        if (!confirm(`确定要删除站点 ${domain} 吗？此操作不可恢复！`)) {
            return;
        }

        try {
            await api.deleteSite(domain);
            app.showSuccess(`站点 ${domain} 已删除`);
            await this.loadSitesList(app);
        } catch (error) {
            app.showError(`删除站点失败: ${error.message}`);
        }
    },

    async configureMirror(domain) {
        let ws = null;
        let reconnectTimer = null;
        const maxReconnectAttempts = 5;
        let reconnectAttempts = 0;

        const connectWebSocket = (progressArea) => {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${api.baseURL.split('/api/')[0]}/api/v1/nginx/mirror/progress/${domain}`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                reconnectAttempts = 0;
                progressArea.querySelector('.connection-status').textContent = '已连接';
                progressArea.querySelector('.connection-status').className = 'connection-status connected';
            };

            ws.onmessage = (event) => {
                const progress = JSON.parse(event.data);
                updateProgress(progressArea, progress);
            };

            ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                progressArea.querySelector('.connection-status').textContent = '连接错误';
                progressArea.querySelector('.connection-status').className = 'connection-status error';
            };

            ws.onclose = () => {
                progressArea.querySelector('.connection-status').textContent = '已断开';
                progressArea.querySelector('.connection-status').className = 'connection-status disconnected';
                
                // 尝试重连
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                    progressArea.querySelector('.connection-status').textContent = `${delay/1000}秒后重连...`;
                    reconnectTimer = setTimeout(() => connectWebSocket(progressArea), delay);
                } else {
                    progressArea.querySelector('.connection-status').textContent = '重连失败，请刷新页面';
                }
            };

            return ws;
        };

        const updateProgress = (progressArea, progress) => {
            // 更新总进度
            const progressFill = progressArea.querySelector('.progress-fill');
            const progressText = progressArea.querySelector('.progress-text');
            progressFill.style.width = `${progress.overall_progress}%`;
            progressText.textContent = `${progress.overall_progress}%`;

            // 更新统计信息
            const stats = progress.stats;
            Object.keys(stats).forEach(key => {
                const element = progressArea.querySelector(`.${key}-tasks`);
                if (element) {
                    element.textContent = stats[key];
                    // 添加动画效果
                    element.classList.add('updated');
                    setTimeout(() => element.classList.remove('updated'), 300);
                }
            });

            // 更新速度和预计剩余时间
            if (progress.speed) {
                progressArea.querySelector('.download-speed').textContent = 
                    `${utils.formatFileSize(progress.speed)}/s`;
            }
            if (progress.eta) {
                progressArea.querySelector('.eta').textContent = 
                    `预计剩余: ${utils.formatDuration(progress.eta)}`;
            }

            // 更新当前任务列表
            const taskList = progressArea.querySelector('.task-list');
            const taskItems = progress.current_tasks.map(task => `
                <div class="task-item ${task.status}">
                    <div class="task-header">
                        <div class="task-url" title="${utils.escapeHtml(task.url)}">
                            ${utils.escapeHtml(utils.truncateUrl(task.url, 60))}
                        </div>
                        <div class="task-status">${task.status}</div>
                    </div>
                    <div class="task-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${task.progress}%"></div>
                        </div>
                        <div class="progress-stats">
                            <span class="progress-text">
                                ${utils.formatFileSize(task.downloaded)} / ${utils.formatFileSize(task.size)}
                            </span>
                            <span class="progress-percentage">${task.progress}%</span>
                        </div>
                    </div>
                    ${task.error ? `<div class="task-error">${utils.escapeHtml(task.error)}</div>` : ''}
                </div>
            `).join('');

            // 使用DOM diffing来更新任务列表，避免闪烁
            if (taskList.innerHTML !== taskItems) {
                taskList.innerHTML = taskItems;
            }

            // 更新日志
            if (progress.logs && progress.logs.length > 0) {
                const logContent = progressArea.querySelector('.log-content');
                progress.logs.forEach(log => {
                    const logEntry = document.createElement('div');
                    logEntry.className = `log-entry ${log.level}`;
                    logEntry.innerHTML = `
                        <span class="log-time">${log.time}</span>
                        <span class="log-message">${utils.escapeHtml(log.message)}</span>
                    `;
                    logContent.appendChild(logEntry);
                    
                    // 保持最新的日志可见
                    if (logContent.scrollHeight - logContent.scrollTop < logContent.clientHeight + 100) {
                        logContent.scrollTop = logContent.scrollHeight;
                    }
                });

                // 限制日志条数
                while (logContent.children.length > 1000) {
                    logContent.removeChild(logContent.firstChild);
                }
            }
        };

        try {
            const site = await api.getSite(domain);
            const mirrorStatus = await api.getMirrorStatus(domain);
            const modal = document.createElement('div');
            modal.className = 'modal';
            
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
                                        <span>${utils.escapeHtml(mirrorStatus.target_domain)}</span>
                                    </div>
                                    <div class="info-item">
                                        <label>镜像时间</label>
                                        <span>${utils.formatDateTime(mirrorStatus.mirror_time)}</span>
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
                                    <button class="btn btn-warning" onclick="app.modules.sites.refreshMirror('${domain}')">
                                        刷新镜像
                                    </button>
                                    <button class="btn btn-danger" onclick="app.modules.sites.deleteMirror('${domain}')">
                                        删除镜像
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
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
                            <div id="mirrorProgress" class="mirror-progress" style="display: none;">
                                <div class="progress-header">
                                    <h4>镜像进度</h4>
                                    <div class="connection-status">正在连接...</div>
                                </div>
                                <div class="progress-stats">
                                    <div class="download-speed">- KB/s</div>
                                    <div class="eta">预计剩余: 计算中...</div>
                                </div>
                                <div class="progress-info">
                                    <div class="progress-bar">
                                        <div class="progress-fill"></div>
                                    </div>
                                    <div class="progress-text">0%</div>
                                </div>
                                <div class="task-stats">
                                    <div class="stat-item">
                                        <label>总任务数</label>
                                        <span class="total-tasks">0</span>
                                    </div>
                                    <div class="stat-item">
                                        <label>已完成</label>
                                        <span class="completed-tasks">0</span>
                                    </div>
                                    <div class="stat-item">
                                        <label>下载中</label>
                                        <span class="downloading-tasks">0</span>
                                    </div>
                                    <div class="stat-item">
                                        <label>失败</label>
                                        <span class="failed-tasks">0</span>
                                    </div>
                                </div>
                                <div class="current-tasks">
                                    <h5>当前下载任务</h5>
                                    <div class="task-list"></div>
                                </div>
                                <div class="mirror-logs">
                                    <h5>镜像日志</h5>
                                    <div class="log-content"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);

                // 绑定表单事件
                const form = modal.querySelector('#mirrorForm');
                if (form) {
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
                                tdk_rules: formData.get('tdk_rules') ? JSON.parse(formData.get('tdk_rules')) : null
                            };

                            // 显示进度区域
                            form.style.display = 'none';
                            const progressArea = modal.querySelector('#mirrorProgress');
                            progressArea.style.display = 'block';

                            // 开始镜像并监听进度
                            const progressFill = progressArea.querySelector('.progress-fill');
                            const progressText = progressArea.querySelector('.progress-text');
                            const taskList = progressArea.querySelector('.task-list');
                            const logContent = progressArea.querySelector('.log-content');

                            // 启动WebSocket连接监听进度
                            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                            const ws = new WebSocket(`${wsProtocol}//${api.baseURL.split('/api/')[0]}/api/v1/nginx/mirror/progress/${domain}`);

                            ws.onmessage = (event) => {
                                const progress = JSON.parse(event.data);
                                
                                // 更新总进度
                                progressFill.style.width = `${progress.overall_progress}%`;
                                progressText.textContent = `${progress.overall_progress}%`;

                                // 更新统计信息
                                const stats = progress.stats;
                                progressArea.querySelector('.total-tasks').textContent = stats.total;
                                progressArea.querySelector('.completed-tasks').textContent = stats.completed;
                                progressArea.querySelector('.downloading-tasks').textContent = stats.downloading;
                                progressArea.querySelector('.failed-tasks').textContent = stats.failed;

                                // 更新当前任务列表
                                taskList.innerHTML = progress.current_tasks.map(task => `
                                    <div class="task-item">
                                        <div class="task-url">${utils.escapeHtml(task.url)}</div>
                                        <div class="task-progress">
                                            <div class="progress-bar">
                                                <div class="progress-fill" style="width: ${task.progress}%"></div>
                                            </div>
                                            <div class="progress-text">
                                                ${utils.formatFileSize(task.downloaded)} / ${utils.formatFileSize(task.size)}
                                            </div>
                                        </div>
                                    </div>
                                `).join('');

                                // 添加日志
                                if (progress.logs && progress.logs.length > 0) {
                                    progress.logs.forEach(log => {
                                        const logEntry = document.createElement('div');
                                        logEntry.className = `log-entry ${log.level}`;
                                        logEntry.innerHTML = `
                                            <span class="log-time">${log.time}</span>
                                            <span class="log-message">${utils.escapeHtml(log.message)}</span>
                                        `;
                                        logContent.appendChild(logEntry);
                                        logContent.scrollTop = logContent.scrollHeight;
                                    });
                                }
                            };

                            // 开始镜像
                            const response = await api.mirrorSite(data);
                            if (!response.success) {
                                throw new Error(response.message);
                            }

                        } catch (error) {
                            app.showError(error.message);
                            submitBtn.disabled = false;
                            submitBtn.textContent = '开始镜像';
                        }
                    });
                }
            }

            // 关闭按钮事件
            const closeBtn = modal.querySelector('.close-btn');
            if (closeBtn) {
                closeBtn.onclick = () => modal.remove();
            }

            // 点击背景关闭
            modal.onclick = (e) => {
                if (e.target === modal) modal.remove();
            };

        } catch (error) {
            app.showError(`加载镜像配置失败: ${error.message}`);
        }
    },

    async refreshMirror(domain) {
        if (!confirm('确定要刷新镜像站点吗？这将重新下载所有资源。')) {
            return;
        }
        
        try {
            await api.refreshMirror(domain);
            app.showSuccess('镜像刷新成功');
            document.querySelector('.modal').remove();
        } catch (error) {
            app.showError(`刷新镜像失败: ${error.message}`);
        }
    },

    async deleteMirror(domain) {
        if (!confirm('确定要删除��像站点吗？此操作不可恢复！')) {
            return;
        }
        
        try {
            await api.deleteMirror(domain);
            app.showSuccess('镜像删除成功');
            document.querySelector('.modal').remove();
        } catch (error) {
            app.showError(`删除镜像失败: ${error.message}`);
        }
    }
};

window.SitesModule = SitesModule; 