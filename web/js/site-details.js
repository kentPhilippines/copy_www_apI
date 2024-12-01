class SiteDetails {
    constructor() {
        this.currentDomain = null;
    }

    async show(domain) {
        try {
            this.currentDomain = domain;
            const site = await api.getSite(domain);
            if (!site) {
                showToast('站点不存在', 'error');
                return;
            }

            // 创建内容
            const content = document.createElement('div');
            content.className = 'site-details';
            content.innerHTML = this._createContent(site);

            // 显示对话框
            const dialog = await showDialog(`站点详情 - ${domain}`, content, {
                width: '800px',
                buttons: [] // 不显示默认的按钮
            });

            // 绑定按钮事件
            this._bindEvents(dialog);

        } catch (error) {
            showToast(error.message, 'error');
            console.error('显示站点详情失败:', error);
        }
    }

    _createContent(site) {
        return `
            <div class="detail-section">
                <h4>基本信息</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>状态:</label>
                        <span class="status-badge ${site.status === 'active' ? 'status-running' : 'status-stopped'}">
                            ${site.status}
                        </span>
                    </div>
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
                        <button class="btn btn-sm btn-info" onclick="viewLog('${site.domain}', 'access')">
                            查看日志
                        </button>
                    </div>
                    <div class="detail-item">
                        <label>错误日志:</label>
                        <span class="file-path" title="${site.logs.error_log}">${site.logs.error_log}</span>
                        <button class="btn btn-sm btn-info" onclick="viewLog('${site.domain}', 'error')">
                            查看日志
                        </button>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <h4>访问地址</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>HTTP:</label>
                        <div class="access-urls">
                            ${site.access_urls.http.map(url => `
                                <a href="${url}" target="_blank" class="url-link">
                                    <span class="protocol">${url}</span>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                    ${site.access_urls.https ? `
                        <div class="detail-item">
                            <label>HTTPS:</label>
                            <div class="access-urls">
                                ${site.access_urls.https.map(url => `
                                    <a href="${url}" target="_blank" class="url-link">
                                        <span class="protocol secure">${url}</span>
                                    </a>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>

            <div class="detail-section">
                <h4>操作</h4>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="handleEditSite('${site.domain}')">
                        编辑配置
                    </button>
                    <button class="btn btn-warning" onclick="handleBackupSite('${site.domain}')">
                        备份站点
                    </button>
                    <button class="btn btn-danger" onclick="handleDeleteSite('${site.domain}')">
                        删除站点
                    </button>
                </div>
            </div>
        `;
    }

    _bindEvents(dialog) {
        // 编辑配置按钮
        const editBtn = dialog.querySelector('.btn-primary');
        if (editBtn) {
            editBtn.onclick = async () => {
                dialog.remove();
                await this._showEditDialog(this.currentDomain);
            };
        }

        // 备份站点按钮
        const backupBtn = dialog.querySelector('.btn-warning');
        if (backupBtn) {
            backupBtn.onclick = async () => {
                try {
                    const response = await api.backupSite(this.currentDomain);
                    if (response.success) {
                        showToast('站点备份成功', 'success');
                    } else {
                        showToast(response.message, 'error');
                    }
                } catch (error) {
                    showToast(error.message, 'error');
                }
            };
        }

        // 删除站点按钮
        const deleteBtn = dialog.querySelector('.btn-danger');
        if (deleteBtn) {
            deleteBtn.onclick = async () => {
                if (confirm(`确定要删除站点 ${this.currentDomain} 吗？`)) {
                    try {
                        const response = await api.deleteSite(this.currentDomain);
                        if (response.success) {
                            dialog.remove();
                            showToast('站点删除成功', 'success');
                            await updateSitesList(); // 更新站点列表
                        } else {
                            showToast(response.message, 'error');
                        }
                    } catch (error) {
                        showToast(error.message, 'error');
                    }
                }
            };
        }

        // 日志查看按钮
        dialog.querySelectorAll('[onclick^="viewLog"]').forEach(btn => {
            const [domain, type] = btn.getAttribute('onclick')
                .match(/viewLog\('([^']+)',\s*'([^']+)'\)/i)
                .slice(1);
            btn.onclick = (e) => {
                e.preventDefault();
                dialog.remove();
                viewLog(domain, type);
            };
        });
    }

    async _showEditDialog(domain) {
        try {
            const site = await api.getSite(domain);
            if (!site) {
                showToast('站点不存在', 'error');
                return;
            }

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

            const result = await showDialog('编辑站点', form, {
                width: '600px',
                buttons: ['保存', '取消']
            });

            if (result === '保存') {
                const formData = new FormData(form);
                const updates = {
                    root_path: formData.get('root_path'),
                    ssl_enabled: formData.get('ssl_enabled') === 'on',
                    custom_config: formData.get('custom_config')
                };

                const response = await api.updateSite(domain, updates);
                if (response.success) {
                    showToast('站点更新成功', 'success');
                    await updateSitesList();
                    await this.show(domain); // 重新显示详情
                } else {
                    showToast(response.message, 'error');
                }
            }
        } catch (error) {
            showToast(error.message, 'error');
        }
    }
}

// 创建全局实例
const siteDetails = new SiteDetails();

// 修改原来的处理函数
async function handleViewSiteDetails(domain) {
    await siteDetails.show(domain);
} 