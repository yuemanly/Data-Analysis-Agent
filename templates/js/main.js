/**
 * main.js - 主应用逻辑
 * 事件注册、初始化、业务逻辑
 */

class ChartApp {
  constructor() {
    this.selectedCardEl = null; // 性能优化：缓存当前选中卡片
    this.init();
  }

  async init() {
    this.registerEventListeners();
    await this.loadInitialData();
    this.setupStateListeners();
  }

  registerEventListeners() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (uploadArea) {
      uploadArea.addEventListener('click', () => fileInput?.click());
      uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#ECF3F9';
      });
      uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = '';
      });
      uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.background = '';
        if (e.dataTransfer.files?.length) this.handleFileUpload(e.dataTransfer.files[0]);
      });
    }

    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        if (e.target.files?.length) this.handleFileUpload(e.target.files[0]);
      });
    }

    document.getElementById('generateBtn')?.addEventListener('click', () => this.generateChart());
    document.getElementById('sendBtn')?.addEventListener('click', () => this.sendMessage());
    document.getElementById('saveConfigBtn')?.addEventListener('click', () => this.saveConfig());
    document.getElementById('testConfigBtn')?.addEventListener('click', () => this.testConfig());
    document.getElementById('addCustomBtn')?.addEventListener('click', () => this.showAddCustomModal());
    document.getElementById('cancelCustomBtn')?.addEventListener('click', () => this.hideAddCustomModal());
    document.getElementById('confirmCustomBtn')?.addEventListener('click', () => this.addCustomModel());

    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }
  }

  async loadInitialData() {
    try {
      const chartsData = await ChartAPI.getCharts();
      if (chartsData.charts) {
        StateManager.setCharts(chartsData.charts);
        this.renderCharts(chartsData.charts);
      }

      // 修正：LLMAPI 命名
      const llmData = await LLMAPI.listConfigs();
      if (llmData.configs) {
        StateManager.setLLMConfigs(llmData.configs);
        this.renderLLMProviders(llmData.configs);
      }
    } catch (error) {
      UIUtils.showToast(`加载数据失败: ${error.message}`, 'error');
      console.error('Failed to load initial data:', error);
    }
  }

  setupStateListeners() {
    StateManager.on('stateChange', ({ path, value }) => {
      console.log(`State changed: ${path}`, value);
    });
  }

  async handleFileUpload(file) {
    const maxSize = 20 * 1024 * 1024;
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv',
    ];

    if (file.size > maxSize) {
      UIUtils.showToast(`文件过大，最大 ${UIUtils.formatFileSize(maxSize)}`, 'warning');
      return;
    }

    if (!allowedTypes.includes(file.type)) {
      UIUtils.showToast('仅支持 Excel (.xlsx) 和 CSV 文件', 'warning');
      return;
    }

    StateManager.setLoading('upload', true);

    try {
      const data = await ChartAPI.uploadFile(file);
      if (data.filepath) {
        StateManager.setFile(data.filepath, file.name, file.size);
        UIUtils.showToast(`文件上传成功: ${file.name}`, 'success');
        await this.analyzeData(data.filepath);
      }
    } catch (error) {
      UIUtils.showToast(`上传失败: ${error.message}`, 'error');
    } finally {
      StateManager.setLoading('upload', false);
    }
  }

  async analyzeData(filepath) {
    StateManager.setLoading('analyze', true);

    try {
      const provider = document.getElementById('provider')?.value || undefined;
      // 修正：analyzeData 传对象
      const data = await ChartAPI.analyzeData({
        filepath,
        query: '请推荐最适合的图表类型并说明原因',
        provider,
      });

      if (data.recommendations) this.displayRecommendations(data.recommendations);
    } catch (error) {
      UIUtils.showToast(`分析失败: ${error.message}`, 'error');
    } finally {
      StateManager.setLoading('analyze', false);
    }
  }

  displayRecommendations(recommendations) {
    const recText = recommendations.map(rec => {
      const zh = rec.name_zh || rec.name || '';
      const en = rec.name_en || rec.chart_id || '';
      return `${rec.stars || ''} ${zh}${en ? `（${en}）` : ''}\n${rec.reason || ''}`;
    }).join('\n\n---\n\n');

    this.addMessage('=== 推荐图表 ===\n\n' + recText, 'bot');
  }

  async generateChart() {
    const selectedChart = StateManager.getSelectedChart();
    const file = StateManager.getFile();

    if (!selectedChart) return UIUtils.showToast('请先选择图表', 'warning');
    if (!file.path) return UIUtils.showToast('请先上传文件', 'warning');

    const generateBtn = document.getElementById('generateBtn');
    StateManager.setLoading('generate', true);
    UIUtils.setButtonLoading(generateBtn, true, '生成中...');

    try {
      const colorScheme = document.getElementById('colorScheme')?.value || 'mckinsey';
      const chartOptions = this.collectChartOptions();

      // 修正：generateChart 传对象
      const data = await ChartAPI.generateChart({
        filepath: file.path,
        chartType: selectedChart,
        colorScheme,
        options: chartOptions,
      });

      if (data.success) {
        UIUtils.showToast('生成成功', 'success');
        if (data.download_url) {
          ChartAPI.openDownloadByURL(data.download_url);
        } else if (data.filename) {
          ChartAPI.openDownloadByFilename(data.filename);
        }
      } else {
        throw new Error(data.error || '生成失败');
      }
    } catch (error) {
      UIUtils.showToast(`生成失败: ${error.message}`, 'error');
    } finally {
      StateManager.setLoading('generate', false);
      UIUtils.setButtonLoading(generateBtn, false);
    }
  }

  collectChartOptions() {
    const options = {};
    const optionInputs = document.getElementById('chartOptions')?.querySelectorAll('input, select') || [];
    optionInputs.forEach(input => {
      const name = input.id?.replace('opt_', '');
      if (!name) return;
      options[name] = input.type === 'checkbox' ? input.checked : input.value;
    });
    return options;
  }

  async sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput?.value?.trim();
    if (!message) return UIUtils.showToast('请输入消息', 'warning');

    this.addMessage(message, 'user');
    chatInput.value = '';

    const sendBtn = document.getElementById('sendBtn');
    UIUtils.setButtonLoading(sendBtn, true);

    try {
      // 修正：LLMAPI 命名
      const data = await LLMAPI.sendMessage(message);
      if (data.response) this.addMessage(data.response, 'bot');
    } catch (error) {
      UIUtils.showToast(`发送失败: ${error.message}`, 'error');
    } finally {
      UIUtils.setButtonLoading(sendBtn, false);
    }
  }

  addMessage(text, role = 'user') {
    const messagesEl = document.getElementById('chatMessages');
    if (!messagesEl) return;
    const messageEl = document.createElement('div');
    messageEl.className = `chat-message chat-message-${role}`;
    messageEl.textContent = text;
    messagesEl.appendChild(messageEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    StateManager.addMessage(text, role);
  }

  async saveConfig() {
    const provider = document.getElementById('provider')?.value;
    const apiKey = document.getElementById('apiKey')?.value?.trim();
    if (!provider || !apiKey) return UIUtils.showToast('请填写完整信息', 'warning');

    const saveBtn = document.getElementById('saveConfigBtn');
    UIUtils.setButtonLoading(saveBtn, true);

    try {
      const data = await LLMAPI.saveConfig(provider, apiKey);
      UIUtils.showToast(data.message || '配置已保存', 'success');
    } catch (error) {
      UIUtils.showToast(`保存失败: ${error.message}`, 'error');
    } finally {
      UIUtils.setButtonLoading(saveBtn, false);
    }
  }

  async testConfig() {
    const provider = document.getElementById('provider')?.value;
    if (!provider) return UIUtils.showToast('请选择提供商', 'warning');

    const testBtn = document.getElementById('testConfigBtn');
    UIUtils.setButtonLoading(testBtn, true);

    try {
      const data = await LLMAPI.testConfig(provider);
      if (data.success) {
        UIUtils.showToast(`✓ 配置有效\n提供商: ${data.provider}\n模型: ${data.model}`, 'success');
      } else {
        UIUtils.showToast(`✗ 配置无效\n${data.message}`, 'error');
      }
    } catch (error) {
      UIUtils.showToast(`测试失败: ${error.message}`, 'error');
    } finally {
      UIUtils.setButtonLoading(testBtn, false);
    }
  }

  showAddCustomModal() {
    document.getElementById('customModelModal')?.classList.add('show');
  }

  hideAddCustomModal() {
    document.getElementById('customModelModal')?.classList.remove('show');
    ['customName', 'customBaseUrl', 'customModelName', 'customApiKey'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
  }

  async addCustomModel() {
    const name = document.getElementById('customName')?.value?.trim();
    const baseUrl = document.getElementById('customBaseUrl')?.value?.trim();
    const modelName = document.getElementById('customModelName')?.value?.trim();
    const apiKey = document.getElementById('customApiKey')?.value?.trim();

    if (!name || !baseUrl || !modelName || !apiKey) {
      return UIUtils.showToast('请完整填写所有字段', 'warning');
    }

    const confirmBtn = document.getElementById('confirmCustomBtn');
    UIUtils.setButtonLoading(confirmBtn, true);

    try {
      const data = await LLMAPI.addCustomModel(name, baseUrl, modelName, apiKey);
      if (data.success) {
        UIUtils.showToast(`✓ 添加成功\nProvider ID: ${data.provider_id}`, 'success');
        this.hideAddCustomModal();
        await this.loadInitialData();
      } else {
        throw new Error(data.error || '添加失败');
      }
    } catch (error) {
      UIUtils.showToast(`添加失败: ${error.message}`, 'error');
    } finally {
      UIUtils.setButtonLoading(confirmBtn, false);
    }
  }

  renderCharts(charts) {
    const grid = document.getElementById('chartsGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const frag = document.createDocumentFragment();
    const categories = {};
    charts.forEach(chart => {
      const cat = chart.category || '其他';
      (categories[cat] ||= []).push(chart);
    });

    Object.entries(categories).forEach(([cat, items]) => {
      const section = document.createElement('div');
      section.className = 'chart-category';

      const title = document.createElement('div');
      title.className = 'chart-category-title';
      title.innerHTML = `${cat} <span class="count">(${items.length})</span>`;
      section.appendChild(title);

      const wrap = document.createElement('div');
      wrap.className = 'chart-cards-wrap';

      items.forEach(chart => {
        const card = document.createElement('div');
        card.className = 'chart-card';
        card.tabIndex = 0;
        card.setAttribute('role', 'button');
        card.setAttribute('aria-label', `选择 ${chart.name}`);

        const zh = chart.name_zh || chart.name || '';
        const en = chart.name_en || chart.chart_id || '';
        card.textContent = zh && en ? `${zh}（${en}）` : (zh || en || '未命名图表');
        card.title = `${chart.desc || ''}（双击查看详情）`;
        card.dataset.chartId = chart.chart_id;

        card.addEventListener('click', () => this.selectChart(chart, card));
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.selectChart(chart, card);
          }
        });
        card.addEventListener('dblclick', () => {
          window.open(`/chart-detail?chart_id=${chart.chart_id}`, '_blank');
        });

        wrap.appendChild(card);
      });

      section.appendChild(wrap);
      frag.appendChild(section);
    });

    grid.appendChild(frag);
  }

  selectChart(chart, cardEl) {
    if (this.selectedCardEl && this.selectedCardEl !== cardEl) {
      this.selectedCardEl.classList.remove('selected');
    }
    cardEl.classList.add('selected');
    this.selectedCardEl = cardEl;

    StateManager.setSelectedChart(chart.chart_id, chart);
    this.showChartOptions(chart);
  }

  showChartOptions(chart) {
    const container = document.getElementById('chartOptionsContainer');
    const optionsDiv = document.getElementById('chartOptions');

    if (!chart.options || chart.options.length === 0) {
      if (container) container.style.display = 'none';
      return;
    }

    if (container) container.style.display = 'block';
    if (optionsDiv) optionsDiv.innerHTML = '';

    chart.options.forEach(opt => {
      const row = document.createElement('div');
      row.className = 'setting-row';
      row.style.marginBottom = '8px';

      const label = document.createElement('label');
      label.textContent = opt.label || opt.name;
      label.style.fontSize = '12px';
      label.style.marginBottom = '4px';
      label.style.display = 'block';
      row.appendChild(label);

      let control;
      if (opt.type === 'boolean') {
        control = document.createElement('input');
        control.type = 'checkbox';
        control.id = `opt_${opt.name}`;
        control.checked = opt.default !== false;
        control.style.marginRight = '6px';

        const span = document.createElement('span');
        span.textContent = opt.description || '';
        span.style.fontSize = '11px';
        span.style.color = '#666';

        row.appendChild(control);
        row.appendChild(span);
      } else if (opt.type === 'number') {
        control = document.createElement('input');
        control.type = 'number';
        control.id = `opt_${opt.name}`;
        control.value = opt.default || 0;
        control.style.width = '100%';
        control.style.padding = '4px';
        row.appendChild(control);
      } else if (opt.type === 'select') {
        control = document.createElement('select');
        control.id = `opt_${opt.name}`;
        control.style.width = '100%';
        control.style.padding = '4px';

        (opt.options || []).forEach(o => {
          const op = document.createElement('option');
          op.value = o.value || o;
          op.textContent = o.label || o;
          control.appendChild(op);
        });

        row.appendChild(control);
      }

      optionsDiv?.appendChild(row);
    });
  }

  renderLLMProviders(configs) {
    const select = document.getElementById('provider');
    if (!select) return;

    select.innerHTML = '';
    Object.entries(configs).forEach(([key, cfg]) => {
      const option = document.createElement('option');
      option.value = key;
      option.textContent = cfg.is_custom ? `[自定义] ${cfg.model || key}` : (cfg.provider || key);
      select.appendChild(option);
    });

    if (!select.options.length) {
      select.innerHTML = '<option value="">暂无可用提供商</option>';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new ChartApp();
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ChartApp };
}