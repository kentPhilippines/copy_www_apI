// 定义全局模块对象
window.AppModules = {
    sites: SitesModule,
    config: ConfigModule,
    logs: LogsModule
};

// 页面模板
const PAGE_TEMPLATES = {
    sites: `
        <div class="page sites-page">
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
        </div>
    `,
    
    config: `
        <div class="page config-page">
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
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>进程信息</h2>
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
                <h2>配置操作</h2>
                <div class="button-group">
                    <button id="testConfigBtn" class="btn">测试配置</button>
                    <button id="reloadConfigBtn" class="btn btn-warning">重载配置</button>
                    <button id="restartNginxBtn" class="btn btn-danger">重启Nginx</button>
                </div>
                <pre id="configTestResult" class="config-test-result" style="display: none;"></pre>
            </div>
        </div>
    `,
    
    logs: `
        <div class="page logs-page">
            <div class="card">
                <h2>日志查看</h2>
                <div class="log-controls">
                    <div class="form-group">
                        <label>日志类型</label>
                        <select id="logType">
                            <option value="access">访问日志</option>
                            <option value="error">错误日志</option>
                        </select>
                    </div>
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
    `
};

class App {
    constructor() {
        this.modules = AppModules;
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
        if (hash && this.modules[hash]) {
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
            
            // 加载页面模板
            const template = PAGE_TEMPLATES[this.currentPage];
            if (template) {
                this.mainContent.innerHTML = template;
            }
            
            // 初始化当前页面的模块
            if (this.modules[this.currentPage]) {
                await this.modules[this.currentPage].init(this);
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
        if (!this.modules[pageId]) return;
        
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
}

// 当DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});