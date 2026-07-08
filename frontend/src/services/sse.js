import { useAuthStore } from '../stores/auth.js'

class SSEManager {
  constructor() {
    this.connections = {}
    this.listeners = {}
    this.reconnectAttempts = {}
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
  }

  _getAuthToken() {
    const authStore = useAuthStore()
    return authStore.token
  }

  _getBaseUrl() {
    return import.meta.env.VITE_API_BASE_URL || '/api/v1'
  }

  connect(channel) {
    if (this.connections[channel]) {
      return this.connections[channel]
    }

    const token = this._getAuthToken()
    const baseUrl = this._getBaseUrl()
    const url = `${baseUrl}/sse/${channel}?token=${encodeURIComponent(token)}`

    try {
      const eventSource = new EventSource(url)

      eventSource.onopen = () => {
        console.log(`[SSE] Connected to ${channel}`)
        this.reconnectAttempts[channel] = 0
        this._emit(channel, 'connected')
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this._emit(channel, 'message', data)
        } catch (e) {
          console.error(`[SSE] Failed to parse message from ${channel}:`, e)
        }
      }

      eventSource.addEventListener('new_alert', (event) => {
        try {
          const data = JSON.parse(event.data)
          this._emit(channel, 'new_alert', data)
        } catch (e) {
          console.error('[SSE] Failed to parse new_alert:', e)
        }
      })

      eventSource.addEventListener('device_status', (event) => {
        try {
          const data = JSON.parse(event.data)
          this._emit(channel, 'device_status', data)
        } catch (e) {
          console.error('[SSE] Failed to parse device_status:', e)
        }
      })

      eventSource.addEventListener('command_response', (event) => {
        try {
          const data = JSON.parse(event.data)
          this._emit(channel, 'command_response', data)
        } catch (e) {
          console.error('[SSE] Failed to parse command_response:', e)
        }
      })

      eventSource.onerror = (error) => {
        console.error(`[SSE] Error on ${channel}:`, error)
        this._emit(channel, 'error', error)

        if (eventSource.readyState === EventSource.CLOSED) {
          this._tryReconnect(channel)
        }
      }

      this.connections[channel] = eventSource
      this.reconnectAttempts[channel] = 0
      return eventSource
    } catch (error) {
      console.error(`[SSE] Failed to connect to ${channel}:`, error)
      return null
    }
  }

  _tryReconnect(channel) {
    if (this.reconnectAttempts[channel] >= this.maxReconnectAttempts) {
      console.error(`[SSE] Max reconnect attempts reached for ${channel}`)
      this._emit(channel, 'max_reconnect_reached')
      return
    }

    this.reconnectAttempts[channel] = (this.reconnectAttempts[channel] || 0) + 1
    console.log(`[SSE] Reconnecting ${channel} (attempt ${this.reconnectAttempts[channel]})...`)

    setTimeout(() => {
      this.connections[channel] = null
      this.connect(channel)
    }, this.reconnectDelay * this.reconnectAttempts[channel])
  }

  disconnect(channel) {
    if (this.connections[channel]) {
      this.connections[channel].close()
      this.connections[channel] = null
      delete this.connections[channel]
      console.log(`[SSE] Disconnected from ${channel}`)
    }
    this.listeners[channel] = {}
  }

  disconnectAll() {
    Object.keys(this.connections).forEach(channel => {
      this.disconnect(channel)
    })
  }

  on(channel, event, callback) {
    if (!this.listeners[channel]) {
      this.listeners[channel] = {}
    }
    if (!this.listeners[channel][event]) {
      this.listeners[channel][event] = []
    }
    this.listeners[channel][event].push(callback)

    if (!this.connections[channel]) {
      this.connect(channel)
    }
  }

  off(channel, event, callback) {
    if (this.listeners[channel] && this.listeners[channel][event]) {
      this.listeners[channel][event] = this.listeners[channel][event].filter(
        cb => cb !== callback
      )
    }
  }

  _emit(channel, event, data) {
    if (this.listeners[channel] && this.listeners[channel][event]) {
      this.listeners[channel][event].forEach(callback => {
        try {
          callback(data)
        } catch (e) {
          console.error(`[SSE] Listener error for ${channel}/${event}:`, e)
        }
      })
    }
  }
}

export const sseManager = new SSEManager()
export default sseManager
