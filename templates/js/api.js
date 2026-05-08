/**
 * api.js - API 调用统一封装（最终修正版）
 * 特性：
 * - 统一错误处理
 * - 超时控制（AbortController）
 * - 自动 JSON 序列化/解析
 * - 支持 baseURL
 * - 上传文件专用方法
 */

const API = {
  baseURL: '', // 例如: 'http://localhost:5000'
  timeout: 30000,

  /**
   * 构造完整 URL
   * @param {string} url
   * @returns {string}
   */
  buildURL(url) {
    if (!this.baseURL) return url;
    const base = this.baseURL.replace(/\/+$/, '');
    const path = String(url || '').replace(/^\/+/, '');
    return `${base}/${path}`;
  },

  /**
   * 统一请求方法
   * @param {string} url
   * @param {object} options
   * @returns {Promise<any>}
   */
  async request(url, options = {}) {
    const {
      method = 'GET',
      headers = {},
      body = null,
      timeout = this.timeout,
      ...rest
    } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // 仅在 JSON body 时自动添加 Content-Type
    const finalHeaders = { ...headers };
    const hasBody = body !== null && body !== undefined;
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

    let finalBody = null;
    if (hasBody) {
      if (isFormData) {
        finalBody = body;
      } else {
        finalHeaders['Content-Type'] = finalHeaders['Content-Type'] || 'application/json';
        finalBody =
          typeof body === 'string' || body instanceof Blob
            ? body
            : JSON.stringify(body);
      }
    }

    try {
      const response = await fetch(this.buildURL(url), {
        method,
        headers: finalHeaders,
        body: finalBody,
        signal: controller.signal,
        ...rest,
      });

      clearTimeout(timeoutId);

      // 兼容非 JSON 返回
      const contentType = response.headers.get('content-type') || '';
      const isJSON = contentType.includes('application/json');
      const data = isJSON ? await response.json().catch(() => ({})) : await response.text();

      if (!response.ok) {
        const message =
          (isJSON && data && (data.error || data.message)) ||
          `HTTP ${response.status} ${response.statusText}`;
        const error = new Error(message);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error(`请求超时（${timeout}ms）`);
      }
      throw error;
    }
  },

  get(url, options = {}) {
    return this.request(url, { ...options, method: 'GET' });
  },

  post(url, body, options = {}) {
    return this.request(url, { ...options, method: 'POST', body });
  },

  put(url, body, options = {}) {
    return this.request(url, { ...options, method: 'PUT', body });
  },

  patch(url, body, options = {}) {
    return this.request(url, { ...options, method: 'PATCH', body });
  },

  delete(url, options = {}) {
    return this.request(url, { ...options, method: 'DELETE' });
  },

  /**
   * 文件上传（multipart/form-data）
   * @param {string} url
   * @param {File|Blob} file
   * @param {object} extraFields - 额外表单字段
   * @param {object} options - 可传 timeout 等
   */
  upload(url, file, extraFields = {}, options = {}) {
    const formData = new FormData();
    formData.append('file', file);

    Object.entries(extraFields || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null) formData.append(k, v);
    });

    return this.request(url, {
      ...options,
      method: 'POST',
      body: formData,
    });
  },
};

/**
 * 图表相关 API
 */
const ChartAPI= {
  /** 获取图表列表 */
  getCharts() {
    return API.get('/api/charts');
  },

  /** 获取配色方案（若后端提供） */
  getColorSchemes() {
    return API.get('/api/color-schemes');
  },

  /** 上传文件 */
  uploadFile(file) {
    return API.upload('/api/upload', file);
  },

  /**
   * 分析数据（与你当前页面逻辑对齐）
   * @param {object} params
   * @param {string} params.filepath
   * @param {string} params.query
   * @param {string} [params.provider]
   */
  analyzeData({ filepath, query, provider }) {
    return API.post('/api/analyze', { filepath, query, provider });
  },

  /**
   * 生成图表
   * @param {object} params
   * @param {string} params.filepath
   * @param {string} params.chartType
   * @param {string} [params.colorScheme]
   * @param {object} [params.options]
   */
  generateChart({ filepath, chartType, colorScheme, options = {} }) {
    return API.post('/api/generate', {
      filepath,
      chart_type: chartType,
      color_scheme: colorScheme,
      options,
    });
  },

  /** 打开下载链接 */
  openDownloadByFilename(filename) {
    window.open(`/api/download/${filename}`, '_blank');
  },

  /** 打开后端返回的下载 URL */
  openDownloadByURL(downloadURL) {
    window.open(downloadURL, '_blank');
  },
};

/**
 * LLM 相关 API
 */
const LLMAPI = {
  /** 获取 LLM 配置列表 */
  listConfigs() {
    return API.get('/api/llm/list');
  },

  /** 保存 LLM 配置 */
  saveConfig(provider, apiKey) {
    return API.post('/api/llm/config', { provider, api_key: apiKey });
  },

  /** 测试 LLM 配置 */
  testConfig(provider) {
    return API.post(`/api/llm/test/${provider}`);
  },

  /** 添加自定义模型 */
  addCustomModel(name, baseUrl, modelName, apiKey) {
    return API.post('/api/llm/add-custom', {
      name,
      base_url: baseUrl,
      model_name: modelName,
      api_key: apiKey,
    });
  },

  /**
   * 如果你有 /api/chat 可用，保留此方法
   * 当前主流程通常用 /api/analyze
   */
  sendMessage(message) {
    return API.post('/api/chat', { message });
  },
};

/* ---------- 导出（兼容浏览器和 Node） ---------- */

// 浏览器全局
if (typeof window !== 'undefined') {
  window.API = API;
  window.ChartAPI = ChartAPI;
  window.LLMAPI = LLMAPI;
}

// CommonJS
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { API, ChartAPI, LLMAPI };
}
