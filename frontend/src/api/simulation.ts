import service from "./index";

export const getSimulations = () => service.get("/simulations");

export const createSimulation = (payload: {
  content_text: string;
  persona_group_id: number;
  platform: string;
  config: Record<string, unknown>;
}) => service.post("/simulations", payload);

export const startSimulation = (sessionId: number) => service.post(`/simulations/${sessionId}/start`);
export const getSimulationStatus = (sessionId: number) => service.get(`/simulations/${sessionId}/status`);
export const getSimulationReport = (sessionId: number) => service.get(`/simulations/${sessionId}/report`);
export const getTask = (taskId: string) => service.get(`/tasks/${taskId}`);
