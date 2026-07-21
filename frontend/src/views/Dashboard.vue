<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { usePriceStore } from '../stores/price'
import PriceChart from '../components/PriceChart.vue'
import StatCard from '../components/StatCard.vue'
import AlertList from '../components/AlertList.vue'

const store = usePriceStore()
const {
  config, latest, daily, history, alerts,
  loading, error, lastCheckAt,
  isAboveTarget, profit, profitRate,
} = storeToRefs(store)

const now = ref(new Date())
let timer = null
onMounted(() => {
  timer = setInterval(() => (now.value = new Date()), 1000)
})

const priceText = computed(() => {
  const p = latest.value?.price
  return p == null ? '-' : `¥${Number(p).toFixed(2)}`
})
const targetText = computed(() =>
  config.value ? `¥${Number(config.value.target_price).toFixed(2)}` : '-'
)
const purchaseText = computed(() =>
  config.value ? `¥${Number(config.value.purchase_price).toFixed(2)}` : '-'
)
const profitText = computed(() => {
  if (profit.value === null) return '-'
  const sign = profit.value > 0 ? '+' : ''
  return `${sign}¥${profit.value.toFixed(2)}`
})
const profitRateText = computed(() => {
  if (profitRate.value === null) return '-'
  const sign = profitRate.value > 0 ? '+' : ''
  return `${sign}${profitRate.value.toFixed(2)}%`
})
const profitTone = computed(() => {
  if (profit.value === null) return 'neutral'
  if (profit.value > 0) return 'up'
  if (profit.value < 0) return 'down'
  return 'neutral'
})
const priceTone = computed(() => isAboveTarget.value ? 'warn' : 'neutral')

const updatedAt = computed(() => {
  const t = latest.value?.created_at
  if (!t) return '-'
  return t.replace('T', ' ')
})

const dataCount = computed(() => daily.value?.length || 0)
const min30 = computed(() => {
  if (!history.value?.length) return null
  const prices = history.value.map(p => p.price)
  return Math.min(...prices).toFixed(2)
})
const max30 = computed(() => {
  if (!history.value?.length) return null
  const prices = history.value.map(p => p.price)
  return Math.max(...prices).toFixed(2)
})

async function refresh() {
  await store.fetchAll()
}
async function triggerCheck() {
  await store.triggerCheck()
}
function formatTime(d) {
  return d.toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <div class="page">
    <header class="hero">
      <div class="hero-left">
        <div class="badge">CSGO · BUFF 价格监控</div>
        <h1>{{ config?.item_name || '弯刀 传说 久经沙场' }}</h1>
        <div class="sub">
          每日自动抓取 BUFF 在售最低价 · 价格超 ¥{{ config?.target_price || 690 }} 时桌面弹窗提醒
        </div>
      </div>
      <div class="hero-right">
        <div class="clock">{{ formatTime(now) }}</div>
        <div class="actions">
          <button class="btn primary" :disabled="loading" @click="triggerCheck">
            {{ loading ? '抓取中...' : '立即抓取一次' }}
          </button>
          <button class="btn ghost" :disabled="loading" @click="refresh">
            刷新数据
          </button>
        </div>
      </div>
    </header>

    <div v-if="error" class="error-bar">⚠️ {{ error }}</div>

    <section class="cards">
      <StatCard
        label="当前最低在售价"
        :value="priceText"
        :hint="`更新于 ${updatedAt}`"
        :tone="priceTone"
      />
      <StatCard
        label="盈亏金额"
        :value="profitText"
        :hint="`相对购入价 ¥${config?.purchase_price || 0}`"
        :tone="profitTone"
      />
      <StatCard
        label="盈亏比例"
        :value="profitRateText"
        :hint="isAboveTarget ? '已超过目标价！' : '未超目标价'"
        :tone="isAboveTarget ? 'warn' : profitTone"
      />
      <StatCard
        label="已累计记录"
        :value="`${dataCount} 天`"
        :hint="history.length ? `近30天 最低 ¥${min30} / 最高 ¥${max30}` : '等待历史数据'"
      />
    </section>

    <section class="chart-card">
      <div class="chart-head">
        <div>
          <h2>价格曲线</h2>
          <p class="muted">
            橙色实线 = 每日抓取的在售最低价；蓝色虚线 = BUFF 30 天均价参考线。
          </p>
        </div>
        <div class="legend-row">
          <span class="lg-dot target"></span>目标价
          <span class="lg-dot purchase"></span>购入价
        </div>
      </div>
      <PriceChart
        :daily="daily"
        :history="history"
        :target="config?.target_price || 0"
        :purchase="config?.purchase_price || 0"
      />
    </section>

    <section class="grid-two">
      <div class="settings">
        <h3>监控设置</h3>
        <div class="kv">
          <span>监控物品 ID</span>
          <b>{{ config?.goods_id }}</b>
        </div>
        <div class="kv">
          <span>购入价</span>
          <b>{{ purchaseText }}</b>
        </div>
        <div class="kv">
          <span>目标提醒价</span>
          <b class="warn">{{ targetText }}</b>
        </div>
        <div class="kv">
          <span>每日抓取时间</span>
          <b>{{ config?.check_time }}</b>
        </div>
        <div class="kv">
          <span>数据接口</span>
          <b>http://{{ config?.api_host }}:{{ config?.api_port }}/docs</b>
        </div>
      </div>
      <AlertList :alerts="alerts" />
    </section>

    <footer class="foot">
      <span>last check: {{ lastCheckAt ? formatTime(lastCheckAt) : '尚未手动触发' }}</span>
      <span>·</span>
      <span>数据源：网易 BUFF 公开 API</span>
    </footer>
  </div>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 28px 60px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding-bottom: 18px;
  border-bottom: 1px solid #1c2029;
  margin-bottom: 22px;
  flex-wrap: wrap;
}
.badge {
  display: inline-block;
  font-size: 12px;
  letter-spacing: 1px;
  color: #ff7043;
  background: rgba(255, 112, 67, 0.1);
  border: 1px solid rgba(255, 112, 67, 0.3);
  border-radius: 999px;
  padding: 4px 10px;
  margin-bottom: 10px;
}
.hero h1 {
  font-size: 22px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 6px;
}
.sub {
  color: #8a8f99;
  font-size: 13px;
}
.clock {
  font-size: 14px;
  color: #8a8f99;
  font-variant-numeric: tabular-nums;
  margin-bottom: 8px;
  text-align: right;
}
.actions {
  display: flex;
  gap: 8px;
}
.btn {
  border-radius: 8px;
  border: 1px solid #2a2f3a;
  background: #1c2029;
  color: #cfd3dc;
  padding: 8px 14px;
  font-size: 13px;
  transition: all 0.15s ease;
}
.btn:hover:not(:disabled) {
  border-color: #ff7043;
  color: #ff7043;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn.primary {
  background: linear-gradient(135deg, #ff7043 0%, #f4511e 100%);
  border-color: transparent;
  color: #fff;
}
.btn.primary:hover:not(:disabled) {
  color: #fff;
  filter: brightness(1.1);
}

.error-bar {
  background: rgba(239, 83, 80, 0.12);
  border: 1px solid rgba(239, 83, 80, 0.4);
  color: #ef9a9a;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}
@media (max-width: 900px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
}

.chart-card {
  background: #161a22;
  border: 1px solid #232834;
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 18px;
}
.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 12px;
}
.chart-head h2 {
  font-size: 16px;
  color: #e6e8eb;
  font-weight: 600;
}
.muted {
  color: #6c7280;
  font-size: 12px;
  margin-top: 4px;
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #8a8f99;
  font-size: 12px;
}
.lg-dot {
  display: inline-block;
  width: 16px;
  height: 2px;
  margin-right: 4px;
  vertical-align: middle;
}
.lg-dot.target { background: #fbc02d; }
.lg-dot.purchase { background: #26a69a; }

.grid-two {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 14px;
}
@media (max-width: 900px) {
  .grid-two { grid-template-columns: 1fr; }
}

.settings {
  background: #161a22;
  border: 1px solid #232834;
  border-radius: 12px;
  padding: 18px 20px;
}
.settings h3, .alerts h3 {
  font-size: 15px;
  color: #cfd3dc;
  margin-bottom: 12px;
  font-weight: 600;
}
.kv {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #232834;
  font-size: 13px;
  color: #8a8f99;
}
.kv:last-child { border-bottom: none; }
.kv b {
  color: #e6e8eb;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.kv b.warn { color: #fbc02d; }

.foot {
  margin-top: 24px;
  text-align: center;
  color: #4a4f5a;
  font-size: 12px;
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
