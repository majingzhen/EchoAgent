const _base = (() => {
  const explicitBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
  const backendTarget = import.meta.env.VITE_BACKEND_TARGET as string | undefined;
  const normalizedTarget = backendTarget ? backendTarget.replace(/\/$/, "") : undefined;
  return explicitBase ?? (normalizedTarget ? `${normalizedTarget}/api` : "/api");
})();

export const downloadReport = (module: string, sessionId: number, format: "pdf" | "pptx") => {
  const url = `${_base}/export/${module}/${sessionId}/${format}`;
  const link = document.createElement("a");
  link.href = url;
  link.download = `report_${module}_${sessionId}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
