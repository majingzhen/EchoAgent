<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { createSimulation, getSimulationReport, getSimulationStatus, getTask, startSimulation } from "@/api/simulation";
import { useWebSocket } from "@/composables/useWebSocket";
import { getPersonaGroups } from "@/api/persona";
import FileUploadField from "@/components/FileUploadField.vue";

const route = useRoute();
const groups = ref<any[]>([]);
const form = ref({
  persona_group_id: 0,
  platform: "小红书",
  content_text: "新品精华上线，7天改善暗沉，限时福利价299元。",
  config: { max_rounds: 8 },
});

const sessionId = ref<number | null>(null);
const taskId = ref<string>("");
const status = ref<any>(null);
const report = ref<any>(null);
const error = ref("");
const loading = ref(false);
const readonly = ref(false);

const wsPath = computed(() => (sessionId.value ? `/api/ws/simulation/${sessionId.value}` : ""));
const { connected, messages, connect, send } = useWebSocket(() => wsPath.value);

onMounted(async () => {
  try {
    const resp = await getPersonaGroups();
    groups.value = resp.data ?? [];
    if (groups.value.length > 0) {
      form.value.persona_group_id = groups.value[0].id;
    }
  } catch {
    // 加载失败时保持手填
  }

  // 历史回看模式
  const historyId = Number(route.query.session_id);
  if (historyId) {
    readonly.value = true;
    sessionId.value = historyId;
    try {
      const sim = await getSimulationStatus(historyId);
      status.value = sim.data;
      const rpt = await getSimulationReport(historyId);
      report.value = rpt.data;
    } catch { /* ignore */ }
  }
});

const createSession = async () => {
  loading.value = true;
  error.value = "";
  report.value = null;
  try {
    const resp = await createSimulation(form.value);
    sessionId.value = resp.data.id;
  } catch (e: any) {
    error.value = e.message ?? "创建模拟失败";
  } finally {
    loading.value = false;
  }
};

const run = async () => {
  if (!sessionId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const resp = await startSimulation(sessionId.value);
    taskId.value = resp.data.task_id;
    connect();
    send({ type: "subscribe", session_id: sessionId.value });
    await pollStatus();
  } catch (e: any) {
    error.value = e.message ?? "启动失败";
  } finally {
    loading.value = false;
  }
};

const pollStatus = async () => {
  if (!sessionId.value || !taskId.value) return;
  for (let i = 0; i < 90; i += 1) {
    const [task, sim] = await Promise.all([getTask(taskId.value), getSimulationStatus(sessionId.value)]);
    status.value = sim.data;
    if (task.data.status === "completed") {
      const reportResp = await getSimulationReport(sessionId.value);
      report.value = reportResp.data;
      break;
    }
    if (task.data.status === "failed") {
      throw new Error(task.data.error ?? "模拟任务失败");
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
};
</script>

<template>
  <section class="card">
    <h2>沙盘推演</h2>
    <div class="grid">
      <label>
        画像组
        <select v-if="groups.length" v-model.number="form.persona_group_id">
          <option v-for="g in groups" :key="g.id" :value="g.id">
            #{{ g.id }} {{ g.name }}（{{ g.persona_count }} 人）
          </option>
        </select>
        <input v-else v-model.number="form.persona_group_id" type="number" min="1" placeholder="输入画像组 ID" />
      </label>
      <label>平台<input v-model="form.platform" /></label>
      <FileUploadField
        v-model="form.content_text"
        label="营销内容文件"
        placeholder="上传待测试的文案 / 推文 / 活动策划"
      />
      <label>最大轮次<input v-model.number="form.config.max_rounds" type="number" min="3" max="20" /></label>
    </div>
    <div class="actions">
      <button :disabled="loading || readonly" @click="createSession">创建模拟</button>
      <button :disabled="loading || !sessionId || readonly" @click="run">启动模拟</button>
    </div>
    <p v-if="sessionId">会话 ID: {{ sessionId }}，WebSocket: {{ connected ? "已连接" : "未连接" }}</p>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <section v-if="status" class="card">
    <h3>实时状态</h3>
    <p>状态: {{ status.status }}，轮次: {{ status.current_round }}/{{ status.total_rounds }}</p>
    <pre>{{ status.metrics_timeline }}</pre>
  </section>

  <div v-if="status || report" class="disclaimer">
    以上数据由 AI 基于画像特征模拟生成，反映相对趋势，不代表真实平台数据，请勿作为精确预测依据。
  </div>

  <section class="card">
    <h3>WebSocket 消息</h3>
    <ul>
      <li v-for="(msg, idx) in messages.slice(-12)" :key="idx">{{ msg }}</li>
    </ul>
  </section>

  <section v-if="report" class="card">
    <h3>模拟报告 <span class="report-hint">参考趋势，非真实预测</span></h3>
    <p>{{ report.executive_summary }}</p>
    <pre>{{ report.metrics }}</pre>
    <ul>
      <li v-for="(risk, idx) in report.risks" :key="idx">{{ risk }}</li>
    </ul>
  </section>
</template>

<style scoped>
.card {
  border: 1px solid #d9e2ec;
  border-radius: 12px;
  background: #fff;
  padding: 16px;
  margin-bottom: 14px;
}
.grid { display: grid; gap: 10px; }
label { display: grid; gap: 6px; }
input, select, textarea { border: 1px solid #bcccdc; border-radius: 8px; padding: 8px; }
.actions { display: flex; gap: 10px; margin-top: 8px; }
button {
  border: 0; border-radius: 8px; padding: 8px 12px;
  color: #fff; background: #334e68; cursor: pointer;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
.error { color: #d64545; }
.disclaimer {
  font-size: 12px;
  color: #829ab1;
  background: #f8fbff;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 8px 14px;
  margin-bottom: 14px;
}
.report-hint {
  font-size: 12px;
  font-weight: 400;
  color: #829ab1;
  margin-left: 8px;
}
</style>
