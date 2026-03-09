<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { runSentimentGuard, getSentimentGuardSession } from "@/api/sentiment_guard";
import FileUploadField from "@/components/FileUploadField.vue";

const route = useRoute();

const form = ref({
  mode: "proactive",
  event_description: "某博主发布视频称我品牌产品含有违禁成分，内容在小红书迅速扩散",
  current_sentiment: "",
});

const sessionId = ref<number | null>(null);
const loading = ref(false);
const error = ref("");
const readonly = ref(false);

// 各步骤状态
const steps = ref<Record<string, { status: "pending" | "running" | "done"; data?: any }>>({
  risk_assess: { status: "pending" },
  spread: { status: "pending" },
  response_gen: { status: "pending" },
  validate: { status: "pending" },
});
const finalReport = ref<any>(null);

const stepLabels: Record<string, string> = {
  risk_assess: "风险评估",
  spread: "传播模拟",
  response_gen: "方案生成",
  validate: "方案验证",
};

let wsInstance: WebSocket | null = null;

const setupWS = (sid: number) => {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const base = (import.meta.env.VITE_WS_BASE_URL as string) ?? `${proto}://${location.hostname}:8000`;
  const ws = new WebSocket(`${base}/api/ws/sentiment-guard/${sid}`);
  ws.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    if (data.type === "progress") {
      if (steps.value[data.step]) steps.value[data.step].status = "running";
    } else if (data.type === "step_done") {
      if (steps.value[data.step]) {
        steps.value[data.step].status = "done";
        steps.value[data.step].data = data.data;
      }
    } else if (data.type === "done") {
      finalReport.value = data.data;
      loading.value = false;
      ws.close();
    } else if (data.type === "error") {
      error.value = data.message ?? "评估失败";
      loading.value = false;
      ws.close();
    }
  };
  ws.onerror = () => {
    error.value = "WebSocket 连接失败";
    loading.value = false;
  };
  return ws;
};

const submit = async () => {
  loading.value = true;
  error.value = "";
  finalReport.value = null;
  for (const key of Object.keys(steps.value)) {
    steps.value[key] = { status: "pending" };
  }
  wsInstance?.close();

  try {
    const resp = await runSentimentGuard(form.value);
    sessionId.value = resp.data.session_id;
    wsInstance = setupWS(resp.data.session_id);
  } catch (e: any) {
    error.value = e.message ?? "提交失败";
    loading.value = false;
  }
};

const bestValidation = (report: any) => {
  const vs: any[] = report.validation_results ?? [];
  return vs.find((v) => v.label === report.best_plan) ?? vs[0] ?? null;
};

onMounted(async () => {
  const historyId = Number(route.query.session_id);
  if (historyId) {
    readonly.value = true;
    sessionId.value = historyId;
    try {
      const resp = await getSentimentGuardSession(historyId);
      const d = resp.data;
      if (d) {
        form.value.mode = d.mode ?? "proactive";
        form.value.event_description = d.event_description ?? "";
        if (d.payload) {
          finalReport.value = d.payload;
          for (const key of Object.keys(steps.value)) {
            steps.value[key] = { status: "done", data: d.payload[key] };
          }
        }
      }
    } catch { /* ignore */ }
  }
});
</script>

<template>
  <section class="card">
    <h2>舆情哨兵</h2>
    <p class="tip">
      输入一个潜在或已发生的负面事件，AI 评估传播风险、模拟扩散路径、生成并验证3套应对方案，输出最优方案与执行时间窗口。
    </p>
    <div class="form-grid">
      <label>
        评估模式
        <select v-model="form.mode">
          <option value="proactive">事前预判（潜在风险）</option>
          <option value="reactive">事后应对（已发生负面）</option>
        </select>
      </label>
      <FileUploadField
        v-model="form.event_description"
        label="风险事件资料"
        placeholder="上传舆情报告 / 投诉记录 / 风险描述文件"
      />
      <FileUploadField
        v-if="form.mode === 'reactive'"
        v-model="form.current_sentiment"
        label="当前舆情数据（可选）"
        placeholder="上传舆情监测数据 / 传播范围报告"
      />
      <button :disabled="loading || !form.event_description || readonly" @click="submit">
        {{ loading ? "评估中..." : "开始评估" }}
      </button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <section v-if="sessionId" class="card">
    <h3>评估进度</h3>
    <div class="step-list">
      <div v-for="(val, key) in steps" :key="key" class="step-item" :class="val.status">
        <div class="step-icon">
          <span v-if="val.status === 'done'">✓</span>
          <span v-else-if="val.status === 'running'" class="spin">⟳</span>
          <span v-else>○</span>
        </div>
        <div class="step-info">
          <span class="step-name">{{ stepLabels[key] }}</span>
          <span v-if="val.status === 'running'" class="step-hint">进行中...</span>
          <span v-else-if="val.status === 'done'" class="step-hint done-hint">完成</span>
        </div>
      </div>
    </div>

    <!-- 风险评估结果 -->
    <div v-if="steps.risk_assess.data" class="result-block">
      <h4>风险评估</h4>
      <div class="risk-bar">
        <span>严重程度</span>
        <div class="bar-bg">
          <div class="bar-fill" :style="{ width: `${steps.risk_assess.data.severity * 10}%`, background: steps.risk_assess.data.severity >= 7 ? '#d64545' : steps.risk_assess.data.severity >= 4 ? '#f0a500' : '#27ab83' }" />
        </div>
        <span class="bar-val">{{ steps.risk_assess.data.severity }}/10</span>
      </div>
      <div class="tag-row">
        <strong>引爆话题：</strong>
        <span v-for="t in steps.risk_assess.data.trigger_topics" :key="t" class="tag">{{ t }}</span>
      </div>
      <div class="tag-row">
        <strong>易感人群：</strong>
        <span v-for="a in steps.risk_assess.data.vulnerable_audiences" :key="a" class="tag tag-warn">{{ a }}</span>
      </div>
      <p class="meta">预计传播速度：{{ steps.risk_assess.data.estimated_spread_speed }}</p>
    </div>

    <!-- 传播模拟 -->
    <div v-if="steps.spread.data" class="result-block">
      <h4>传播模拟</h4>
      <div class="spread-grid">
        <div class="spread-item"><span class="spread-label">峰值时间</span><span class="spread-val">{{ steps.spread.data.peak_hours }}h</span></div>
        <div class="spread-item"><span class="spread-label">触达率</span><span class="spread-val">{{ steps.spread.data.estimated_reach_rate }}</span></div>
        <div class="spread-item"><span class="spread-label">负向情绪占比</span><span class="spread-val warn">{{ steps.spread.data.negative_sentiment_ratio }}</span></div>
      </div>
      <p class="meta">{{ steps.spread.data.inflection_point }}</p>
    </div>

    <!-- 3套方案 -->
    <div v-if="steps.response_gen.data" class="result-block">
      <h4>应对方案</h4>
      <div class="plans-grid">
        <div v-for="plan in steps.response_gen.data" :key="plan.label" class="plan-card">
          <div class="plan-label">{{ plan.label }}</div>
          <div class="plan-strategy">{{ plan.strategy }}</div>
          <p class="plan-msg">{{ plan.key_message }}</p>
          <div class="plan-timing">时机：{{ plan.timing }}</div>
        </div>
      </div>
    </div>

    <!-- 验证结果 -->
    <div v-if="steps.validate.data" class="result-block">
      <h4>方案验证对比</h4>
      <div class="plans-grid">
        <div v-for="v in steps.validate.data" :key="v.label" class="plan-card" :class="{ best: finalReport?.best_plan === v.label }">
          <div class="plan-label">{{ v.label }} {{ finalReport?.best_plan === v.label ? '⭐ 推荐' : '' }}</div>
          <div class="val-row"><span>效果评分</span><strong>{{ v.score }}/10</strong></div>
          <div class="val-row"><span>预计平息时间</span><strong>{{ v.recovery_time }}</strong></div>
          <div class="val-row"><span>执行窗口</span><strong>{{ v.execution_window }}</strong></div>
          <div class="val-row"><span>综合评价</span><strong>{{ v.effectiveness }}</strong></div>
        </div>
      </div>
    </div>
  </section>

  <section v-if="finalReport" class="card result-summary">
    <h3>最终评估报告</h3>
    <p class="summary-text">{{ finalReport.summary }}</p>
    <div class="best-plan-box" v-if="bestValidation(finalReport)">
      <div class="best-title">推荐方案：{{ finalReport.best_plan }}</div>
      <div class="best-detail">执行窗口：{{ bestValidation(finalReport).execution_window }}</div>
    </div>
  </section>
</template>

<style scoped>
.card { border: 1px solid #d9e2ec; border-radius: 12px; background: #fff; padding: 20px 24px; margin-bottom: 16px; }
.tip { color: #486581; font-size: 14px; margin: 0 0 16px; line-height: 1.7; }
.form-grid { display: grid; gap: 12px; }
label { display: grid; gap: 6px; font-size: 14px; }
input, select, textarea { border: 1px solid #bcccdc; border-radius: 8px; padding: 8px 10px; font-size: 14px; }
button { width: fit-content; border: 0; border-radius: 8px; padding: 9px 18px; color: #fff; background: #334e68; cursor: pointer; font-size: 14px; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.error { color: #d64545; font-size: 14px; margin-top: 8px; }

.step-list { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
.step-item { display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 8px; border: 1px solid #d9e2ec; background: #f8fbff; }
.step-item.running { border-color: #f0a500; background: #fffbf0; }
.step-item.done { border-color: #27ab83; background: #f0faf5; }
.step-icon { font-size: 16px; color: #829ab1; }
.step-item.running .step-icon { color: #f0a500; }
.step-item.done .step-icon { color: #27ab83; }
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.step-name { font-size: 13px; font-weight: 600; }
.step-hint { font-size: 12px; color: #829ab1; }
.done-hint { color: #27ab83; }

.result-block { border-top: 1px solid #e4ecf5; padding-top: 16px; margin-top: 16px; }
.result-block h4 { margin: 0 0 12px; font-size: 14px; color: #334e68; }
.risk-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; font-size: 14px; }
.bar-bg { flex: 1; height: 8px; background: #d9e2ec; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
.bar-val { font-weight: 700; font-size: 14px; min-width: 40px; }
.tag-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-bottom: 8px; font-size: 13px; }
.tag { background: #e8f0fe; color: #334e68; border-radius: 12px; padding: 2px 10px; font-size: 12px; }
.tag-warn { background: #fff3cd; color: #856404; }
.meta { font-size: 13px; color: #627d98; margin: 4px 0 0; }

.spread-grid { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }
.spread-item { background: #f0f4f8; border-radius: 8px; padding: 10px 16px; text-align: center; }
.spread-label { display: block; font-size: 12px; color: #829ab1; margin-bottom: 4px; }
.spread-val { font-size: 18px; font-weight: 700; color: #334e68; }
.spread-val.warn { color: #d64545; }

.plans-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.plan-card { border: 1px solid #d9e2ec; border-radius: 10px; padding: 14px; background: #f8fbff; }
.plan-card.best { border-color: #334e68; background: #eef2ff; }
.plan-label { font-weight: 700; font-size: 14px; color: #334e68; margin-bottom: 6px; }
.plan-strategy { font-size: 13px; color: #486581; margin-bottom: 6px; font-weight: 600; }
.plan-msg { font-size: 13px; color: #627d98; margin: 0 0 6px; line-height: 1.5; }
.plan-timing { font-size: 12px; color: #829ab1; }
.val-row { display: flex; justify-content: space-between; font-size: 13px; color: #486581; padding: 3px 0; border-bottom: 1px solid #f0f4f8; }
.val-row:last-child { border: none; }

.result-summary { background: #f0faf5; border-color: #27ab83; }
.summary-text { font-size: 15px; color: #102a43; line-height: 1.7; margin: 0 0 16px; }
.best-plan-box { background: #334e68; color: #fff; border-radius: 10px; padding: 14px 18px; }
.best-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.best-detail { font-size: 14px; opacity: 0.85; }
</style>
