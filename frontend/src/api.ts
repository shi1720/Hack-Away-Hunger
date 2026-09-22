import type { Auth } from "./types";
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
async function request(path: string, options: RequestInit): Promise<Response> {
  try {
    return await fetch(path, {
      ...options,
      signal: AbortSignal.timeout(20000),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError")
      throw new Error(
        "The request timed out. Refresh the workspace before retrying any change.",
      );
    throw new Error(
      "Could not reach Pantry Relay. Check your connection and try again.",
    );
  }
}
let csrf = "";
export function setAuth(auth: Auth) {
  csrf = auth.csrf_token;
}
export function clearAuth() {
  csrf = "";
}
export async function api<T>(
  path: string,
  body?: unknown,
  method?: string,
): Promise<T> {
  const verb = method || (body !== undefined ? "POST" : "GET");
  const response = await request(`/api${path}`, {
    method: verb,
    credentials: "include",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(verb !== "GET" ? { "X-CSRF-Token": csrf } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  if (
    response.status === 401 &&
    ![
      "/auth/me",
      "/auth/login",
      "/auth/register",
      "/auth/join",
      "/auth/demo",
    ].includes(path)
  )
    window.dispatchEvent(new Event("pantry-session-expired"));
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const message =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail
              .map(
                (x: { msg: string; loc: string[] }) =>
                  `${x.loc?.slice(1).join(" ")}: ${x.msg}`,
              )
              .join(". ")
          : `Request could not be completed (${response.status}).`;
    throw new ApiError(message, response.status);
  }
  try {
    return await response.json();
  } catch {
    throw new Error(
      "The server returned an unexpected response. Please try again.",
    );
  }
}
export async function downloadReport(path: string, filename: string) {
  const response = await request(`/api/reports/${path}.csv`, {
    credentials: "include",
  });
  if (response.status === 401)
    window.dispatchEvent(new Event("pantry-session-expired"));
  if (!response.ok)
    throw new Error("The report could not be downloaded. Please try again.");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
