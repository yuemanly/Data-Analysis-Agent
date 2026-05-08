/**
 * state.js - 集中状态管理
 * 所有应用状态集中在这里，避免全局变量漂移
 */

const AppState = {
  // 文件相关
  file: {
    path: null,
    name: null,
    size: null,
    uploadTime: null,
  },

  // 图表相关
  chart: {
    selected: null,
    all: [],
    options: {},
  },

  // LLM 相关
  llm: {
    provider: '',
    apiKey: '',
    configs: {},
  },

  // UI 状态
  ui: {
    loading: {
      upload: false,
      analyze: false,
      generate: false,
      llm: false,
    },
    messages: [],
    selectedChartMeta: null,
  },

  // 缓存
  cache: {
    charts: null,
    colorSchemes: null,
  },
};

/**
 * 状态管理器
 */
const StateManager = {
  /**
   * 获取状态
   */
  getState(path) {
    if (!path) return AppState;
    
    return path.split('.').reduce((obj, key) => obj?.[key], AppState);
  },

  /**
   * 设置状态
   */
  setState(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    
    let obj = AppState;
    for (const key of keys) {
      if (!obj[key]) obj[key] = {};
      obj = obj[key];
    }
    
    obj[lastKey] = value;
    
    // 触发状态变化事件
    this.emit('stateChange', { path, value });
  },

  /**
   * 更新状态（深度合并）
   */
  updateState(path, updates) {
    const current = this.getState(path);
    const merged = { ...current, ...updates };
    this.setState(path, merged);
  },

  /**
   * 重置状态
   */
  resetState(path) {
    if (path === 'file') {
      this.setState('file', {
        path: null,
        name: null,
        size: null,
        uploadTime: null,
      });
    } else if (path === 'chart') {
      this.setState('chart', {
        selected: null,
        options: {},
      });
    } else if (path === 'ui.messages') {
      this.setState('ui.messages', []);
    }
  },

  /**
   * 事件系统
   */
  listeners: {},

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  },

  off(event, callback) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  },

  emit(event, data) {
    if (!this.listeners[event]) return;
    this.listeners[event].forEach(callback => callback(data));
  },

  /**
   * 设置加载状态
   */
  setLoading(key, value) {
    this.setState(`ui.loading.${key}`, value);
  },

  /**
   * 获取加载状态
   */
  isLoading(key) {
    return this.getState(`ui.loading.${key}`);
  },

  /**
   * 设置文件
   */
  setFile(path, name, size) {
    this.setState('file', {
      path,
      name,
      size,
      uploadTime: new Date().toLocaleString(),
    });
  },

  /**
   * 获取文件
   */
  getFile() {
    return this.getState('file');
  },

  /**
   * 清除文件
   */
  clearFile() {
    this.resetState('file');
  },

  /**
   * 设置选中的图表
   */
  setSelectedChart(chartId, chartMeta) {
    this.setState('chart.selected', chartId);
    this.setState('ui.selectedChartMeta', chartMeta);
  },

  /**
   * 获取选中的图表
   */
  getSelectedChart() {
    return this.getState('chart.selected');
  },

  /**
   * 获取选中的图表元数据
   */
  getSelectedChartMeta() {
    return this.getState('ui.selectedChartMeta');
  },

  /**
   * 设置所有图表
   */
  setCharts(charts) {
    this.setState('chart.all', charts);
    this.setState('cache.charts', charts);
  },

  /**
   * 获取所有图表
   */
  getCharts() {
    return this.getState('chart.all');
  },

  /**
   * 设置图表选项
   */
  setChartOptions(options) {
    this.setState('chart.options', options);
  },

  /**
   * 获取图表选项
   */
  getChartOptions() {
    return this.getState('chart.options');
  },

  /**
   * 设置 LLM 配置
   */
  setLLMConfigs(configs) {
    this.setState('llm.configs', configs);
  },

  /**
   * 获取 LLM 配置
   */
  getLLMConfigs() {
    return this.getState('llm.configs');
  },

  /**
   * 设置当前 LLM 提供商
   */
  setCurrentProvider(provider) {
    this.setState('llm.provider', provider);
  },

  /**
   * 获取当前 LLM 提供商
   */
  getCurrentProvider() {
    return this.getState('llm.provider');
  },

  /**
   * 添加消息
   */
  addMessage(message, role = 'user') {
    const messages = this.getState('ui.messages');
    messages.push({
      id: Date.now(),
      text: message,
      role,
      timestamp: new Date(),
    });
    this.setState('ui.messages', messages);
  },

  /**
   * 获取所有消息
   */
  getMessages() {
    return this.getState('ui.messages');
  },

  /**
   * 清除消息
   */
  clearMessages() {
    this.resetState('ui.messages');
  },

  /**
   * 调试：打印当前状态
   */
  debug() {
    console.log('Current AppState:', JSON.parse(JSON.stringify(AppState)));
  },
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AppState, StateManager };
}
