<template>
  <div class="app">
    <header class="header">
      <h1>🤖 提示词优化工具</h1>
      <p>LLM Prompt Optimizer - 智能提示词优化平台</p>
    </header>
    <main class="main">
      <Home />
    </main>
    <Toast />
  </div>
</template>

<script setup>
import Home from './views/Home.vue'
import Toast from './components/Toast.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.app {
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  text-align: center;
  color: white;
  padding: 30px;
}

.header h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.header p {
  opacity: 0.9;
  font-size: 14px;
}

.main {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden;
}
</style>