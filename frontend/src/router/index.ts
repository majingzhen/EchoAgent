import { createRouter, createWebHistory } from "vue-router";

const routes = [
  // ── 主导航 5 个入口 ──────────────────────
  { path: "/", component: () => import("@/views/Dashboard.vue") },
  { path: "/audience", component: () => import("@/views/AudienceHub.vue") },
  { path: "/content", component: () => import("@/views/ContentHub.vue") },
  { path: "/analysis", component: () => import("@/views/AnalysisHub.vue") },
  { path: "/workflow", component: () => import("@/views/workflow/WorkflowRun.vue") },

  // ── 深链接（各功能详情页，保留供内部跳转）───
  { path: "/personas/create", component: () => import("@/views/persona/PersonaCreate.vue") },
  { path: "/focus-groups/session", component: () => import("@/views/focus_group/FocusGroupSession.vue") },
  { path: "/focus-groups/compare", component: () => import("@/views/focus_group/FocusGroupCompare.vue") },
  { path: "/simulation/run", component: () => import("@/views/simulation/SimulationRun.vue") },
  { path: "/workshop/session", component: () => import("@/views/workshop/WorkshopSession.vue") },
  { path: "/market/graph", component: () => import("@/views/market/MarketGraph.vue") },
  { path: "/sentiment-guard/session", component: () => import("@/views/sentiment_guard/SentimentGuard.vue") },
  { path: "/strategy-advisor/session", component: () => import("@/views/strategy_advisor/StrategyAdvisor.vue") },
  { path: "/search", component: () => import("@/views/search/SearchEnhance.vue") },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
