<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-container">
      <div 
        v-for="toast in toasts" 
        :key="toast.id" 
        :class="['toast', `toast-${toast.type}`]"
      >
        <span class="toast-icon">{{ getIcon(toast.type) }}</span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const toasts = ref([])
let toastId = 0

const showToast = (message, type = 'success') => {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3000)
}

const getIcon = (type) => {
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  }
  return icons[type] || icons.info
}

// 全局暴露 toast 方法
onMounted(() => {
  window.showToast = showToast
})

onUnmounted(() => {
  delete window.showToast
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  min-width: 200px;
  max-width: 400px;
}

.toast-success {
  border-left: 4px solid #28a745;
}

.toast-error {
  border-left: 4px solid #dc3545;
}

.toast-warning {
  border-left: 4px solid #ffc107;
}

.toast-info {
  border-left: 4px solid #17a2b8;
}

.toast-icon {
  font-size: 18px;
}

.toast-message {
  font-size: 14px;
  color: #333;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}
</style>