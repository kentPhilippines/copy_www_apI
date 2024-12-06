// 通用工具函数
const utils = {
    // 格式化日期时间
    formatDateTime(date) {
        const d = new Date(date);
        return d.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    },

    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // HTML转义
    escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // 深拷贝
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        const copy = Array.isArray(obj) ? [] : {};
        Object.keys(obj).forEach(key => {
            copy[key] = this.deepClone(obj[key]);
        });
        return copy;
    },

    // 格式化时间差
    formatTimeDiff(timestamp) {
        const diff = Date.now() - new Date(timestamp).getTime();
        const seconds = Math.floor(diff / 1000);
        
        if (seconds < 60) return '刚刚';
        
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}分钟前`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}小时前`;
        
        const days = Math.floor(hours / 24);
        if (days < 30) return `${days}天前`;
        
        const months = Math.floor(days / 30);
        if (months < 12) return `${months}个月前`;
        
        const years = Math.floor(months / 12);
        return `${years}年前`;
    },

    // 生成随机ID
    generateId(prefix = '') {
        return `${prefix}${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    },

    // 格式化错误消息
    formatError(error) {
        if (typeof error === 'string') return error;
        if (error instanceof Error) return error.message;
        if (error.message) return error.message;
        return '未知错误';
    }
};

// 导出工具函数
window.utils = utils; 