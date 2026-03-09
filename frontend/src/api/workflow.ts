import service from "./index";

export const getWorkflowTemplates = () => service.get("/workflows/templates");

export const createWorkflow = (data: {
  workflow_type: string;
  persona_group_id: number;
  platform: string;
  brand_tone: string;
  brief: string;
  market_source_text?: string;
  disabled_steps?: string[];
}) => service.post("/workflows", data);

export const getWorkflows = () => service.get("/workflows");

export const getWorkflow = (workflowId: number) =>
  service.get(`/workflows/${workflowId}`);

export const getWorkflowStatus = (workflowId: number) =>
  service.get(`/workflows/${workflowId}/status`);

export const completeWorkflowStep = (workflowId: number, stepName: string, notes = "") =>
  service.post(`/workflows/${workflowId}/steps/${stepName}/complete`, { notes });
