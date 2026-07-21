<script setup>
import { onMounted } from 'vue'
import Dashboard from './views/Dashboard.vue'
import { usePriceStore } from './stores/price'

const store = usePriceStore()
onMounted(() => {
  store.fetchAll()
})
</script>

<template>
  <Dashboard />
</template>

<style scoped>
</style>
