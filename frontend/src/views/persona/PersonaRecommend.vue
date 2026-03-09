<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { recommendPersonaCombination } from "@/api/persona";

const router = useRouter();
const scenario = ref("");
const loading = ref(false);
const error = ref("");
const result = ref<any>(null);

const submit = async () => {
  if (!scenario.value.trim()) return;
  loading.value = true;
  error.value = "";
  result.value = null;
  try {
    const resp = await recommendPersonaCombination(scenario.value.trim());
    result.value = (resp as any).data ?? resp;
  } catch (e: any) {
    error.value = e.message ?? "推荐失败";
  } finally {
    loading.value = false;
  }
};

const goGroup = (id: number) => router.push(`/focus-groups/session?groupId=${id}`);
</script>

<template>
  <section class="card">
    <h2>画像组合推荐</h2>
    <p class="tip">描述你的营销场景，AI 将分析并推荐最合适的画像组合。</p>

    <div class="form-grid">
      <label>
        营销场景描述
        <textarea
          v-model="scenario"
          rows="5"
          placeholder="例如：面向一二线城市 25-35 岁职场女性，推广一款主打成分护肤的精华液，定价 300 元，预算偏保守，主要渠道是小红书和抖音。"
        />
      </label>
      <button :disabled="loading || !scenario.trim()" @click="submit">
        {{ loading ? "分析中..." : "获取推荐" }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <section v-if="result" class="card result-card">
    <div class="recommend-header">
      <div class="recommend-badge">
        <span class="badge-label">推荐画像组</span>
        <span class="badge-value">{{ result.recommended_group_name || `#${result.recommended_group_id}` }}</span>
      </div>
      <button v-if="result.recommended_group_id" @click="goGroup(result.recommended_group_id)">
        用此组创建焦点小组
      </button>
    </div>

    <div class="reasoning-block">
      <h4>推荐理由</h4>
      <p>{{ result.reasoning }}</p>
    </div>

    <div v-if="result.match_scores?.length" class="scores-section">
      <h4>各画像组匹配度</h4>
      <div class="score-list">
        <div
          v-for="item in result.match_scores"
          :key="item.group_id"
          :class="['score-item', item.group_id === result.recommended_group_id ? 'best' : '']"
        >
          <div class="score-top">
            <span class="score-name">{{ item.group_name }} <span class="score-id">#{{ item.group_id }}</span></span>
            <span class="score-bar-wrap">
              <span class="score-bar" :style="{ width: `${item.score}%` }" />
            </span>
            <span class="score-num">{{ item.score }}</span>
          </div>
          <p class="score-reason">{{ item.reason }}</p>
        </div>
      </div>
    </div>

    <div v-if="result.complementary_types?.length" class="complement-section">
      <h4>建议补充的画像类型</h4>
      <ul>
        <li v-for="(t, i) in result.complementary_types" :key="i">{{ t }}</li>
      </ul>
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
label { display: grid; gap: 6px; font-size: 14px; }
textarea {
  border: 1px solid #bcccdc;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  box-sizing: border-box;
  width: 100%;
}
button {
  border: 0; border-radius: 8px; padding: 8px 16px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.error { color: #d64545; font-size: 14px; margin-top: 8px; }

.result-card { padding: 20px 24px; }
.recommend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.recommend-badge { display: flex; flex-direction: column; gap: 4px; }
.badge-label { font-size: 12px; color: #829ab1; }
.badge-value { font-size: 20px; font-weight: 700; color: #334e68; }
.reasoning-block { margin-bottom: 20px; }
.reasoning-block h4 { margin: 0 0 8px; font-size: 14px; color: #334e68; }
.reasoning-block p { font-size: 14px; color: #486581; line-height: 1.7; margin: 0; }
.scores-section { margin-bottom: 20px; }
.scores-section h4 { margin: 0 0 10px; font-size: 14px; color: #334e68; }
.score-list { display: flex; flex-direction: column; gap: 10px; }
.score-item {
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 10px 14px;
  background: #f8fbff;
}
.score-item.best { border-color: #334e68; background: #edf5ff; }
.score-top { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.score-name { font-size: 14px; font-weight: 600; color: #334e68; min-width: 120px; }
.score-id { font-weight: 400; color: #829ab1; font-size: 12px; }
.score-bar-wrap {
  flex: 1; height: 8px; background: #d9e2ec; border-radius: 4px; overflow: hidden;
}
.score-bar { display: block; height: 100%; background: #334e68; border-radius: 4px; transition: width 0.4s; }
.score-item.best .score-bar { background: #27ab83; }
.score-num { font-size: 13px; font-weight: 700; color: #334e68; min-width: 32px; text-align: right; }
.score-reason { font-size: 13px; color: #627d98; margin: 0; }
.complement-section h4 { margin: 0 0 8px; font-size: 14px; color: #334e68; }
.complement-section ul { margin: 0; padding-left: 18px; }
.complement-section li { font-size: 14px; color: #486581; line-height: 1.7; }
</style>
