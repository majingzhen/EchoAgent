<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

const quickActions = [
  { label: "生成画像组",   desc: "描述目标人群，AI 秒级生成",   path: "/personas/create",   icon: "👥" },
  { label: "发起焦点讨论", desc: "向虚拟消费者提问，获取真实反馈", path: "/audience",           icon: "💬" },
  { label: "测试传播内容", desc: "预判文案在社交平台的扩散效果",   path: "/analysis?tab=simulation", icon: "📡" },
  { label: "生成营销文案", desc: "多 Agent 协作，全流程生成内容",  path: "/content",            icon: "✍️" },
];

const moduleGroups = [
  {
    group: "受众洞察",
    color: "#e0f0ff",
    accent: "#2b6cb0",
    items: [
      {
        icon: "👥", title: "画像工厂", subtitle: "生成虚拟消费者",
        path: "/audience",
        what: "描述目标人群，AI 生成一组有名字、职业、消费习惯、媒体偏好的虚拟用户。",
        example: "「25-35岁一线城市白领，关注性价比与品质」→ 6 个差异化画像",
      },
      {
        icon: "💬", title: "焦点小组", subtitle: "向虚拟消费者提问",
        path: "/audience",
        what: "选一组画像提问，每个画像独立作答，AI 汇总共识与分歧。",
        example: "「你会为这款精华液付 299 吗？」→ 6 个画像从不同角度回答",
      },
    ],
  },
  {
    group: "内容创作",
    color: "#fefce8",
    accent: "#b7791f",
    items: [
      {
        icon: "✍️", title: "内容工坊", subtitle: "多 Agent 协作生成文案",
        path: "/content",
        what: "输入产品 Brief，AI 依次扮演策略师→文案师→消费者评审→合规官，生成并评选最优文案。",
        example: "Brief「精华液温和提亮，目标小红书」→ 3个策略方向 → 3版文案 → 画像打分",
      },
    ],
  },
  {
    group: "市场与分析",
    color: "#f0fff4",
    accent: "#276749",
    items: [
      {
        icon: "🧠", title: "市场图谱", subtitle: "竞品洞察与知识图谱",
        path: "/analysis?tab=market",
        what: "上传竞品文本，AI 提取关键实体关系，构建可视化图谱并生成竞品分析报告。",
        example: "「竞品A的小红书评论汇总」→ 提取价格/成分/口碑节点 → 注入工坊",
      },
      {
        icon: "📡", title: "传播推演", subtitle: "模拟社交传播效果",
        path: "/analysis?tab=simulation",
        what: "让虚拟画像在模拟社交平台传播 N 轮，观察点赞、评论、转发、情绪曲线。",
        example: "「7天提亮限时299」在 8 轮传播中的互动率与情绪走向",
      },
      {
        icon: "🛡️", title: "舆情预判", subtitle: "负面风险预判与应对",
        path: "/analysis?tab=sentiment",
        what: "输入潜在负面事件，AI 评估传播风险，并发生成 3 套应对方案，推荐最优执行时间窗口。",
        example: "「博主发视频称产品含违禁成分」→ 风险 8/10 → 3套方案 → 推荐4小时内发声",
      },
      {
        icon: "♟️", title: "策略建议", subtitle: "5 种思维模型多维决策",
        path: "/analysis?tab=strategy",
        what: "输入业务决策问题，AI 用第一性原理、博弈论等5种模型独立分析后综合输出。",
        example: "「要不要进入下沉市场？」→ 5模型各自分析 → 辩论 → 决策框架",
      },
    ],
  },
];

const scenario = [
  { step: "1", action: "画像工厂", desc: "描述「精华液目标人群」，生成 6 个差异化虚拟消费者" },
  { step: "2", action: "市场图谱", desc: "上传竞品文本，获取「竞品成分被诟病」等洞察" },
  { step: "3", action: "焦点小组", desc: "问画像「看到竞品负评后你怎么看我们产品」" },
  { step: "4", action: "内容工坊", desc: "注入竞品洞察，AI 生成以成分安全为差异点的文案" },
  { step: "5", action: "传播推演", desc: "用最优文案跑 8 轮模拟，确认情绪走向后上线" },
];
</script>

<template>
  <div class="page">

    <!-- Hero -->
    <div class="hero">
      <h2>EchoAgent — AI 虚拟用研平台</h2>
      <p class="tagline">
        用 AI 生成虚拟消费者，在投放前完成用研、焦点访谈、内容测试全流程。<br>
        不招募真实用户，不等报告，秒级获取目标人群反馈。
      </p>
    </div>

    <!-- 快速入口 -->
    <div class="quick-actions">
      <div
        v-for="a in quickActions" :key="a.label"
        class="qa-card"
        @click="router.push(a.path)"
      >
        <span class="qa-icon">{{ a.icon }}</span>
        <div>
          <div class="qa-label">{{ a.label }}</div>
          <div class="qa-desc">{{ a.desc }}</div>
        </div>
      </div>
    </div>

    <!-- 功能模块 -->
    <div v-for="mg in moduleGroups" :key="mg.group" class="module-group">
      <h3 class="group-title" :style="{ borderColor: mg.accent }">{{ mg.group }}</h3>
      <div class="module-cards">
        <div
          v-for="m in mg.items" :key="m.title"
          class="module-card"
          :style="{ background: mg.color }"
          @click="router.push(m.path)"
        >
          <div class="mc-top">
            <span class="mc-icon">{{ m.icon }}</span>
            <div>
              <div class="mc-title">{{ m.title }}</div>
              <div class="mc-sub">{{ m.subtitle }}</div>
            </div>
          </div>
          <p class="mc-what">{{ m.what }}</p>
          <div class="mc-example">{{ m.example }}</div>
          <div class="mc-enter">进入 →</div>
        </div>
      </div>
    </div>

    <!-- 典型场景 -->
    <h3 class="section-title">新品上市前完整测试流程</h3>
    <div class="scenario">
      <template v-for="(s, i) in scenario" :key="i">
        <div class="scenario-step">
          <div class="step-num">{{ s.step }}</div>
          <div class="step-body">
            <div class="step-action">{{ s.action }}</div>
            <div class="step-desc">{{ s.desc }}</div>
          </div>
        </div>
        <div v-if="i < scenario.length - 1" class="step-arrow">→</div>
      </template>
    </div>

  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px; }

.hero { text-align: center; padding: 20px 0 4px; }
.hero h2 { font-size: 24px; margin: 0 0 10px; }
.tagline { color: #486581; font-size: 15px; line-height: 1.8; margin: 0; }

/* Quick actions */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.qa-card {
  background: #fff;
  border: 1px solid #d9e2ec;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.qa-card:hover {
  border-color: #334e68;
  box-shadow: 0 2px 8px rgba(51,78,104,0.1);
}
.qa-icon { font-size: 22px; flex-shrink: 0; }
.qa-label { font-size: 14px; font-weight: 600; color: #102a43; margin-bottom: 2px; }
.qa-desc { font-size: 12px; color: #829ab1; line-height: 1.4; }

/* Module groups */
.module-group { display: flex; flex-direction: column; gap: 10px; }
.group-title {
  margin: 0;
  font-size: 15px;
  color: #102a43;
  border-left: 3px solid #334e68;
  padding-left: 10px;
}
.module-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
}
.module-card {
  border: 1px solid #d9e2ec;
  border-radius: 10px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.module-card:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.08); }
.mc-top { display: flex; align-items: center; gap: 10px; }
.mc-icon { font-size: 24px; }
.mc-title { font-size: 15px; font-weight: 700; color: #102a43; }
.mc-sub { font-size: 12px; color: #627d98; }
.mc-what { margin: 0; font-size: 13px; color: #334e68; line-height: 1.6; }
.mc-example {
  background: rgba(255,255,255,0.6);
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 12px;
  color: #486581;
  line-height: 1.5;
}
.mc-enter {
  font-size: 13px;
  font-weight: 600;
  color: #334e68;
  margin-top: auto;
}

/* Scenario */
.section-title {
  margin: 0;
  font-size: 15px;
  color: #102a43;
  border-left: 3px solid #334e68;
  padding-left: 10px;
}
.scenario {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.scenario-step { display: flex; align-items: flex-start; gap: 8px; }
.step-num {
  width: 26px; height: 26px; background: #334e68; color: #fff;
  border-radius: 50%; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}
.step-body {
  background: #fff; border: 1px solid #d9e2ec; border-radius: 8px;
  padding: 9px 12px; max-width: 170px;
}
.step-action { font-size: 12px; font-weight: 700; color: #334e68; margin-bottom: 3px; }
.step-desc { font-size: 11px; color: #486581; line-height: 1.5; }
.step-arrow { font-size: 16px; color: #9fb3c8; }
</style>
