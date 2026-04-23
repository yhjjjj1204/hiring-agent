import { ref } from 'vue'

const socket = ref(null)
const listeners = new Set()
const status = ref('disconnected')
let reconnectTimeout = null

export function useWebSocket() {
  function connect() {
    if (socket.value) return

    const token = localStorage.getItem('token')
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws?token=${token}`

    socket.value = new WebSocket(wsUrl)
    status.value = 'connecting'

    socket.value.onopen = () => {
      console.log('WebSocket Connected')
      status.value = 'connected'
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
        reconnectTimeout = null
      }
    }

    socket.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      listeners.forEach(callback => callback(data))
    }

    socket.value.onclose = () => {
      console.log('WebSocket Disconnected')
      status.value = 'disconnected'
      socket.value = null
      
      // Attempt to reconnect after 3 seconds
      if (!reconnectTimeout) {
        reconnectTimeout = setTimeout(() => {
          reconnectTimeout = null
          connect()
        }, 3000)
      }
    }

    socket.value.onerror = (err) => {
      console.error('WebSocket Error:', err)
      socket.value.close()
    }
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
  }

  function subscribe(callback) {
    listeners.add(callback)
    return () => listeners.delete(callback)
  }

  function send(data) {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not open. Message not sent:', data)
    }
  }

  return {
    status,
    connect,
    disconnect,
    subscribe,
    send
  }
}
