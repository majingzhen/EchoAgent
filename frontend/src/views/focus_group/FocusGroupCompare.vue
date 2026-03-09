<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getFocusGroupMessages, summarizeFocusGroup } from "@/api/focus_group";

const route = useRoute();
const router = useRouter();
const ids = ref<number[]>([]);
const sessions = ref<[any, any]>([null, null]);
const loading = ref(false);

onMounted(async () => {
  const raw = (route.query.ids as string) ?? "";
  ids.value = raw.split(",").map(Number).filter(Boolean);
  if (ids.value.length < 2) return;
  loading.value = true;
  try {
    const [a, b] = await Promise.all(ids.value.slice(0, 2).map(id => getFocusGroupMessages(id)));
    sessions.value = [a.data, b.data];
  } catch { /* ignore */ }
  loading.value = false;
});

const goBack = () => router.push("/focus-groups/history");
</script>

<template>
  <section class="card">
    <div class="header-row">
      <h2>焦点小组 - 对比</h2>
      <button @click="goBack">返回列表</button>
    </div>

    <p v-if="loading" class="tip">加载中...</p>
    <p v-else-if="ids.length < 2" class="tip">请从历史列表勾选 2 条记录进行对比</p>

    <div v-else class="compare-grid">
      <div v-for="(msgs, idx) in sessions" :key="idx" class="compare-col">
        <h3>会话 #{{ ids[idx] }}</h3>
        <div v-if="msgs" class="messages">
          <div v-for="(m, mi) in msgs" :key="mi" :class="['msg', m.sender_type]">
            <span class="msg-sender">{{ m.sender_type === 'user' ? '提问' : m.persona_name }}</span>
            <span class="msg-content">{{ m.content }}</span>
          </div>
        </div>
        <p v-else class="tip">暂无数据</p>
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
.messages { display: flex; flex-direction: column; gap: 8px; max-height: 500px; overflow-y: auto; }
.msg { display: flex; gap: 8px; align-items: flex-start; }
.msg.user { flex-direction: row-reverse; }
.msg-sender { font-size: 12px; color: #829ab1; white-space: nowrap; min-width: 50px; text-align: right; }
.msg.user .msg-sender { text-align: left; }
.msg-content { background: #f0f4f8; border-radius: 6px; padding: 6px 10px; font-size: 13px; line-height: 1.5; }
.msg.user .msg-content { background: #334e68; color: #fff; }
button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:hover { background: #243b53; }
</style>
