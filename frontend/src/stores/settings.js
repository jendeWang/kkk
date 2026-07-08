import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const uiMode = ref(localStorage.getItem('ui_mode') || 'simple')

  function setUiMode(mode) {
    uiMode.value = mode
    localStorage.setItem('ui_mode', mode)
  }

  function toggleUiMode() {
    setUiMode(uiMode.value === 'simple' ? 'advanced' : 'simple')
  }

  return {
    uiMode,
    setUiMode,
    toggleUiMode
  }
})
