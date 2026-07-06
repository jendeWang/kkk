<template>
  <span class="status-badge" :class="statusClass">
    <span class="status-dot"></span>
    <span class="status-text">{{ statusText }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'offline' },
})

const statusClass = computed(() => {
  return `status-${props.status}`
})

const statusText = computed(() => {
  const map = {
    online: '在线',
    offline: '离线',
    error: '异常',
    connecting: '连接中',
  }
  return map[props.status] || props.status
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-online {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.status-offline {
  background: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.status-error {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.status-connecting {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.status-online .status-dot {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>