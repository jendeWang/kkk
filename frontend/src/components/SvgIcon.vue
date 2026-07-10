<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    :style="iconStyle"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    fill="none"
    stroke="currentColor"
    class="svg-icon"
    v-html="iconPath"
  />
</template>

<script setup>
import { computed } from 'vue'
import { icons, getIconName } from '../utils/icons.js'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 24 },
  color: { type: String, default: 'currentColor' },
})

const iconPath = computed(() => {
  const iconName = icons[props.name] ? props.name : getIconName(props.name)
  return icons[iconName] || icons['default']
})

const iconStyle = computed(() => ({
  color: props.color,
  width: typeof props.size === 'number' ? `${props.size}px` : props.size,
  height: typeof props.size === 'number' ? `${props.size}px` : props.size,
}))
</script>

<style scoped>
.svg-icon {
  display: inline-block;
  vertical-align: middle;
}
</style>