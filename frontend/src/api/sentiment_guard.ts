import service from "./index";

export const runSentimentGuard = (payload: { mode: string; event_description: string; current_sentiment?: string }) =>
  service.post("/sentiment-guard/assess", payload);

export const getSentimentGuardSessions = () => service.get("/sentiment-guard/sessions");

export const getSentimentGuardSession = (sessionId: number) =>
  service.get(`/sentiment-guard/sessions/${sessionId}`);
