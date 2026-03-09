import service from "./index";

export type PersonaGeneratePayload = {
  group_name: string;
  description: string;
  count: number;
};

export const generatePersonas = (payload: PersonaGeneratePayload) => service.post("/personas/generate", payload);
export const getPersonaGroups = () => service.get("/personas/groups");
export const getPersonaGroupDetail = (groupId: number) => service.get(`/personas/groups/${groupId}`);
export const getPersonaMemories = (personaId: number) => service.get(`/personas/${personaId}/memories`);
