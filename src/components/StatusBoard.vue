<template>
  <div class="status-board">
    <div class="header">
      <h2>交易组件监控面板</h2>
      <div class="controls">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索组件..."
          class="search-input"
        />
        <button @click="fetchData" class="refresh-btn" :disabled="loading">
          {{ loading ? '刷新中...' : '手动刷新' }}
        </button>
      </div>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>组件 ID</th>
            <th>心跳状态</th>
            <th>文件更新</th>
            <th>运行等级</th>
            <th>整体健康</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="comp in filteredComponents"
            :key="comp.component_id"
            class="component-row"
          >
            <td class="component-id">{{ comp.component_id }}</td>
            
            <td>
              <div class="status-cell">
                <span :class="['status-dot', getHeartbeatClass(comp)]"></span>
                <span :class="['status-text', getHeartbeatTextClass(comp)]">
                  {{ getHeartbeatText(comp) }}
                </span>
                <span v-if="comp.heartbeat?.last_heartbeat_at" class="time-hint">
                  {{ formatTime(comp.heartbeat.last_heartbeat_at) }}
                </span>
              </div>
            </td>

            <td>
              <div v-if="comp.file_status" class="file-status">
                <div 
                  class="status-cell file-cell"
                  @mouseenter="showFileTooltip($event, comp)"
                  @mouseleave="hideFileTooltip"
                >
                  <span :class="['status-dot', comp.file_status.overall_file_health ? 'dot-success' : 'dot-error']"></span>
                  <span :class="['status-text', comp.file_status.overall_file_health ? 'text-success' : 'text-error']">
                    {{ comp.file_status.overall_file_health ? '正常' : '异常' }}
                  </span>
                </div>
              </div>
              <span v-else class="dash">—</span>
            </td>

            <td>
              <div v-if="comp.level_status" class="status-cell">
                <span :class="['status-dot', comp.level_status.compliant ? 'dot-success' : 'dot-warning']"></span>
                <span :class="['status-text', comp.level_status.compliant ? 'text-success' : 'text-warning']">
                  {{ comp.level_status.compliant ? '合规' : '违规' }}
                </span>
                <span class="level-hint">
                  {{ comp.level_status.observed_level || '?' }} / {{ comp.level_status.expected_level }}
                </span>
              </div>
              <span v-else class="dash">—</span>
            </td>

            <td>
              <div class="status-cell">
                <span :class="['status-dot', getOverallHealthClass(comp) === 'health-good' ? 'dot-success' : 'dot-error']"></span>
                <span :class="['status-text', getOverallHealthClass(comp) === 'health-good' ? 'text-success' : 'text-error']">
                  {{ getOverallHealthText(comp) }}
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="footer">
      <span>最后更新: {{ lastUpdateTime }}</span>
      <span class="count">共 {{ filteredComponents.length }} 个组件</span>
    </div>

    <!-- 文件详情 Tooltip -->
    <div 
      v-if="tooltip.visible" 
      class="file-tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      <div class="tooltip-title">文件详情</div>
      <div v-for="(file, idx) in tooltip.files" :key="idx" class="tooltip-item">
        <div class="tooltip-path">{{ file.path }}</div>
        <div class="tooltip-time">
          修改时间: {{ file.last_modified ? formatTime(file.last_modified) : '从未' }}
        </div>
        <div :class="['tooltip-status', file.is_compliant ? 'success' : 'error']">
          {{ file.is_compliant ? '✓ 合规' : '✗ 不合规' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const components = ref([])
const searchQuery = ref('')
const lastUpdateTime = ref('—')
const loading = ref(false)
const timer = ref(null)

const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  files: []
})

// 获取数据
const fetchData = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const res = await fetch('http://localhost:8000/api/v1/status')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    
    const data = await res.json()
    components.value = data.components || []
    lastUpdateTime.value = new Date().toLocaleString()
  } catch (err) {
    console.error('Failed to fetch status:', err)
    alert('网络错误: ' + err.message)
  } finally {
    loading.value = false
  }
}

// 过滤和排序
const filteredComponents = computed(() => {
  let result = components.value
  
  // 搜索过滤
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

// 心跳状态相关
const getHeartbeatClass = (comp) => {
  if (!comp.heartbeat) return 'dot-none'
  if (comp.heartbeat.status === 'healthy') return 'dot-success'
  if (comp.heartbeat.status === 'warning') return 'dot-warning'
  return 'dot-error'
}

const getHeartbeatTextClass = (comp) => {
  if (!comp.heartbeat) return 'text-muted'
  if (comp.heartbeat.status === 'healthy') return 'text-success'
  if (comp.heartbeat.status === 'warning') return 'text-warning'
  return 'text-error'
}

const getHeartbeatText = (comp) => {
  if (!comp.heartbeat) return '未知'
  if (comp.heartbeat.status === 'healthy') return '存活'
  return '宕机'
}

// 整体健康
const getOverallHealthClass = (comp) => {
  const hbOk = comp.heartbeat?.status === 'healthy'
  const fileOk = comp.file_status?.overall_file_health !== false
  const levelOk = comp.level_status?.compliant !== false
  
  return hbOk && fileOk && levelOk ? 'health-good' : 'health-bad'
}

const getOverallHealthText = (comp) => {
  return getOverallHealthClass(comp) === 'health-good' ? '正常' : '异常'
}

// 文件 tooltip
const showFileTooltip = (event, comp) => {
  if (!comp.file_status) return
  
  const files = []
  
  // 收集输入文件
  if (comp.file_status.input_files) {
    comp.file_status.input_files.forEach(f => {
      files.push({ ...f, type: '输入' })
    })
  }
  
  // 收集输出文件
  if (comp.file_status.output_files) {
    comp.file_status.output_files.forEach(f => {
      files.push({ ...f, type: '输出' })
    })
  }
  
  tooltip.value = {
    visible: true,
    x: event.clientX + 10,
    y: event.clientY + 10,
    files
  }
}

const hideFileTooltip = () => {
  tooltip.value.visible = false
}

// 时间格式化
const formatTime = (isoString) => {
  if (!isoString) return '—'
  try {
    const date = new Date(isoString)
    return date.toLocaleString()
  } catch {
    return isoString
  }
}

// 生命周期
onMounted(() => {
  fetchData()
  timer.value = setInterval(fetchData, 10000)
})

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
})
</script>

<style scoped>
.status-board {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

.controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  width: 200px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #409eff;
}

.refresh-btn {
  padding: 10px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.refresh-btn:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}

.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8f9fa;
}

th {
  padding: 16px 20px;
  text-align: left;
  font-weight: 600;
  color: #606266;
  font-size: 14px;
  border-bottom: 1px solid #ebeef5;
}

.component-row {
  transition: background 0.2s;
}

.component-row:hover {
  background: #f5f7fa;
}

td {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  font-size: 14px;
}

.component-id {
  font-weight: 500;
  color: #303133;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-success {
  background: #67c23a;
}

.dot-error {
  background: #f56c6c;
}

.dot-warning {
  background: #e6a23c;
}

.dot-none {
  background: #c0c4cc;
}

.status-text {
  font-weight: 500;
}

.text-success {
  color: #67c23a;
}

.text-error {
  color: #f56c6c;
}

.text-warning {
  color: #e6a23c;
}

.text-muted {
  color: #909399;
}

.time-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.level-hint {
  font-size: 12px;
  color: #606266;
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.file-cell {
  cursor: help;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.file-cell:hover {
  background: #e6f2ff;
}

.dash {
  color: #c0c4cc;
}

.footer {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
  font-size: 13px;
  color: #909399;
}

.count {
  font-weight: 500;
}

/* Tooltip */
.file-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-width: 400px;
  min-width: 300px;
}

.tooltip-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 12px;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.tooltip-item {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.tooltip-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.tooltip-path {
  font-size: 13px;
  color: #606266;
  word-break: break-all;
  margin-bottom: 4px;
}

.tooltip-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.tooltip-status {
  font-size: 12px;
  font-weight: 500;
}

.tooltip-status.success {
  color: #67c23a;
}

.tooltip-status.error {
  color: #f56c6c;
}
</style>
