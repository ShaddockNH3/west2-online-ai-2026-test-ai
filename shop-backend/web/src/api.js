const API_BASE = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";

export function getToken() {
  return localStorage.getItem("accessToken") || "";
}

export function getRefreshToken() {
  return localStorage.getItem("refreshToken") || "";
}

export function saveAuth(data) {
  localStorage.setItem("accessToken", data.accessToken);
  localStorage.setItem("refreshToken", data.refreshToken);
  localStorage.setItem("user", JSON.stringify(data.user));
}

export function clearAuth() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("user");
}

export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem("user") || "null");
  } catch {
    return null;
  }
}

async function rawRequest(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { message: text };
  }
  return { status: response.status, data };
}

let refreshing = null;

async function refreshTokens() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  if (!refreshing) {
    refreshing = (async () => {
      const { status, data } = await rawRequest("/auth/refresh", {
        method: "POST",
        body: { refreshToken },
      });
      refreshing = null;
      if (status === 200 && data?.accessToken) {
        saveAuth(data);
        return true;
      }
      clearAuth();
      return false;
    })();
  }
  return refreshing;
}

export async function api(path, options = {}) {
  let { status, data } = await rawRequest(path, { ...options, token: getToken() });
  if (status === 401 && options.skipAuth !== true && getRefreshToken()) {
    const ok = await refreshTokens();
    if (ok) {
      ({ status, data } = await rawRequest(path, { ...options, token: getToken() }));
    }
  }
  if (status >= 400) {
    const error = new Error(data?.message || `请求失败（${status}）`);
    error.status = status;
    error.code = data?.code;
    error.details = data?.details;
    throw error;
  }
  return data;
}

export const http = {
  get: (path) => api(path),
  post: (path, body) => api(path, { method: "POST", body }),
  patch: (path, body) => api(path, { method: "PATCH", body }),
  put: (path, body) => api(path, { method: "PUT", body }),
  del: (path) => api(path, { method: "DELETE" }),
};

export function money(value) {
  return `¥${value ?? "0.00"}`;
}
