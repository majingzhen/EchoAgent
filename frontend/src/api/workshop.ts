import service from "./index";

export const getWorkshopSessions = () => service.get("/workshop/sessions");

export const createWorkshopSession = (payload: {
  persona_group_id: number;
  platform: string;
  brand_tone: string;
  brief: string;
  goal: string;
  product: string;
}) => service.post("/workshop/sessions", payload);

export const runWorkshopSession = (sessionId: number, payload: { market_graph_id?: number | null }) =>
  service.post(`/workshop/sessions/${sessionId}/run`, payload);

export const getWorkshopSession = (sessionId: number) => service.get(`/workshop/sessions/${sessionId}`);

export const injectWorkshopInsights = (sessionId: number, graphId: number) =>
  service.post(`/workshop/sessions/${sessionId}/inject-insights`, { graph_id: graphId });

export const createWorkshopABTest = (sessionId: number) => service.post(`/workshop/sessions/${sessionId}/ab-test`);

export const saveContentResult = (sessionId: number, payload: {
  variant: string;
  went_live: boolean;
  actual_engagement_rate?: number | null;
  actual_conversion_rate?: number | null;
  notes?: string;
}) => service.post(`/workshop/sessions/${sessionId}/results`, payload);

export const getContentResults = (sessionId: number) =>
  service.get(`/workshop/sessions/${sessionId}/results`);
