<template>
  <button 
    class="actuator-btn" 
    :class="{ active: isActive, disabled: isDisabled }"
    @click="handleClick"
  >
    <span class="actuator-icon">{{ icon }}</span>
    <span class="actuator-label">{{ label }}</span>
    <span class="actuator-status">{{ isActive ? '运行中' : '停止' }}</span>
  </button>
</template>

<script setup>
const props = defineProps({
  icon: { type: String, default: '⚙️' },
  label: { type: String, default: '执行器' },
  isActive: { type: Boolean, default: false },
  isDisabled: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle'])

const handleClick = () => {
  if (!props.isDisabled) {
    emit('toggle', !props.isActive)
  }
}
</script>

<style scoped>
.actuator-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #fff;
  border: 2px solid #ebeef5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
}

.actuator-btn:hover:not(.disabled) {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.actuator-btn.active {
  border-color: #67c23a;
  background: rgba(103, 194, 58, 0.05);
}

.actuator-btn.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.actuator-icon {
  font-size: 28px;
}

.actuator-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.actuator-status {
  font-size: 12px;
  color: #909399;
  padding: 2px 8px;
  background: #f5f7fa;
  border-radius: 10px;
}

.actuator-btn.active .actuator-status {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}
</style>