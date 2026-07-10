<template>
  <div class="sensor-card" :class="{ 'status-warning': isWarning, 'status-error': isError }">
    <div class="sensor-icon"><SvgIcon :name="icon" :size="32" /></div>
    <div class="sensor-info">
      <div class="sensor-name">{{ name }}</div>
      <div class="sensor-value">
        <span class="value">{{ displayValue }}</span>
        <span class="unit">{{ unit }}</span>
      </div>
    </div>
    <div class="sensor-status" v-if="normalRange">
      <div class="range-bar">
        <div class="range-fill" :style="rangeStyle"></div>
      </div>
      <div class="range-text">{{ normalRange.min }}-{{ normalRange.max }} {{ unit }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, default: '📊' },
  name: { type: String, default: '传感器' },
  value: { type: [Number, String], default: 0 },
  unit: { type: String, default: '' },
  normalRange: { type: Object, default: null },
  decimals: { type: Number, default: 1 },
})

const displayValue = computed(() => {
  const num = typeof props.value === 'string' ? parseFloat(props.value) : props.value
  return isNaN(num) ? '--' : num.toFixed(props.decimals)
})

const isWarning = computed(() => {
  if (!props.normalRange) return false
  const num = typeof props.value === 'string' ? parseFloat(props.value) : props.value
  if (isNaN(num)) return false
  return num < props.normalRange.min || num > props.normalRange.max
})

const isError = computed(() => {
  if (!props.normalRange) return false
  const num = typeof props.value === 'string' ? parseFloat(props.value) : props.value
  if (isNaN(num)) return false
  const min = props.normalRange.min
  const max = props.normalRange.max
  const range = max - min
  return num < min - range * 0.2 || num > max + range * 0.2
})

const rangeStyle = computed(() => {
  if (!props.normalRange) return {}
  const num = typeof props.value === 'string' ? parseFloat(props.value) : props.value
  if (isNaN(num)) return {}
  
  const min = props.normalRange.min
  const max = props.normalRange.max
  const range = max - min
  const lowerBound = min - range * 0.2
  const upperBound = max + range * 0.2
  
  const totalRange = upperBound - lowerBound
  const position = ((num - lowerBound) / totalRange) * 100
  
  return {
    left: `${Math.max(0, Math.min(100, position))}%`,
    backgroundColor: isError.value ? '#f56c6c' : isWarning.value ? '#e6a23c' : '#67c23a'
  }
})
</script>

<style scoped>
.sensor-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: all 0.3s ease;
  border-left: 4px solid #409eff;
}

.sensor-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.sensor-card.status-warning {
  border-left-color: #e6a23c;
}

.sensor-card.status-error {
  border-left-color: #f56c6c;
}

.sensor-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 10px;
}

.sensor-info {
  flex: 1;
}

.sensor-name {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.sensor-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.sensor-value .value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.sensor-value .unit {
  font-size: 14px;
  color: #909399;
}

.sensor-status {
  width: 80px;
}

.range-bar {
  height: 4px;
  background: #ebeef5;
  border-radius: 2px;
  position: relative;
  margin-bottom: 4px;
}

.range-fill {
  width: 6px;
  height: 100%;
  border-radius: 3px;
  position: absolute;
  transform: translateX(-50%);
  transition: all 0.3s ease;
}

.range-text {
  font-size: 10px;
  color: #c0c4cc;
  text-align: center;
}
</style>