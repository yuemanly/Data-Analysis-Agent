/**
 * ui.js - UI 工具函数
 * 提供 Toast、Modal、Loading 等 UI 操作
 */

const UIUtils = {
  /**
   * 显示 Toast 提示
   */
  showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer') || this.createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    
    const icon = this.getToastIcon(type);
    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span class="toast-text">${this.escapeHtml(message)}</span>
      <button class="toast-close" aria-label="关闭提示">×</button>
    `;
    
    container.appendChild(toast);
    
    // 自动关闭
    const timeoutId = setTimeout(() => {
      toast.classList.add('toast-exit');
      setTimeout(() => toast.remove(), 300);
    }, duration);
    
    // 手动关闭
    toast.querySelector('.toast-close').addEventListener('click', () => {
      clearTimeout(timeoutId);
      toast.classList.add('toast-exit');
      setTimeout(() => toast.remove(), 300);
    });
    
    return toast;
  },

  /**
   * 创建 Toast 容器
   */
  createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
  },

  /**
   * 获取 Toast 图标
   */
  getToastIcon(type) {
    const icons = {
      info: 'ℹ️',
      success: '✓',
      warning: '⚠️',
      error: '✕',
    };
    return icons[type] || icons.info;
  },

  /**
   * 设置按钮加载状态
   */
  setButtonLoading(btn, loading, text = '处理中...') {
    if (!btn) return;
    
    if (loading) {
      btn.dataset.originText = btn.textContent;
      btn.textContent = text;
      btn.disabled = true;
      btn.classList.add('loading');
    } else {
      btn.textContent = btn.dataset.originText || btn.textContent;
      btn.disabled = false;
      btn.classList.remove('loading');
    }
  },

  /**
   * 显示加载骨架
   */
  showSkeleton(container, count = 3) {
    if (!container) return;
    
    container.innerHTML = '';
    for (let i = 0; i < count; i++) {
      const skeleton = document.createElement('div');
      skeleton.className = 'skeleton-item';
      skeleton.innerHTML = `
        <div class="skeleton skeleton-avatar"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text" style="width: 80%;"></div>
      `;
      container.appendChild(skeleton);
    }
  },

  /**
   * 隐藏加载骨架
   */
  hideSkeleton(container) {
    if (!container) return;
    container.innerHTML = '';
  },

  /**
   * 显示状态消息
   */
  showStatus(elementId, type, message) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    el.className = `status status-${type}`;
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    
    const icon = this.getToastIcon(type);
    el.innerHTML = `
      <span class="status-icon">${icon}</span>
      <span class="status-text">${this.escapeHtml(message)}</span>
    `;
    
    el.style.display = 'flex';
  },

  /**
   * 隐藏状态消息
   */
  hideStatus(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'none';
  },

  /**
   * 显示模态框
   */
  showModal(title, content, buttons = []) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'modalTitle');
    
    const buttonsHtml = buttons
      .map((btn, idx) => `
        <button class="btn btn-${btn.type || 'primary'}" data-action="${idx}">
          ${this.escapeHtml(btn.text)}
        </button>
      `)
      .join('');
    
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2 id="modalTitle">${this.escapeHtml(title)}</h2>
          <button class="modal-close" aria-label="关闭">×</button>
        </div>
        <div class="modal-body">
          ${content}
        </div>
        <div class="modal-footer">
          ${buttonsHtml}
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // 关闭按钮
    modal.querySelector('.modal-close').addEventListener('click', () => {
      modal.remove();
    });
    
    // 按钮事件
    modal.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = parseInt(btn.dataset.action);
        if (buttons[action]?.onClick) {
          buttons[action].onClick();
        }
        modal.remove();
      });
    });
    
    // 点击背景关闭
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
    
    return modal;
  },

  /**
   * 显示确认对话框
   */
  confirm(message, onConfirm, onCancel) {
    return this.showModal('确认', message, [
      {
        text: '取消',
        type: 'secondary',
        onClick: onCancel,
      },
      {
        text: '确认',
        type: 'primary',
        onClick: onConfirm,
      },
    ]);
  },

  /**
   * 显示警告对话框
   */
  alert(message, onClose) {
    return this.showModal('提示', message, [
      {
        text: '关闭',
        type: 'primary',
        onClick: onClose,
      },
    ]);
  },

  /**
   * 禁用所有按钮
   */
  disableAllButtons(disabled = true) {
    document.querySelectorAll('button').forEach(btn => {
      btn.disabled = disabled;
    });
  },

  /**
   * 禁用表单
   */
  disableForm(formId, disabled = true) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.querySelectorAll('input, textarea, select, button').forEach(el => {
      el.disabled = disabled;
    });
  },

  /**
   * 清空表单
   */
  clearForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.querySelectorAll('input, textarea, select').forEach(el => {
      if (el.type === 'checkbox' || el.type === 'radio') {
        el.checked = false;
      } else {
        el.value = '';
      }
    });
  },

  /**
   * 获取表单数据
   */
  getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    
    const data = {};
    form.querySelectorAll('input, textarea, select').forEach(el => {
      if (el.name) {
        if (el.type === 'checkbox') {
          data[el.name] = el.checked;
        } else if (el.type === 'radio') {
          if (el.checked) data[el.name] = el.value;
        } else {
          data[el.name] = el.value;
        }
      }
    });
    
    return data;
  },

  /**
   * 设置表单数据
   */
  setFormData(formId, data) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    Object.entries(data).forEach(([name, value]) => {
      const el = form.querySelector(`[name="${name}"]`);
      if (!el) return;
      
      if (el.type === 'checkbox') {
        el.checked = value;
      } else if (el.type === 'radio') {
        form.querySelector(`[name="${name}"][value="${value}"]`).checked = true;
      } else {
        el.value = value;
      }
    });
  },

  /**
   * 复制到剪贴板
   */
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      this.showToast('已复制到剪贴板', 'success');
      return true;
    } catch (err) {
      this.showToast('复制失败', 'error');
      return false;
    }
  },

  /**
   * HTML 转义
   */
  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  },

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  },

  /**
   * 格式化日期
   */
  formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (typeof date === 'string') date = new Date(date);
    
    const pad = (n) => String(n).padStart(2, '0');
    
    return format
      .replace('YYYY', date.getFullYear())
      .replace('MM', pad(date.getMonth() + 1))
      .replace('DD', pad(date.getDate()))
      .replace('HH', pad(date.getHours()))
      .replace('mm', pad(date.getMinutes()))
      .replace('ss', pad(date.getSeconds()));
  },
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { UIUtils };
}
