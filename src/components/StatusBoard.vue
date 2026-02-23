<template>
  <div class="status-board">
    <h2>交易组件监控面板</h2>
    <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%;">
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
        <tr v-for="comp in components" :key="comp.component_id">
          <td>{{ comp.component_id }}</td>
          <td>
            <span :class="getStatusClass(comp.heartbeat?.status === 'healthy')">
              {{ comp.heartbeat?.status === 'healthy' ? '存活' : (comp.heartbeat?.status || '未知') }}
            </span>
          </td>
          <td>
            <span v-if="comp.file_status">
              <span :class="getStatusClass(comp.file_status.overall_file_health)">
                {{ comp.file_status.overall_file_health ? '正常' : '异常' }}
              </span>
            </span>
            <span v-else>—</span>
          </td>
          <td>
            <span v-if="comp.level_status">
              实际: {{ comp.level_status.observed_level || '?' }} / 
              期望: {{ comp.level_status.expected_level }}
              <span :class="getStatusClass(comp.level_status.compliant)">
                {{ comp.level_status.compliant ? '✓' : '✗' }}
              </span>
            </span>
            <span v-else>—</span>
          </td>
          <td>
            <span :class="getOverallHealthClass(comp)"></span>
          </td>
        </tr>
      </tbody>
    </table>
    <p>最后更新: {{ lastUpdateTime }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const components = ref([])
const lastUpdateTime = ref('—')

// 状态颜色映射
const getStatusClass = (isOk) => {
  return isOk === true ? 'status-ok' : isOk === false ? 'status-error' : 'status-unknown'
}

// 整体健康状态
const getOverallHealthClass = (comp) => {
  const hbOk = comp.heartbeat?.status === 'healthy'
  const fileOk = comp.file_status?.overall_file_health !== false
  const levelOk = comp.level_status?.compliant !== false
  
  if (!hbOk || !fileOk || !levelOk) return 'health-bad'
  return 'health-good'
}

// 轮询后端
const fetchData = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/v1/status')
    if (!res.ok) throw new Error('API error')
    const data = await res.json()
    // 修复：使用 data.components 数组
    components.value = data.components || []
    lastUpdateTime.value = new Date().toLocaleTimeString()
  } catch (err) {
    console.error('Failed to fetch status:', err)
    components.value = []
  }
}

onMounted(() => {
  fetchData()
  setInterval(fetchData, 5000) // 每5秒刷新
})
</script>

<style scoped>
.status-ok { color: #4ade80; font-weight: bold; }
.status-error { color: #f87171; font-weight: bold; }
.status-unknown { color: #fbbf24; }

.health-good::before { 
  content: "🟢"; 
  font-size: 20px;
}
.health-bad::before { 
  content: "🔴"; 
  font-size: 20px;
}

.status-board {
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f172a;
  color: #e2e8f0;
  min-height: 100vh;
}

h2 {
  margin-bottom: 16px;
  color: #fff;
}

table {
  background: #1e293b;
  border-color: #334155;
}

th {
  background: #334155;
  color: #fff;
}

td {
  color: #cbd5e1;
}

p {
  margin-top: 16px;
  color: #94a3b8;
}
</style>
