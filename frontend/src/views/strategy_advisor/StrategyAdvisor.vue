<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { runStrategyAdvisor, getStrategyAdvisorSession } from "@/api/strategy_advisor";
import FileUploadField from "@/components/FileUploadField.vue";

const route = useRoute();

const MODELS = [
  { key: "first_principles", name: "第一性原理", icon: "🔬", desc: "剥离表象，回到本质" },
  { key: "game_theory", name: "博弈论", icon: "♟", desc: "分析各方利益与策略互动" },
  { key: "systems_thinking", name: "系统思维", icon: "🔄", desc: "看整体结构和反馈回路" },
  { key: "inversion", name: "逆向思维", icon: "🔀", desc: "反过来想，怎样才能失败" },
  { key: "customer_lens", name: "用户视角", icon: "👁", desc: "站在客户角度思考" },
];

const form = ref({
  question: "我们要不要进入下沉市场？",
  context_info: "",
});

const sessionId = ref<number | null>(null);
const loading = ref(false);
const error = ref("");
const readonly = ref(false);

const modelResults = ref<Record<string, any>>({});
const debateResult = ref<any>(null);
const synthesis = ref<any>(null);

// 步骤状态
const phase = ref<"idle" | "phase1" | "phase2" | "phase3" | "done">("idle");

let wsInstance: WebSocket | null = null;

const setupWS = (sid: number) => {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const base = (import.meta.env.VITE_WS_BASE_URL as string) ?? `${proto}://${location.hostname}:8000`;
  const ws = new WebSocket(`${base}/api/ws/strategy-advisor/${sid}`);
  ws.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    if (data.type === "progress") {
      if (data.step === "phase1") phase.value = "phase1";
      else if (data.step === "phase2") phase.value = "phase2";
      else if (data.step === "phase3") phase.value = "phase3";
    } else if (data.type === "model_done") {
      modelResults.value[data.model_key] = data.data;
    } else if (data.type === "step_done" && data.step === "debate") {
      debateResult.value = data.data;
    } else if (data.type === "done") {
      synthesis.value = data.data;
      phase.value = "done";
      loading.value = false;
      ws.close();
    } else if (data.type === "error") {
      error.value = data.message ?? "分析失败";
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

onMounted(async () => {
  const historyId = Number(route.query.session_id);
  if (historyId) {
    readonly.value = true;
    sessionId.value = historyId;
    try {
      const resp = await getStrategyAdvisorSession(historyId);
      const d = resp.data;
      if (d) {
        form.value.question = d.question ?? "";
        form.value.context_info = d.context_info ?? "";
        if (d.payload) {
          const p = d.payload;
          if (p.model_analyses) {
            for (const [key, val] of Object.entries(p.model_analyses)) {
              modelResults.value[key] = val;
            }
          }
          if (p.debate) debateResult.value = p.debate;
          if (p.synthesis) synthesis.value = p.synthesis;
          phase.value = "done";
        }
      }
    } catch { /* ignore */ }
  }
});

const submit = async () => {
  loading.value = true;
  error.value = "";
  modelResults.value = {};
  debateResult.value = null;
  synthesis.value = null;
  phase.value = "idle";
  wsInstance?.close();

  try {
    const resp = await runStrategyAdvisor(form.value);
    sessionId.value = resp.data.session_id;
    wsInstance = setupWS(resp.data.session_id);
  } catch (e: any) {
    error.value = e.message ?? "提交失败";
    loading.value = false;
  }
};

const modelOf = (key: string) => MODELS.find((m) => m.key === key);
const modelStatus = (key: string) => {
  if (modelResults.value[key]) return "done";
  if (phase.value === "phase1") return "running";
  return "pending";
};
</script>

<template>
  <section class="card">
    <h2>策略参谋</h2>
    <p class="tip">
      输入一个业务决策问题，AI 同时调用5种思维模型（第一性原理、博弈论、系统思维、逆向思维、用户视角）独立分析，
      再进行交叉质疑辩论，最终综合输出共识、分歧、关键假设与决策框架。
    </p>
    <div class="form-grid">
      <label>
        决策问题
        <textarea v-model="form.question" rows="2" placeholder="如：我们要不要进入下沉市场？" />
      </label>
      <FileUploadField
        v-model="form.context_info"
        label="背景资料文件（可选）"
        placeholder="上传行业报告 / 竞品分析 / 内部数据文件"
      />
      <button :disabled="loading || !form.question || readonly" @click="submit">
        {{ loading ? "分析中..." : "开始多维分析" }}
      </button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <section v-if="sessionId" class="card">
    <div class="phase-header">
      <div class="phase-step" :class="{ active: phase === 'phase1', done: ['phase2','phase3','done'].includes(phase) }">
        Phase 1<br/><small>独立分析</small>
      </div>
      <div class="phase-arrow">→</div>
      <div class="phase-step" :class="{ active: phase === 'phase2', done: ['phase3','done'].includes(phase) }">
        Phase 2<br/><small>交叉质疑</small>
      </div>
      <div class="phase-arrow">→</div>
      <div class="phase-step" :class="{ active: phase === 'phase3', done: phase === 'done' }">
        Phase 3<br/><small>综合报告</small>
      </div>
    </div>

    <!-- Phase 1: 5个模型卡片实时出现 -->
    <div class="models-grid">
      <div
        v-for="m in MODELS"
        :key="m.key"
        class="model-card"
        :class="{ done: modelResults[m.key], running: modelStatus(m.key) === 'running' && !modelResults[m.key] }"
      >
        <div class="model-header">
          <span class="model-icon">{{ m.icon }}</span>
          <div>
            <div class="model-name">{{ m.name }}</div>
            <div class="model-desc">{{ m.desc }}</div>
          </div>
          <div class="model-status">
            <span v-if="modelResults[m.key]" class="status-done">✓</span>
            <span v-else-if="modelStatus(m.key) === 'running'" class="status-spin">⟳</span>
            <span v-else class="status-wait">○</span>
          </div>
        </div>
        <template v-if="modelResults[m.key]">
          <p class="model-conclusion">{{ modelResults[m.key].conclusion }}</p>
          <div v-if="modelResults[m.key].key_assumptions?.length" class="assumptions">
            <span class="assumption-label">关键假设：</span>
            <span v-for="a in modelResults[m.key].key_assumptions.slice(0,2)" :key="a" class="assumption-tag">{{ a }}</span>
          </div>
        </template>
        <p v-else-if="modelStatus(m.key) === 'running'" class="model-placeholder">思考中...</p>
        <p v-else class="model-placeholder">等待...</p>
      </div>
    </div>
  </section>

  <!-- Phase 2: 辩论结果 -->
  <section v-if="debateResult && !debateResult.skipped" class="card">
    <h3>交叉质疑辩论</h3>
    <p class="debate-dispute">核心分歧：{{ debateResult.core_disagreement }}</p>
    <div class="debate-grid">
      <div class="debate-side">
        <div class="debate-name">{{ debateResult.model_a }}</div>
        <p class="debate-arg">{{ debateResult.model_a_argument }}</p>
      </div>
      <div class="debate-vs">VS</div>
      <div class="debate-side">
        <div class="debate-name">{{ debateResult.model_b }}</div>
        <p class="debate-arg">{{ debateResult.model_b_argument }}</p>
      </div>
    </div>
    <div class="judge-box">
      <span class="judge-label">评审结论</span>
      <p class="judge-verdict">{{ debateResult.judge_verdict }}</p>
    </div>
  </section>

  <!-- Phase 3: 综合报告 -->
  <section v-if="synthesis" class="card synthesis-card">
    <h3>综合决策报告</h3>
    <div class="synthesis-grid">
      <div class="synthesis-block">
        <h4>共识观点</h4>
        <ul><li v-for="(item, i) in synthesis.consensus" :key="i">{{ item }}</li></ul>
      </div>
      <div class="synthesis-block">
        <h4>核心分歧</h4>
        <ul><li v-for="(item, i) in synthesis.divergences" :key="i">{{ item }}</li></ul>
      </div>
      <div class="synthesis-block">
        <h4>关键假设</h4>
        <ul><li v-for="(item, i) in synthesis.key_assumptions" :key="i">{{ item }}</li></ul>
      </div>
      <div class="synthesis-block">
        <h4>潜在盲区</h4>
        <ul><li v-for="(item, i) in synthesis.blind_spots" :key="i">{{ item }}</li></ul>
      </div>
    </div>
    <div class="recommendation-box">
      <h4>决策建议</h4>
      <p>{{ synthesis.recommendation }}</p>
    </div>
  </section>
</template>

<style scoped>
.card { border: 1px solid #d9e2ec; border-radius: 12px; background: #fff; padding: 20px 24px; margin-bottom: 16px; }
.tip { color: #486581; font-size: 14px; margin: 0 0 16px; line-height: 1.7; }
.form-grid { display: grid; gap: 12px; }
label { display: grid; gap: 6px; font-size: 14px; }
input, textarea { border: 1px solid #bcccdc; border-radius: 8px; padding: 8px 10px; font-size: 14px; }
button { width: fit-content; border: 0; border-radius: 8px; padding: 9px 18px; color: #fff; background: #334e68; cursor: pointer; font-size: 14px; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.error { color: #d64545; font-size: 14px; margin-top: 8px; }

.phase-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.phase-step { background: #f0f4f8; border: 1px solid #d9e2ec; border-radius: 10px; padding: 10px 16px; text-align: center; font-size: 13px; font-weight: 600; color: #829ab1; line-height: 1.5; }
.phase-step.active { background: #e8f0fe; border-color: #334e68; color: #334e68; }
.phase-step.done { background: #f0faf5; border-color: #27ab83; color: #27ab83; }
.phase-step small { font-weight: 400; opacity: 0.8; }
.phase-arrow { color: #9fb3c8; font-size: 18px; }

.models-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.model-card { border: 1px solid #d9e2ec; border-radius: 10px; padding: 14px; background: #f8fbff; transition: border-color 0.3s; }
.model-card.running { border-color: #f0a500; background: #fffbf0; }
.model-card.done { border-color: #27ab83; background: #f0faf5; animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0.4; transform: translateY(4px); } to { opacity: 1; transform: none; } }
.model-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
.model-icon { font-size: 22px; line-height: 1; }
.model-name { font-weight: 700; font-size: 14px; color: #102a43; }
.model-desc { font-size: 12px; color: #829ab1; }
.model-status { margin-left: auto; font-size: 16px; }
.status-done { color: #27ab83; }
.status-spin { color: #f0a500; display: inline-block; animation: spin 1s linear infinite; }
.status-wait { color: #d9e2ec; }
@keyframes spin { to { transform: rotate(360deg); } }
.model-conclusion { font-size: 13px; color: #243b53; line-height: 1.6; margin: 0 0 8px; }
.model-placeholder { font-size: 13px; color: #bcccdc; font-style: italic; margin: 0; }
.assumptions { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
.assumption-label { font-size: 12px; color: #829ab1; }
.assumption-tag { background: #e8f0fe; color: #334e68; border-radius: 10px; padding: 2px 8px; font-size: 11px; }

.debate-dispute { font-size: 14px; color: #486581; font-weight: 600; margin: 0 0 16px; }
.debate-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px; align-items: start; margin-bottom: 16px; }
.debate-side { background: #f8fbff; border: 1px solid #d9e2ec; border-radius: 10px; padding: 14px; }
.debate-name { font-weight: 700; font-size: 14px; color: #334e68; margin-bottom: 8px; }
.debate-arg { font-size: 13px; color: #486581; line-height: 1.6; margin: 0; }
.debate-vs { font-size: 20px; font-weight: 900; color: #d9e2ec; align-self: center; }
.judge-box { background: #334e68; border-radius: 10px; padding: 14px 18px; }
.judge-label { font-size: 12px; color: rgba(255,255,255,0.7); margin-bottom: 4px; display: block; }
.judge-verdict { color: #fff; font-size: 14px; line-height: 1.6; margin: 0; }

.synthesis-card { background: linear-gradient(135deg, #f8fbff, #f0faf5); }
.synthesis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.synthesis-block h4 { margin: 0 0 8px; font-size: 14px; color: #334e68; }
.synthesis-block ul { margin: 0; padding-left: 18px; }
.synthesis-block li { font-size: 13px; color: #486581; line-height: 1.7; }
.recommendation-box { background: #334e68; border-radius: 10px; padding: 16px 20px; }
.recommendation-box h4 { margin: 0 0 8px; font-size: 14px; color: rgba(255,255,255,0.8); }
.recommendation-box p { margin: 0; color: #fff; font-size: 14px; line-height: 1.7; }
</style>
