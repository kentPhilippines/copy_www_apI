import SitesModule from './modules/sites.js';
import ConfigModule from './modules/config.js';
import LogsModule from './modules/logs.js';

class App {
    constructor() {
        this.modules = {
            sites: SitesModule,
            config: ConfigModule,
            logs: LogsModule
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
            const response = await fetch(`/pages/${this.currentPage}.html`);
            const html = await response.text();
            this.mainContent.innerHTML = html;
            
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