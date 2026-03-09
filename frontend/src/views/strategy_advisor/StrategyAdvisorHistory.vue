<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getStrategyAdvisorSessions } from "@/api/strategy_advisor";
import { downloadReport } from "@/api/export";

const router = useRouter();
const sessions = ref<any[]>([]);
const loading = ref(false);

const statusMap: Record<string, string> = { pending: "待运行", running: "运行中", completed: "已完成", failed: "失败" };
const statusClass = (s: string) => s === "completed" ? "tag-ok" : s === "failed" ? "tag-err" : "tag-run";

onMounted(async () => {
  loading.value = true;
  try {
    const resp = await getStrategyAdvisorSessions();
    sessions.value = resp.data ?? [];
  } catch { /* ignore */ }
  loading.value = false;
});

const goNew = () => router.push("/strategy-advisor/session");
const goDetail = (id: number) => router.push(`/strategy-advisor/session?session_id=${id}`);
const fmtTime = (t: string) => t ? t.replace("T", " ").slice(0, 19) : "";
</script>

<template>
  <section class="card">
    <div class="header-row">
      <h2>策略参谋 - 历史会话</h2>
      <button @click="goNew">新建分析</button>
    </div>

    <p v-if="loading" class="tip">加载中...</p>
    <p v-else-if="!sessions.length" class="tip">暂无历史会话，点击上方按钮创建</p>

    <div v-else class="grid-list">
      <div v-for="s in sessions" :key="s.id" class="item-card">
        <div class="item-top">
          <span class="item-id">#{{ s.id }}</span>
          <span :class="['tag', statusClass(s.status)]">{{ statusMap[s.status] ?? s.status }}</span>
        </div>
        <div class="item-body desc">{{ (s.question ?? "").slice(0, 80) }}</div>
        <div class="item-meta">
          <span>{{ fmtTime(s.created_at) }}</span>
        </div>
        <button class="detail-btn" @click="goDetail(s.id)">查看详情</button>
        <div v-if="s.status === 'completed'" class="export-row">
          <button class="export-btn" @click="downloadReport('strategy-advisor', s.id, 'pdf')">PDF</button>
          <button class="export-btn" @click="downloadReport('strategy-advisor', s.id, 'pptx')">PPT</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card { border: 1px solid #d9e2ec; border-radius: 12px; background: #fff; padding: 20px 24px; }
.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-row h2 { margin: 0; }
.tip { color: #486581; font-size: 14px; }
.grid-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.item-card { border: 1px solid #d9e2ec; border-radius: 10px; padding: 14px; background: #f8fbff; }
.item-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.item-id { font-weight: 600; font-size: 14px; color: #334e68; }
.tag { font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.tag-ok { background: #d4edda; color: #155724; }
.tag-err { background: #f8d7da; color: #721c24; }
.tag-run { background: #fff3cd; color: #856404; }
.item-body { font-size: 14px; color: #334e68; margin-bottom: 6px; }
.desc { font-size: 13px; color: #627d98; }
.item-meta { font-size: 12px; color: #829ab1; margin-bottom: 10px; }
.detail-btn {
  width: 100%; border: 1px solid #334e68; background: #fff; color: #334e68;
  border-radius: 6px; padding: 6px; font-size: 13px; cursor: pointer;
}
.detail-btn:hover { background: #f0f4f8; }
.export-row { display: flex; gap: 6px; margin-top: 6px; }
.export-btn {
  flex: 1; border: 1px solid #bcccdc; background: #f8fbff; color: #486581;
  border-radius: 6px; padding: 4px; font-size: 12px; cursor: pointer;
}
.export-btn:hover { background: #edf3ff; }
button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:hover { background: #243b53; }
</style>
