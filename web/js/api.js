class API {
    constructor() {
        this.baseURL = localStorage.getItem('apiUrl') || 'http://8.218.57.117:8000/api/v1';
    }

    setBaseURL(url) {
        this.baseURL = url;
        localStorage.setItem('apiUrl', url);
    }

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    }

    // Nginx状态
    async getNginxStatus() {
        return this.request('/nginx/status');
    }

    // 站点管理
    async createSite(siteData) {
        return this.request('/deploy/sites', {
            method: 'POST',
            body: JSON.stringify({
                domain: siteData.domain,
                deploy_type: siteData.deploy_type,
                enable_ssl: siteData.enable_ssl,
                ssl_email: siteData.ssl_email
            })
        });
    }

    async deleteSite(domain) {
        return this.request(`/nginx/sites/${domain}`, {
            method: 'DELETE'
        });
    }

    // SSL证书
    async createSSL(domain) {
        return this.request('/ssl/create', {
            method: 'POST',
            body: JSON.stringify({ domain })
        });
    }

    async renewSSL(domain) {
        return this.request('/ssl/renew', {
            method: 'POST',
            body: JSON.stringify({ domain })
        });
    }

    // 配置管理
    async testConfig() {
        return this.request('/nginx/test-config');
    }

    async reloadConfig() {
        return this.request('/nginx/reload');
    }

    // 站点列表
    async getSites() {
        return this.request('/nginx/sites');
    }

    // SSL证书列表
    async getSSLList() {
        return this.request('/ssl/list');
    }

    // 获取日志
    async getLogs(type, lines) {
        return this.request(`/nginx/logs/${type}?lines=${lines}`);
    }

    async getSite(domain) {
        try {
            const response = await this.request(`/sites/${domain}`);
            return {
                domain: response.domain,
                status: response.status || 'unknown',
                config_file: response.config_file,
                root_path: response.root_path,
                root_exists: response.root_exists,
                ports: response.ports || [],
                ssl_ports: response.ssl_ports || [],
                ssl_enabled: response.ssl_enabled,
                ssl_info: response.ssl_info,
                logs: response.logs || {
                    access_log: '/var/log/nginx/access.log',
                    error_log: '/var/log/nginx/error.log'
                },
                access_urls: response.access_urls || {
                    http: [],
                    https: []
                }
            };
        } catch (error) {
            console.error('获取站点详情失败:', error);
            throw new Error('获取站点详情失败');
        }
    }

    async updateSite(domain, updates) {
        return this.request(`/sites/${domain}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    async backupSite(domain) {
        return this.request(`/sites/${domain}/backup`, {
            method: 'POST'
        });
    }
}