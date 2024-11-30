const api = new API();
let currentPage = 'sites';

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // 初始化API地址
    const apiUrlInput = document.getElementById('api-url');
    apiUrlInput.value = api.baseURL;
    apiUrlInput.addEventListener('change', (e) => {
        api.setBaseURL(e.target.value);
    });

    // 初始化导航
    initNavigation();
    
    // 加载初始页面
    await updateNginxStatus();
    loadPage('sites');
}

function initNavigation() {
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const page = e.target.dataset.page;
            
            // 更新活动状态
            document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
            e.target.classList.add('active');
            
            await loadPage(page);
        });
    });
}

async function updateNginxStatus() {
    try {
        const status = await api.getNginxStatus();
        UI.updateNginxStatus(status);
    } catch (error) {
        UI.showToast('获取Nginx状态失败: ' + error.message, 'error');
    }
}

async function loadPage(page) {
    currentPage = page;
    const mainContent = document.getElementById('main-content');
    
    try {
        switch (page) {
            case 'sites':
                mainContent.innerHTML = await createSitesPage();
                break;
            case 'ssl':
                mainContent.innerHTML = await createSSLPage();
                break;
            case 'config':
                mainContent.innerHTML = await createConfigPage();
                break;
            case 'logs':
                mainContent.innerHTML = await createLogsPage();
                break;
        }
    } catch (error) {
        UI.showToast('加载页面失败: ' + error.message, 'error');
    }
}

// 页面内容生成函数...
// (根据需要添加其他页面的内容生成函数)