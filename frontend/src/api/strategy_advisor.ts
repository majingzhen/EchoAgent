import service from "./index";

export const runStrategyAdvisor = (payload: { question: string; context_info?: string }) =>
  service.post("/strategy-advisor/analyze", payload);

export const getStrategyAdvisorSessions = () => service.get("/strategy-advisor/sessions");

export const getStrategyAdvisorSession = (sessionId: number) =>
  service.get(`/strategy-advisor/sessions/${sessionId}`);
