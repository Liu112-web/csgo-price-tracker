<script setup>
defineProps({
  alerts: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="alerts">
    <h3>提醒记录</h3>
    <div v-if="!alerts.length" class="empty">暂无提醒记录</div>
    <ul v-else>
      <li v-for="(a, i) in alerts" :key="i">
        <span class="time">{{ a.triggered_at }}</span>
        <span class="price">¥{{ Number(a.price).toFixed(2) }}</span>
        <span class="target">目标 ¥{{ Number(a.target_price).toFixed(2) }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.alerts {
  background: #161a22;
  border: 1px solid #232834;
  border-radius: 12px;
  padding: 16px 20px;
}
h3 {
  font-size: 15px;
  color: #cfd3dc;
  margin-bottom: 12px;
  font-weight: 600;
}
.empty {
  color: #6c7280;
  font-size: 13px;
  padding: 24px 0;
  text-align: center;
}
ul {
  list-style: none;
  max-height: 240px;
  overflow-y: auto;
}
li {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px dashed #232834;
  font-size: 13px;
  color: #cfd3dc;
}
li:last-child {
  border-bottom: none;
}
.time {
  color: #8a8f99;
  font-variant-numeric: tabular-nums;
}
.price {
  color: #fbc02d;
  font-weight: 600;
  text-align: right;
}
.target {
  color: #8a8f99;
  text-align: right;
}
</style>
