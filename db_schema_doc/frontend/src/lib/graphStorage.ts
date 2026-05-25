import type { GraphPayload } from "../types/graph";

const STORAGE_KEY = "django-db-schema-doc:graph-session";

export type GraphSession = {
  payload: GraphPayload;
  sourceLabel: string;
};

export function saveGraphSession(payload: GraphPayload, sourceLabel: string): void {
  const session: GraphSession = { payload, sourceLabel };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function loadGraphSession(): GraphSession | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as GraphSession;
    if (!session?.payload?.nodes?.length) return null;
    return session;
  } catch {
    return null;
  }
}

export function clearGraphSession(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
