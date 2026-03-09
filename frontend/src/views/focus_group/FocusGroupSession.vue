<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import {
  askFocusGroup,
  createFocusGroupSession,
  getFocusGroupSession,
  summarizeFocusGroup,
} from "@/api/focus_group";
import { getPersonaGroups } from "@/api/persona";
import { focusGroupTopics } from "@/config/templates";

const route = useRoute();

const groups = ref<any[]>([]);
const personaGroupId = ref(Number(route.query.groupId) || 0);
const topic = ref("新品定价反馈");
const question = ref("你觉得这个产品如何？有什么顾虑或期待？");
const askMode = ref<"independent" | "discussion">("independent");

const sessionId = ref<number | null>(null);

type MsgType = "user" | "persona" | "facilitator" | "debate" | "phase";
const messages = ref<{
  type: MsgType;
  phase?: number;
  personaName?: string;
  respondingTo?: string;
  content: string;
}[]>([]);

const pending = ref(0);
const total = ref(0);
const currentPhase = ref(0);
const summary = ref<any>(null);
const error = ref("");
const loading = ref(false);
const resumeMode = ref(false);
const connected = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const fileName = ref("");
const resumeTopic = ref("");
const resumeGroupName = ref("");
const imageInput = ref<HTMLInputElement | null>(null);
const imageName = ref("");
const summarizing = ref(false);

let wsInstance: WebSocket | null = null;

const PHASE_LABELS: Record<number, string> = {
  1: "第一阶段：独立作答",
  2: "第二阶段：主持人梳理",
  3: "第三阶段：交叉讨论",
};

const setupWS = () => {
  wsInstance?.close();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const base = (import.meta.env.VITE_WS_BASE_URL as string) ?? `${proto}://${location.hostname}:8000`;
  const ws = new WebSocket(`${base}/api/ws/focus-group/${sessionId.value}`);
  ws.onopen = () => { connected.value = true; };
  ws.onclose = () => { connected.value = false; };
  ws.onerror = () => { connected.value = false; };
  ws.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    if (data.type === "user_message") {
      messages.value.push({ type: "user", content: data.content });
    } else if (data.type === "phase_start") {
      currentPhase.value = data.phase;
      messages.value.push({ type: "phase", phase: data.phase, content: data.label });
    } else if (data.type === "persona_reply") {
      messages.value.push({ type: "persona", phase: data.phase, personaName: data.persona_name, content: data.content });
      pending.value = Math.max(0, pending.value - 1);
    } else if (data.type === "facilitator") {
      messages.value.push({ type: "facilitator", personaName: "主持人", content: data.content });
    } else if (data.type === "debate_reply") {
      messages.value.push({ type: "debate", personaName: data.persona_name, respondingTo: data.responding_to, content: data.content });
    } else if (data.type === "done") {
      pending.value = 0;
      currentPhase.value = 0;
      loading.value = false;
    } else if (data.type === "summary_start") {
      summarizing.value = true;
    } else if (data.type === "summary_done") {
      summary.value = data.data;
      summarizing.value = false;
    } else if (data.type === "error") {
      error.value = data.message ?? "生成失败";
      pending.value = 0;
      loading.value = false;
      summarizing.value = false;
    }
  };
  wsInstance = ws;
};

onUnmounted(() => { wsInstance?.close(); });

const onFileChange = (e: Event) => {
  const f = (e.target as HTMLInputElement).files?.[0];
  fileName.value = f ? f.name : "";
};

const onImageChange = (e: Event) => {
  const f = (e.target as HTMLInputElement).files?.[0];
  imageName.value = f ? f.name : "";
};

onMounted(async () => {
  try {
    const resp = await getPersonaGroups();
    groups.value = resp.data ?? [];
    if (!personaGroupId.value && groups.value.length > 0) {
      personaGroupId.value = groups.value[0].id;
    }
  } catch { /* ignore */ }

  const historyId = Number(route.query.session_id);
  if (historyId) {
    resumeMode.value = true;
    sessionId.value = historyId;
    try {
      const resp = await getFocusGroupSession(historyId);
      const s = resp.data;
      resumeTopic.value = s.topic || "";
      const g = groups.value.find((g: any) => g.id === s.persona_group_id);
      resumeGroupName.value = g ? `#${g.id} ${g.name}（${g.persona_count} 人）` : `#${s.persona_group_id}`;
      messages.value = (s.messages || []).map((m: any) => ({
        type: m.sender_type === "facilitator" ? "facilitator" : m.sender_type,
        personaName: m.persona_name,
        content: m.content,
      }));
      summary.value = s.summary || null;
    } catch { /* ignore */ }
    setupWS();
  }
});

const createSession = async () => {
  if (!personaGroupId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const fd = new FormData();
    fd.append("persona_group_id", String(personaGroupId.value));
    fd.append("topic", topic.value);
    const file = fileInput.value?.files?.[0];
    if (file) fd.append("file", file);
    const resp = await createFocusGroupSession(fd);
    sessionId.value = resp.data.id;
    messages.value = [];
    summary.value = null;
    setupWS();
  } catch (e: any) {
    error.value = e.message ?? "创建会话失败";
  } finally {
    loading.value = false;
  }
};

const ask = async () => {
  if (!sessionId.value) return;
  loading.value = true;
  error.value = "";
  currentPhase.value = askMode.value === "discussion" ? 1 : 0;
  try {
    const fd = new FormData();
    fd.append("question", question.value);
    fd.append("mode", askMode.value);
    const imgFile = imageInput.value?.files?.[0];
    if (imgFile) fd.append("image", imgFile);
    const resp = await askFocusGroup(sessionId.value, fd);
    total.value = resp.data.persona_count ?? 0;
    pending.value = total.value;
  } catch (e: any) {
    error.value = e.message ?? "提问失败";
    loading.value = false;
  }
};

const runSummary = async () => {
  if (!sessionId.value) return;
  summarizing.value = true;
  error.value = "";
  try {
    await summarizeFocusGroup(sessionId.value);
  } catch (e: any) {
    error.value = e.message ?? "生成总结失败";
    summarizing.value = false;
  }
};

const personaMessages = () => messages.value.filter(m => m.type === "persona" || m.type === "debate" || m.type === "facilitator");
</script>

<template>
  <section class="card">
    <h2>焦点小组</h2>
    <p class="tip">选择画像组和话题，可上传产品文档作为讨论背景，画像会基于文档内容回答。</p>

    <!-- 新建模式 -->
    <div v-if="!resumeMode" class="form-grid">
      <div class="row-2">
        <label>
          画像组
          <select v-if="groups.length" v-model.number="personaGroupId">
            <option v-for="g in groups" :key="g.id" :value="g.id">
              #{{ g.id }} {{ g.name }}（{{ g.persona_count }} 人）
            </option>
          </select>
          <input v-else v-model.number="personaGroupId" type="number" min="1" placeholder="输入画像组 ID" />
        </label>
        <label>
          话题
          <input v-model="topic" />
          <select style="margin-top:4px" @change="(e) => { const v = (e.target as HTMLSelectElement).value; if (v) topic = v; (e.target as HTMLSelectElement).value = ''; }">
            <option value="">-- 选择话题模板 --</option>
            <option v-for="t in focusGroupTopics" :key="t.label" :value="t.value">{{ t.label }}</option>
          </select>
        </label>
      </div>

      <label>
        产品文档（可选，支持 .txt / .md / .pdf）
        <div class="file-upload-row">
          <input ref="fileInput" type="file" accept=".txt,.md,.pdf" class="file-input" @change="onFileChange" />
          <span v-if="fileName" class="file-name">{{ fileName }}</span>
        </div>
      </label>

      <button :disabled="loading || !personaGroupId" @click="createSession">
        {{ loading && !sessionId ? "创建中..." : "创建焦点小组会话" }}
      </button>
    </div>

    <!-- 恢复模式 -->
    <div v-else class="resume-info">
      <div class="row-2">
        <div class="info-item"><span class="info-label">画像组</span><span>{{ resumeGroupName }}</span></div>
        <div class="info-item"><span class="info-label">话题</span><span>{{ resumeTopic }}</span></div>
      </div>
    </div>

    <p v-if="error && !sessionId" class="error">{{ error }}</p>
  </section>

  <!-- 提问区 -->
  <section v-if="sessionId" class="card ask-card">
    <div class="ask-header">
      <h3>向画像提问</h3>
      <span class="ws-dot" :class="{ active: connected }">{{ connected ? "WS 已连接" : "WS 未连接" }}</span>
    </div>
    <div class="ask-body">
      <textarea v-model="question" rows="4" class="ask-textarea" placeholder="输入你想了解的问题..." />

      <!-- 模式切换 -->
      <div class="mode-switch">
        <span class="mode-label">提问模式</span>
        <div class="mode-options">
          <button
            type="button"
            :class="['mode-btn', askMode === 'independent' && 'active']"
            @click="askMode = 'independent'"
          >
            独立作答
            <span class="mode-hint">画像各自回答，不互相影响</span>
          </button>
          <button
            type="button"
            :class="['mode-btn', askMode === 'discussion' && 'active']"
            @click="askMode = 'discussion'"
          >
            小组讨论
            <span class="mode-hint">主持人梳理分歧，画像交叉辩论</span>
          </button>
        </div>
      </div>

      <label class="image-upload-label">
        视觉素材（可选，画像将评价图片）
        <div class="file-upload-row">
          <input ref="imageInput" type="file" accept="image/jpeg,image/png,image/webp" class="file-input" @change="onImageChange" />
          <span v-if="imageName" class="file-name">{{ imageName }}</span>
        </div>
      </label>

      <div class="ask-actions">
        <button :disabled="loading || !connected" @click="ask">
          {{ loading && pending > 0 ? `等待回复 ${pending}/${total}` : "发送问题" }}
        </button>
        <button
          :disabled="summarizing || personaMessages().length === 0"
          class="secondary"
          @click="runSummary"
        >
          {{ summarizing ? "总结生成中..." : "生成总结报告" }}
        </button>
      </div>
    </div>
    <p v-if="error && sessionId" class="error">{{ error }}</p>

    <!-- 实时消息流 -->
    <div v-if="messages.length || pending > 0" class="messages">
      <template v-for="(m, idx) in messages" :key="idx">
        <!-- 阶段分隔线 -->
        <div v-if="m.type === 'phase'" class="phase-divider">
          <span>{{ PHASE_LABELS[m.phase!] ?? m.content }}</span>
        </div>

        <!-- 用户问题 -->
        <div v-else-if="m.type === 'user'" class="msg user">
          <span class="msg-sender">你</span>
          <span class="msg-content">{{ m.content }}</span>
        </div>

        <!-- 主持人总结 -->
        <div v-else-if="m.type === 'facilitator'" class="msg facilitator">
          <span class="msg-sender facilitator-name">主持人</span>
          <span class="msg-content facilitator-content">{{ m.content }}</span>
        </div>

        <!-- 讨论辩论回应 -->
        <div v-else-if="m.type === 'debate'" class="msg persona debate-msg">
          <span class="msg-sender">{{ m.personaName }}</span>
          <div class="debate-bubble">
            <span class="responding-tag">回应 {{ m.respondingTo }}</span>
            <span class="msg-content">{{ m.content }}</span>
          </div>
        </div>

        <!-- 普通画像回答 -->
        <div v-else class="msg persona">
          <span class="msg-sender">{{ m.personaName }}</span>
          <span class="msg-content">{{ m.content }}</span>
        </div>
      </template>

      <div v-if="pending > 0" class="msg persona pending-row">
        <span class="msg-sender">...</span>
        <span class="msg-content typing">
          {{ currentPhase === 3 ? "讨论中..." : `还有 ${pending} 个画像正在思考中` }}
        </span>
      </div>
    </div>
  </section>

  <!-- 总结报告 -->
  <section v-if="summary" class="card">
    <h3>焦点小组总结</h3>
    <div class="summary-grid">
      <div class="summary-block">
        <h4>共识观点</h4>
        <ul><li v-for="(item, i) in summary.consensus" :key="i">{{ item }}</li></ul>
      </div>
      <div class="summary-block">
        <h4>分歧点</h4>
        <ul><li v-for="(item, i) in summary.divergence" :key="i">{{ item }}</li></ul>
      </div>
      <div class="summary-block">
        <h4>关键洞察</h4>
        <ul><li v-for="(item, i) in summary.key_insights" :key="i">{{ item }}</li></ul>
      </div>
      <div class="summary-block">
        <h4>建议</h4>
        <ul><li v-for="(item, i) in summary.recommendations" :key="i">{{ item }}</li></ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card {
  border: 1px solid #d9e2ec;
  border-radius: 12px;
  background: #fff;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.tip { color: #486581; font-size: 14px; margin: 0 0 14px; }
.form-grid { display: grid; gap: 12px; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
label { display: grid; gap: 6px; font-size: 14px; }
input, select, textarea {
  border: 1px solid #bcccdc; border-radius: 8px;
  padding: 8px 10px; font-size: 14px;
}
.file-upload-row { display: flex; align-items: center; gap: 10px; }
.file-input {
  flex: 1; min-width: 0; border: 1px solid #bcccdc;
  border-radius: 8px; padding: 6px 10px; font-size: 14px;
}
.file-name { font-size: 13px; color: #486581; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
.resume-info { padding: 4px 0; }
.info-item { display: flex; flex-direction: column; gap: 4px; font-size: 14px; color: #334e68; }
.info-label { font-size: 12px; color: #829ab1; }

/* 提问区 */
.ask-card { padding: 20px 24px 24px; }
.ask-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.ask-header h3 { margin: 0; }
.ws-dot { font-size: 12px; color: #9fb3c8; display: flex; align-items: center; gap: 4px; }
.ws-dot::before {
  content: ""; display: inline-block; width: 8px; height: 8px;
  border-radius: 50%; background: #9fb3c8;
}
.ws-dot.active { color: #27ab83; }
.ws-dot.active::before { background: #27ab83; }
.ask-body { display: flex; flex-direction: column; gap: 12px; }
.image-upload-label { display: grid; gap: 6px; font-size: 14px; }
.ask-textarea {
  width: 100%; min-height: 80px; resize: vertical; font-size: 14px;
  line-height: 1.6; border: 1px solid #bcccdc; border-radius: 8px;
  padding: 12px 14px; box-sizing: border-box;
}
.ask-textarea:focus { outline: none; border-color: #627d98; box-shadow: 0 0 0 2px rgba(98,125,152,0.15); }
.ask-actions { display: flex; gap: 10px; flex-wrap: wrap; }

/* 模式切换 */
.mode-switch { display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.mode-label { font-size: 14px; color: #334e68; margin-top: 10px; white-space: nowrap; }
.mode-options { display: flex; gap: 8px; }
.mode-btn {
  border: 1px solid #d9e2ec; background: #f8fbff; border-radius: 10px;
  padding: 8px 14px; cursor: pointer; text-align: left;
  display: flex; flex-direction: column; gap: 2px; transition: border-color 0.15s, background 0.15s;
  font-size: 14px; font-weight: 500; color: #486581;
}
.mode-btn:hover { border-color: #829ab1; background: #edf5ff; }
.mode-btn.active { border-color: #334e68; background: #edf5ff; color: #102a43; }
.mode-hint { font-size: 11px; font-weight: 400; color: #829ab1; }
.mode-btn.active .mode-hint { color: #486581; }

button {
  border: 0; border-radius: 8px; padding: 8px 16px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.secondary { background: #fff; color: #334e68; border: 1px solid #334e68; }
.secondary:hover:not(:disabled) { background: #f0f4f8; }
.error { color: #d64545; font-size: 14px; margin-top: 8px; }

/* 消息流 */
.messages {
  margin-top: 18px; padding-top: 16px; border-top: 1px solid #e8ecf1;
  display: flex; flex-direction: column; gap: 10px;
  max-height: 560px; overflow-y: auto;
}

/* 阶段分隔线 */
.phase-divider {
  display: flex; align-items: center; gap: 10px;
  color: #829ab1; font-size: 12px; font-weight: 600;
  margin: 4px 0;
}
.phase-divider::before, .phase-divider::after {
  content: ""; flex: 1; height: 1px; background: #e8ecf1;
}

/* 消息气泡 */
.msg { display: flex; gap: 10px; align-items: flex-start; }
.msg.user { flex-direction: row-reverse; }
.msg-sender { font-size: 12px; color: #829ab1; white-space: nowrap; margin-top: 4px; min-width: 64px; text-align: right; }
.msg.user .msg-sender { text-align: left; }
.msg-content {
  background: #f0f4f8; border-radius: 8px; padding: 8px 12px;
  font-size: 14px; line-height: 1.6; max-width: 80%;
}
.msg.user .msg-content { background: #334e68; color: #fff; }

/* 主持人消息 */
.facilitator-name { color: #b7791f !important; font-weight: 600; }
.facilitator-content { background: #fffbf0 !important; border: 1px solid #f6e05e; color: #744210; }

/* 辩论消息 */
.debate-msg .debate-bubble { display: flex; flex-direction: column; gap: 4px; }
.responding-tag {
  font-size: 11px; color: #829ab1; font-style: italic;
  padding-left: 2px;
}
.debate-msg .msg-content { background: #f0faf5; border: 1px solid #9ae6b4; }

/* 等待状态 */
.pending-row .msg-content.typing {
  color: #829ab1; font-style: italic; background: #f8fbff;
  border: 1px dashed #bcccdc;
}

/* 总结 */
.summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.summary-block h4 { margin: 0 0 8px; font-size: 14px; color: #334e68; }
.summary-block ul { margin: 0; padding-left: 18px; }
.summary-block li { font-size: 14px; color: #486581; line-height: 1.7; }
</style>
