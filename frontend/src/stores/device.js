import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api.js'

export const useDeviceStore = defineStore('device', () => {
  const devices = ref([])
  const currentDevice = ref(null)
  const commands = ref([])
  const alertRules = ref([])
  const alertEvents = ref([])

  async function fetchDevices(params = {}) {
    const response = await api.get('/devices/', { params })
    devices.value = response.data
    return response.data
  }

  async function fetchDevice(deviceId) {
    const response = await api.get(`/devices/${deviceId}`)
    currentDevice.value = response.data
    return response.data
  }

  async function createDevice(data) {
    const response = await api.post('/devices/', data)
    devices.value.push(response.data)
    return response.data
  }

  async function updateDevice(deviceId, data) {
    const response = await api.put(`/devices/${deviceId}`, data)
    const index = devices.value.findIndex(d => d.id === deviceId)
    if (index !== -1) devices.value[index] = response.data
    return response.data
  }

  async function deleteDevice(deviceId) {
    await api.delete(`/devices/${deviceId}`)
    devices.value = devices.value.filter(d => d.id !== deviceId)
  }

  async function regenerateSecret(deviceId) {
    const response = await api.post(`/devices/${deviceId}/regenerate-secret`)
    const index = devices.value.findIndex(d => d.id === deviceId)
    if (index !== -1) devices.value[index] = response.data
    return response.data
  }

  async function fetchTelemetry(params = {}) {
    const response = await api.get('/telemetry/', { params })
    return response.data
  }

  async function fetchCommands(params = {}) {
    const response = await api.get('/commands/', { params })
    commands.value = response.data
    return response.data
  }

  async function createCommand(data) {
    const response = await api.post('/commands/', data)
    commands.value.unshift(response.data)
    return response.data
  }

  async function fetchAlertRules() {
    const response = await api.get('/alerts/rules')
    alertRules.value = Array.isArray(response.data) ? response.data : []
    return alertRules.value
  }

  async function createAlertRule(data) {
    const response = await api.post('/alerts/rules', data)
    alertRules.value.push(response.data)
    return response.data
  }

  async function updateAlertRule(ruleId, data) {
    const response = await api.put(`/alerts/rules/${ruleId}`, data)
    const index = alertRules.value.findIndex(r => r.id === ruleId)
    if (index !== -1) alertRules.value[index] = response.data
    return response.data
  }

  async function deleteAlertRule(ruleId) {
    await api.delete(`/alerts/rules/${ruleId}`)
    alertRules.value = alertRules.value.filter(r => r.id !== ruleId)
  }

  async function fetchAlertEvents(params = {}) {
    const response = await api.get('/alerts/events', { params })
    alertEvents.value = response.data
    return response.data
  }

  async function updateAlertEventStatus(eventId, status) {
    const response = await api.put(`/alerts/events/${eventId}/status`, { status })
    const index = alertEvents.value.findIndex(e => e.id === eventId)
    if (index !== -1) alertEvents.value[index] = response.data
    return response.data
  }

  return {
    devices, currentDevice, commands, alertRules, alertEvents,
    fetchDevices, fetchDevice, createDevice, updateDevice, deleteDevice, regenerateSecret,
    fetchTelemetry, fetchCommands, createCommand,
    fetchAlertRules, createAlertRule, updateAlertRule, deleteAlertRule,
    fetchAlertEvents, updateAlertEventStatus
  }
})
