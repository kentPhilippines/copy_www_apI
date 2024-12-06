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
        // 原viewSiteDetails方法的内容
    },

    async configureMirror(domain) {
        // 原configureMirror方法的内容
    },

    async confirmDelete(domain) {
        // 原confirmDeleteSite方法的内容
    }
};

export default SitesModule; 