class API {
    constructor() {
        this.baseURL = localStorage.getItem('apiUrl') || 'http://8.210.194.181:8000/api/v1';
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

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || '请求失败');
            }

            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    // 设置API基础地址
    setBaseURL(url) {
        this.baseURL = url;
        localStorage.setItem('apiUrl', url);
    }

    // 通用请求方法
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || '请求失败');
            }

            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    // 获取Nginx运行状态
    async getNginxStatus() {
        return this.request('/nginx/status');
    }

    // 获取站点列表
    async getSites() {
        return this.request('/deploy/sites');
    }

    // 创建新站点
    async createSite(data) {
        return this.request('/deploy/sites', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // 获取单个站点信息
    async getSite(domain) {
        return this.request(`/deploy/sites/${domain}`);
    }

    // 更新站点配置
    async updateSite(domain, data) {
        return this.request(`/deploy/sites/${domain}`, {
            method: 'PUT', 
            body: JSON.stringify(data)
        });
    }

    // 删除站点
    async deleteSite(domain) {
        return this.request(`/deploy/sites/${domain}`, {
            method: 'DELETE'
        });
    }

    // 测试Nginx配置
    async testConfig() {
        return this.request('/nginx/test');
    }

    // 重载Nginx配置
    async reloadConfig() {
        return this.request('/nginx/reload');
    }

    // 获取日志内容
    async getLogs(type, lines = 100, domain = '') {
        const params = new URLSearchParams({ 
            type,  // 日志类型: access/error
            lines, // 显示行数
            domain // 站点域名(可选)
        });
        return this.request(`/nginx/logs?${params}`);
    }

    // 镜像站点
    async mirrorSite(data) {
        return this.request('/deploy/sites/mirror', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// 创建全局API实例
window.api = new API(); 