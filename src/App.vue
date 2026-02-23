<template>
  <div id="app">
    <StatusBoard />
  </div>
</template>

<script setup>
import StatusBoard from './components/StatusBoard.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: #0a0e1a;
  color: #fff;
}

#app {
  min-height: 100vh;
}
</style>
