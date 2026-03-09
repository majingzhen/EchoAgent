<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getSimulationReport, getSimulationStatus } from "@/api/simulation";

const route = useRoute();
const router = useRouter();
const ids = ref<number[]>([]);
const data = ref<[any, any]>([null, null]);
const reports = ref<[any, any]>([null, null]);
const loading = ref(false);

onMounted(async () => {
  const raw = (route.query.ids as string) ?? "";
  ids.value = raw.split(",").map(Number).filter(Boolean);
  if (ids.value.length < 2) return;
  loading.value = true;
  try {
    const [s1, s2] = await Promise.all(ids.value.slice(0, 2).map(id => getSimulationStatus(id)));
    data.value = [s1.data, s2.data];
    const [r1, r2] = await Promise.all(ids.value.slice(0, 2).map(id => getSimulationReport(id).catch(() => ({ data: null }))));
    reports.value = [r1.data, r2.data];
  } catch { /* ignore */ }
  loading.value = false;
});

const goBack = () => router.push("/simulation/history");

const lastMetric = (idx: number, key: string) => {
  const d = data.value[idx];
  if (!d?.metrics_timeline?.length) return "-";
  return d.metrics_timeline[d.metrics_timeline.length - 1]?.[key] ?? "-";
};
</script>

<template>
  <section class="card">
    <div class="header-row">
      <h2>沙盘推演 - 对比</h2>
      <button @click="goBack">返回列表</button>
    </div>

    <p v-if="loading" class="tip">加载中...</p>
    <p v-else-if="ids.length < 2" class="tip">请从历史列表勾选 2 条记录进行对比</p>

    <div v-else class="compare-grid">
      <div v-for="(d, idx) in data" :key="idx" class="compare-col">
        <h3>会话 #{{ ids[idx] }}</h3>
        <div v-if="d" class="info-block">
          <p><b>平台：</b>{{ d.platform }} | <b>轮次：</b>{{ d.current_round }}/{{ d.total_rounds }}</p>
          <table class="metric-table">
            <tr><th>指标</th><th>最终值</th></tr>
            <tr><td>互动率</td><td>{{ lastMetric(idx, "engagement_rate") }}</td></tr>
            <tr><td>平均情感</td><td>{{ lastMetric(idx, "avg_sentiment") }}</td></tr>
            <tr><td>购买意愿</td><td>{{ lastMetric(idx, "avg_purchase_intent") }}</td></tr>
          </table>
        </div>
        <div v-if="reports[idx]" class="report-block">
          <h4>报告摘要</h4>
          <p>{{ reports[idx].executive_summary }}</p>
          <h4>风险</h4>
          <ul><li v-for="(r, ri) in reports[idx].risks" :key="ri">{{ r }}</li></ul>
          <h4>建议</h4>
          <ul><li v-for="(s, si) in reports[idx].suggestions" :key="si">{{ s }}</li></ul>
        </div>
        <p v-else class="tip">报告未生成</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card { border: 1px solid #d9e2ec; border-radius: 12px; background: #fff; padding: 20px 24px; }
.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-row h2 { margin: 0; }
.tip { color: #486581; font-size: 14px; }
.compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.compare-col { border: 1px solid #d9e2ec; border-radius: 8px; padding: 14px; background: #f8fbff; }
.compare-col h3 { margin: 0 0 12px; font-size: 15px; color: #334e68; }
.info-block p { font-size: 14px; color: #334e68; margin: 0 0 10px; }
.metric-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 14px; }
.metric-table th { text-align: left; color: #829ab1; padding: 4px 8px; border-bottom: 1px solid #d9e2ec; }
.metric-table td { padding: 4px 8px; color: #334e68; border-bottom: 1px solid #f0f4f8; }
.report-block h4 { margin: 10px 0 6px; font-size: 14px; color: #334e68; }
.report-block p { font-size: 13px; color: #486581; line-height: 1.6; margin: 0 0 8px; }
.report-block ul { margin: 0; padding-left: 18px; }
.report-block li { font-size: 13px; color: #486581; line-height: 1.7; }
button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:hover { background: #243b53; }
</style>
