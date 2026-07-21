<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '-' },
  hint: { type: String, default: '' },
  tone: { type: String, default: 'neutral' }, // neutral | up | down | warn
})
</script>

<template>
  <div class="card" :class="['tone-' + tone]">
    <div class="label">{{ label }}</div>
    <div class="value">{{ value }}</div>
    <div class="hint" v-if="hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
.card {
  background: #161a22;
  border: 1px solid #232834;
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: transform 0.15s ease, border-color 0.15s ease;
}
.card:hover {
  transform: translateY(-2px);
  border-color: #344055;
}
.label {
  color: #8a8f99;
  font-size: 13px;
  letter-spacing: 0.5px;
}
.value {
  color: #e6e8eb;
  font-size: 26px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.hint {
  color: #6c7280;
  font-size: 12px;
}

.tone-up { border-color: rgba(38, 166, 154, 0.5); }
.tone-up .value { color: #26a69a; }
.tone-down { border-color: rgba(239, 83, 80, 0.5); }
.tone-down .value { color: #ef5350; }
.tone-warn { border-color: rgba(251, 192, 45, 0.55); }
.tone-warn .value { color: #fbc02d; }
</style>
