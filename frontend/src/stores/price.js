import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api'

export const usePriceStore = defineStore('price', () => {
  const config = ref(null)
  const latest = ref(null)
  const daily = ref([])
  const history = ref([])
  const alerts = ref([])
  const loading = ref(false)
  const error = ref('')
  const lastCheckAt = ref(null)

  const isAboveTarget = computed(() => {
    if (!latest.value || !config.value) return false
    const price = latest.value.price
    const target = config.value.target_price
    return price !== null && target !== null && price > target
  })

  const profit = computed(() => {
    if (!latest.value || !config.value) return null
    const price = latest.value.price
    const purchase = config.value.purchase_price
    if (price === null || price === undefined) return null
    return Number((price - purchase).toFixed(2))
  })

  const profitRate = computed(() => {
    if (!latest.value || !config.value) return null
    const price = latest.value.price
    const purchase = config.value.purchase_price
    if (!price || !purchase) return null
    return Number((((price - purchase) / purchase) * 100).toFixed(2))
  })

  async function fetchAll() {
    loading.value = true
    error.value = ''
    try {
      const [cfg, lat, dai, his, alt] = await Promise.all([
        api.getConfig(),
        api.getLatest(),
        api.getDaily(),
        api.getHistory(),
        api.getAlerts(),
      ])
      config.value = cfg
      latest.value = lat.latest
      daily.value = dai.points || []
      history.value = his.points || []
      alerts.value = alt.alerts || []
    } catch (e) {
      error.value = e?.message || '加载失败'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function triggerCheck() {
    loading.value = true
    try {
      await api.triggerCheck()
      await fetchAll()
      lastCheckAt.value = new Date()
    } catch (e) {
      error.value = e?.message || '检查失败'
    } finally {
      loading.value = false
    }
  }

  async function saveConfig(newCfg) {
    await api.updateConfig(newCfg)
    await fetchAll()
  }

  return {
    config, latest, daily, history, alerts,
    loading, error, lastCheckAt,
    isAboveTarget, profit, profitRate,
    fetchAll, triggerCheck, saveConfig,
  }
})
