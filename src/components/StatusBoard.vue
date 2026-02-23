<template>
  <div class="dashboard">
    <!-- 左侧菜单栏 -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <span class="logo-icon">◆</span>
        <span>Monitor</span>
      </div>
      <nav class="sidebar-nav">
        <div 
          v-for="item in menuItems" 
          :key="item.id"
          :class="['nav-item', { active: activeMenu === item.id }]"
          @click="activeMenu = item.id"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.label }}</span>
        </div>
      </nav>
    </aside>

    <!-- 主区域 -->
    <div class="main-area">
      <!-- 顶部导航栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">Components</h1>
        </div>
        <div class="topbar-center">
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索组件..."
            />
          </div>
        </div>
        <div class="topbar-right">
          <button class="export-btn" @click="exportToCsv">
            <span>⬇</span> Export CSV
          </button>
          <button class="icon-btn refresh-btn" @click="fetchData" :disabled="loading">
            <span :class="{ spinning: loading }">↻</span>
          </button>
          <button class="icon-btn">🔔</button>
          <div class="user-avatar">U</div>
          <div class="datetime">{{ currentTime }}</div>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="content">
        <div class="content-header">
          <div class="stats-cards">
            <div class="stat-card total">
              <div class="stat-value">{{ components.length }}</div>
              <div class="stat-label">Total</div>
            </div>
            <div class="stat-card healthy">
              <div class="stat-value">{{ healthyCount }}</div>
              <div class="stat-label">Healthy</div>
            </div>
            <div class="stat-card warning">
              <div class="stat-value">{{ warningCount }}</div>
              <div class="stat-label">Warning</div>
            </div>
            <div class="stat-card critical">
              <div class="stat-value">{{ criticalCount }}</div>
              <div class="stat-label">Critical</div>
            </div>
          </div>
        </div>

        <!-- 趋势图区域 -->
        <div class="chart-section">
          <div class="chart-header">
            <h3>Health Trend</h3>
            <select v-model="selectedComponent" class="component-select">
              <option v-for="comp in components" :key="comp.component_id" :value="comp.component_id">
                {{ comp.component_id }}
              </option>
            </select>
          </div>
          <div class="chart-container">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Component ID</th>
                <th>Heartbeat</th>
                <th>Files</th>
                <th>Level</th>
                <th>Health</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="comp in filteredComponents" 
                :key="comp.component_id"
                :class="['component-row', getRowHealthClass(comp)]"
              >
                <td class="component-id">{{ comp.component_id }}</td>
                <td>
                  <div class="status-badge" :class="getHeartbeatClass(comp)">
                    <span class="status-dot"></span>
                    <span>{{ getHeartbeatText(comp) }}</span>
                    <span v-if="comp.heartbeat?.last_heartbeat_at" class="time-tag">
                      {{ formatTimeShort(comp.heartbeat.last_heartbeat_at) }}
                    </span>
                  </div>
                </td>
                <td>
                  <div v-if="comp.file_status" class="status-badge" :class="comp.file_status.overall_file_health ? 'status-ok' : 'status-error'">
                    <span class="status-dot"></span>
                    <span>{{ comp.file_status.overall_file_health ? 'OK' : 'Error' }}</span>
                  </div>
                  <span v-else class="status-unknown">—</span>
                </td>
                <td>
                  <div v-if="comp.level_status" class="status-badge" :class="getLevelClass(comp)">
                    <span class="status-dot"></span>
                    <span>{{ comp.level_status.compliant ? 'Compliant' : 'Violation' }}</span>
                    <span class="level-badge">{{ comp.level_status.observed_level || '?' }}/{{ comp.level_status.expected_level }}</span>
                  </div>
                  <span v-else class="status-unknown">—</span>
                </td>
                <td>
                  <div class="health-indicator" :class="getOverallHealthClass(comp)">
                    <span class="health-icon">{{ getOverallHealthClass(comp) === 'health-good' ? '🟢' : '🔴' }}</span>
                    <span>{{ getOverallHealthClass(comp) === 'health-good' ? 'Healthy' : 'Critical' }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <!-- 底部状态栏 -->
      <footer class="statusbar">
        <div class="statusbar-left">
          <span class="status-item">Last Update: {{ lastUpdateTime }}</span>
        </div>
        <div class="statusbar-center">
          <span class="status-item">Total: {{ components.length }}</span>
          <span class="status-separator">|</span>
          <span class="status-item healthy">Normal: {{ healthyCount }}</span>
          <span class="status-separator">|</span>
          <span class="status-item error">Abnormal: {{ criticalCount }}</span>
        </div>
        <div class="statusbar-right">
          <span class="connection-status" :class="{ connected: isConnected }">
            <span class="connection-dot"></span>
            {{ isConnected ? 'Connected' : 'Disconnected' }}
          </span>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, shallowRef } from 'vue'

const components = ref([])
const searchQuery = ref('')
const lastUpdateTime = ref('—')
const currentTime = ref('')
const loading = ref(false)
const isConnected = ref(true)
const activeMenu = ref('components')
const timer = ref(null)
const timeTimer = ref(null)
const chartTimer = ref(null)
const chartCanvas = ref(null)
const selectedComponent = ref('')
const chartInstance = shallowRef(null)

// 使用普通对象存储历史数据，避免 Vue 响应式与 Chart.js 冲突
let historyData = {}

const menuItems = [
  { id: 'components', label: 'Components', icon: '◈' },
  { id: 'files', label: 'Files', icon: '◫' },
  { id: 'alerts', label: 'Alerts', icon: '◉' },
  { id: 'settings', label: 'Settings', icon: '◐' }
]

// 获取数据
const fetchData = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const res = await fetch('http://localhost:8000/api/v1/status')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    
    const data = await res.json()
    components.value = data.components || []
    lastUpdateTime.value = formatDateTime(new Date())
    
    // 如果还没有选中组件，默认选第一个
    if (components.value.length > 0 && !selectedComponent.value) {
      selectedComponent.value = components.value[0].component_id
    }
    isConnected.value = true
  } catch (err) {
    console.error('Failed to fetch status:', err)
    isConnected.value = false
    alert('Network error: ' + err.message)
  } finally {
    loading.value = false
  }
}

// 更新当前时间
const updateCurrentTime = () => {
  currentTime.value = formatDateTime(new Date())
}

const formatDateTime = (date) => {
  const pad = (n) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const formatTimeShort = (isoString) => {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}

// 过滤和排序组件
const filteredComponents = computed(() => {
  let result = components.value
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(c => c.component_id?.toLowerCase().includes(query))
  }
  
  // 按整体健康排序（异常在前）
  return result.sort((a, b) => {
    const aHealthy = getOverallHealthClass(a) === 'health-good'
    const bHealthy = getOverallHealthClass(b) === 'health-good'
    return aHealthy === bHealthy ? 0 : aHealthy ? 1 : -1
  })
})

// 统计数量
const healthyCount = computed(() => 
  components.value.filter(c => getOverallHealthClass(c) === 'health-good').length
)

const warningCount = computed(() => 
  components.value.filter(c => {
    const hb = c.heartbeat?.status
    return hb === 'warning' && getOverallHealthClass(c) !== 'health-good'
  }).length
)

const criticalCount = computed(() => 
  components.value.filter(c => getOverallHealthClass(c) !== 'health-good').length
)

// 状态判断函数
const getHeartbeatClass = (comp) => {
  if (!comp.heartbeat) return 'status-unknown'
  if (comp.heartbeat.status === 'healthy') return 'status-ok'
  if (comp.heartbeat.status === 'warning') return 'status-warning'
  return 'status-error'
}

const getHeartbeatText = (comp) => {
  if (!comp.heartbeat) return 'Unknown'
  if (comp.heartbeat.status === 'healthy') return 'Alive'
  return 'Down'
}

const getLevelClass = (comp) => {
  if (!comp.level_status) return 'status-unknown'
  if (comp.level_status.compliant) return 'status-ok'
  return 'status-warning'
}

const getOverallHealthClass = (comp) => {
  const hbOk = comp.heartbeat?.status === 'healthy'
  const fileOk = comp.file_status?.overall_file_health !== false
  const levelOk = comp.level_status?.compliant !== false
  
  return hbOk && fileOk && levelOk ? 'health-good' : 'health-bad'
}

const getRowHealthClass = (comp) => {
  return getOverallHealthClass(comp) === 'health-good' ? 'row-healthy' : 'row-critical'
}

// 获取文件状态文本
const getFileStatusText = (comp) => {
  if (!comp.file_status) return 'Unknown'
  return comp.file_status.overall_file_health ? 'OK' : 'Error'
}

// 获取等级合规文本
const getLevelStatusText = (comp) => {
  if (!comp.level_status) return 'Unknown'
  return comp.level_status.compliant ? 'Compliant' : 'Violation'
}

// 获取整体健康文本
const getOverallHealthText = (comp) => {
  return getOverallHealthClass(comp) === 'health-good' ? 'Healthy' : 'Critical'
}

// 导出 CSV
const exportToCsv = () => {
  if (filteredComponents.value.length === 0) {
    alert('No data to export')
    return
  }

  // CSV 头部
  const headers = ['Component ID', 'Heartbeat', 'File Update', 'Level Compliance', 'Overall Health']
  
  // CSV 数据行
  const rows = filteredComponents.value.map(comp => [
    comp.component_id,
    getHeartbeatText(comp),
    getFileStatusText(comp),
    getLevelStatusText(comp),
    getOverallHealthText(comp)
  ])
  
  // 组合 CSV 内容
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
  
  // 创建 Blob
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  
  // 创建下载链接
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  // 设置文件名（包含时间戳）
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
  link.setAttribute('href', url)
  link.setAttribute('download', `component-status-${timestamp}.csv`)
  
  // 触发下载
  document.body.appendChild(link)
  link.click()
  
  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 更新历史数据
const updateHistoryData = () => {
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  
  // 先将组件数据转换为普通对象，避免响应式污染
  const plainComponents = components.value.map(comp => ({
    component_id: comp.component_id,
    heartbeat_status: comp.heartbeat?.status,
    file_health: comp.file_status?.overall_file_health,
    level_compliant: comp.level_status?.compliant
  }))
  
  plainComponents.forEach(comp => {
    const id = comp.component_id
    if (!historyData[id]) {
      historyData[id] = { labels: [], data: [] }
    }
    
    const history = historyData[id]
    history.labels.push(now)
    
    // 直接计算分数，避免访问响应式对象
    let score = 0
    if (comp.heartbeat_status === 'healthy') score += 40
    if (comp.file_health) score += 30
    if (comp.level_compliant) score += 30
    history.data.push(score)
    
    // 只保留最近 20 个数据点
    if (history.labels.length > 20) {
      history.labels.shift()
      history.data.shift()
    }
  })
  
  // 更新图表
  updateChart()
}

// 初始化图表
const initChart = () => {
  if (!chartCanvas.value || chartInstance.value) return
  
  const ctx = chartCanvas.value.getContext('2d')
  
  // 创建完全独立的数据对象，避免 Vue 响应式污染
  const chartData = {
    labels: [],
    datasets: [{
      label: 'Health Score',
      data: [],
      borderColor: '#00d4ff',
      backgroundColor: 'rgba(0, 212, 255, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointBackgroundColor: '#00d4ff'
    }]
  }
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1a2547',
        titleColor: '#e8ecf4',
        bodyColor: '#e8ecf4',
        borderColor: '#00d4ff',
        borderWidth: 1,
        displayColors: false
      }
    },
    scales: {
      x: {
        grid: { color: '#1a2547' },
        ticks: { color: '#8b9dc3', maxTicksLimit: 6 }
      },
      y: {
        min: 0,
        max: 100,
        grid: { color: '#1a2547' },
        ticks: { color: '#8b9dc3', stepSize: 20 }
      }
    }
  }
  
  chartInstance.value = new window.Chart(ctx, {
    type: 'line',
    data: chartData,
    options: chartOptions
  })
}

// 更新图表
const updateChart = () => {
  if (!chartInstance.value || !selectedComponent.value) return
  
  const history = historyData[selectedComponent.value]
  if (!history || history.labels.length === 0) return
  
  // 完全解耦数据，避免 Vue 响应式污染
  const labels = JSON.parse(JSON.stringify(history.labels))
  const data = JSON.parse(JSON.stringify(history.data))
  
  chartInstance.value.data.labels = labels
  chartInstance.value.data.datasets[0].data = data
  chartInstance.value.update()
}

// 监听组件选择变化
watch(selectedComponent, () => {
  updateChart()
})

onMounted(async () => {
  await fetchData()
  timer.value = setInterval(fetchData, 10000)
  updateCurrentTime()
  timeTimer.value = setInterval(updateCurrentTime, 1000)
  
  // 等待 DOM 完全渲染后再初始化图表
  await nextTick()
  
  setTimeout(() => {
    // 设置默认选中的组件
    if (components.value.length > 0 && !selectedComponent.value) {
      selectedComponent.value = components.value[0].component_id
    }
    
    // 初始化图表
    initChart()
    
    // 立即记录一次历史数据
    if (selectedComponent.value) {
      updateHistoryData()
    }
  }, 100)
  
  // 启动历史数据记录
  chartTimer.value = setInterval(updateHistoryData, 10000)
})

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
  if (timeTimer.value) clearInterval(timeTimer.value)
  if (chartTimer.value) clearInterval(chartTimer.value)
  if (chartInstance.value) chartInstance.value.destroy()
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.dashboard {
  display: flex;
  min-height: 100vh;
  background: #0a1028;
  color: #e8ecf4;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 左侧菜单栏 */
.sidebar {
  width: 200px;
  background: #0d1430;
  border-right: 1px solid #1a2547;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  z-index: 100;
}

.sidebar-logo {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
  color: #00d4ff;
  border-bottom: 1px solid #1a2547;
}

.logo-icon {
  font-size: 24px;
  color: #00d4ff;
}

.sidebar-nav {
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #8b9dc3;
}

.nav-item:hover {
  background: #1a2547;
  color: #e8ecf4;
}

.nav-item.active {
  background: #00d4ff22;
  color: #00d4ff;
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
}

/* 主区域 */
.main-area {
  flex: 1;
  margin-left: 200px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶部导航栏 */
.topbar {
  height: 64px;
  background: #0d1430;
  border-bottom: 1px solid #1a2547;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #e8ecf4;
}

.topbar-center {
  flex: 1;
  max-width: 400px;
  margin: 0 24px;
}

.search-box {
  display: flex;
  align-items: center;
  background: #1a2547;
  border: 1px solid #2a3655;
  border-radius: 8px;
  padding: 0 12px;
  height: 40px;
}

.search-icon {
  color: #8b9dc3;
  margin-right: 8px;
}

.search-box input {
  background: transparent;
  border: none;
  color: #e8ecf4;
  font-size: 14px;
  outline: none;
  width: 100%;
}

.search-box input::placeholder {
  color: #5a6a8a;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: #1a2547;
  color: #8b9dc3;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: #2a3655;
  color: #e8ecf4;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #00d4ff22;
  border: 1px solid #00d4ff;
  border-radius: 8px;
  color: #00d4ff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.export-btn:hover {
  background: #00d4ff44;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
}

.datetime {
  font-size: 13px;
  color: #8b9dc3;
  font-family: 'SF Mono', monospace;
}

/* 主内容区 */
.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.content-header {
  margin-bottom: 24px;
}

.stats-cards {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-card {
  background: #0d1430;
  border: 1px solid #1a2547;
  border-radius: 12px;
  padding: 20px 24px;
  min-width: 120px;
  text-align: center;
}

.stat-card.total {
  border-color: #3a4a6a;
}

.stat-card.healthy {
  border-color: #00d4ff;
  background: #00d4ff11;
}

.stat-card.warning {
  border-color: #f5a623;
  background: #f5a62311;
}

.stat-card.critical {
  border-color: #ff4757;
  background: #ff475711;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #e8ecf4;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #8b9dc3;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 图表区域 */
.chart-section {
  background: #0d1430;
  border: 1px solid #1a2547;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8ecf4;
  margin: 0;
}

.component-select {
  padding: 8px 16px;
  background: #1a2547;
  border: 1px solid #2a3655;
  border-radius: 8px;
  color: #e8ecf4;
  font-size: 14px;
  cursor: pointer;
  outline: none;
  min-width: 180px;
}

.component-select option {
  background: #0d1430;
  color: #e8ecf4;
}

.chart-container {
  height: 280px;
  position: relative;
}

/* 表格 */
.table-container {
  background: #0d1430;
  border: 1px solid #1a2547;
  border-radius: 12px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #1a2547;
}

.data-table th {
  padding: 16px 20px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #8b9dc3;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  padding: 16px 20px;
  border-bottom: 1px solid #1a2547;
  font-size: 14px;
}

.component-row {
  transition: background 0.2s;
}

.component-row:hover {
  background: #1a2547;
}

.component-row.row-critical {
  background: #ff475711;
}

.component-row.row-critical:hover {
  background: #ff475722;
}

.component-id {
  font-family: 'SF Mono', monospace;
  font-weight: 600;
  color: #00d4ff;
}

/* 状态徽章 */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-ok {
  background: #00d4ff22;
  color: #00d4ff;
}

.status-ok .status-dot {
  background: #00d4ff;
  box-shadow: 0 0 8px #00d4ff;
}

.status-error {
  background: #ff475722;
  color: #ff4757;
}

.status-error .status-dot {
  background: #ff4757;
  box-shadow: 0 0 8px #ff4757;
}

.status-warning {
  background: #f5a62322;
  color: #f5a623;
}

.status-warning .status-dot {
  background: #f5a623;
}

.status-unknown {
  color: #5a6a8a;
}

.time-tag {
  font-size: 11px;
  color: #8b9dc3;
  margin-left: 8px;
  font-family: 'SF Mono', monospace;
}

.level-badge {
  background: #1a2547;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 8px;
  color: #8b9dc3;
}

.health-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.health-indicator.health-good {
  color: #00d4ff;
}

.health-indicator.health-bad {
  color: #ff4757;
}

.health-icon {
  font-size: 16px;
}

/* 底部状态栏 */
.statusbar {
  height: 48px;
  background: #0d1430;
  border-top: 1px solid #1a2547;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  font-size: 13px;
}

.statusbar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-item {
  color: #8b9dc3;
}

.status-item.healthy {
  color: #00d4ff;
}

.status-item.error {
  color: #ff4757;
}

.status-separator {
  color: #3a4a6a;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ff4757;
}

.connection-status.connected {
  color: #00d4ff;
}

.connection-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

/* 响应式 */
@media (max-width: 1024px) {
  .sidebar {
    width: 64px;
  }
  
  .nav-text {
    display: none;
  }
  
  .main-area {
    margin-left: 64px;
  }
  
  .sidebar-logo span:last-child {
    display: none;
  }
}

@media (max-width: 768px) {
  .topbar-center {
    display: none;
  }
  
  .stats-cards {
    justify-content: center;
  }
  
  .stat-card {
    min-width: 80px;
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}
</style>
