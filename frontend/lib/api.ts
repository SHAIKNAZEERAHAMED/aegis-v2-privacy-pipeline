const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setSession(token: string, sessionId: string) {
  localStorage.setItem("access_token", token);
  localStorage.setItem("session_id", sessionId);
}

export function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("session_id");
}

export function isAuthed(): boolean {
  return !!getToken();
}

async function request(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* noop */
    }
    throw new Error(detail);
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res;
}

export const api = {
  signup: (email: string, password: string) =>
    request("/api/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),

  login: (email: string, password: string) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  uploadVideo: (blob: Blob) => {
    const form = new FormData();
    form.append("file", blob, "capture.webm");
    return request("/api/videos", { method: "POST", body: form });
  },

  startProcessing: (videoId: string) => request(`/api/videos/${videoId}/process`, { method: "POST" }),

  getStatus: (videoId: string) => request(`/api/videos/${videoId}/status`),

  listVideos: () => request("/api/videos"),

  getVideo: (videoId: string) => request(`/api/videos/${videoId}`),

  deleteVideo: (videoId: string) => request(`/api/videos/${videoId}`, { method: "DELETE" }),

  // These two are loaded directly by <video>/<img> src or a plain <a href>,
  // not via fetch() — the browser won't attach our Authorization header for
  // those, so the token rides along as a query param instead (the backend's
  // get_current_user_flexible dependency accepts either).
  downloadUrl: (videoId: string) => {
    const token = getToken();
    return `${API_BASE}/api/videos/${videoId}/download${token ? `?token=${encodeURIComponent(token)}` : ""}`;
  },

  calibrationFrameUrl: (videoId: string) => {
    const token = getToken();
    return `${API_BASE}/api/calibration/${videoId}/frame${token ? `?token=${encodeURIComponent(token)}` : ""}`;
  },

  submitCalibration: (videoId: string, recognizable: boolean) =>
    request("/api/calibration", {
      method: "POST",
      body: JSON.stringify({ video_id: videoId, recognizable }),
    }),

  authHeader: () => {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  },
};
