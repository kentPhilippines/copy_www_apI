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

            // 如果是新建镜像表单，绑定表单事件
            if (!mirrorStatus.exists) {
                const form = modal.querySelector('#mirrorForm');
                const tdkCheckbox = modal.querySelector('input[name="tdk"]');
                const tdkRulesGroup = modal.querySelector('.tdk-rules');

                if (tdkCheckbox && tdkRulesGroup) {
                    tdkCheckbox.addEventListener('change', () => {
                        tdkRulesGroup.style.display = tdkCheckbox.checked ? 'block' : 'none';
                    });
                }

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

                            await api.mirrorSite(data);
                            app.showSuccess('镜像配置成功');
                            modal.remove();
                            await this.loadSitesList(app);
                        } catch (error) {
                            app.showError(error.message);
                        } finally {
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
        if (!confirm('确定要删除镜像站点吗？此操作不可恢复！')) {
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