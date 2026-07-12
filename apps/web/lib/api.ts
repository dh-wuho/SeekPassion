export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// No auth system yet (out of scope for this vertical slice) — a fixed demo
// user id is used until real auth lands. Must match apps/api's seed.py.
export const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

export type Company = {
  id: string;
  name: string;
  career_url: string;
  ats_type: string | null;
  monitoring_status: "active" | "paused";
  last_crawl_at: string | null;
  subscribed: boolean;
};

export async function fetchCompanies(userId: string): Promise<Company[]> {
  const res = await fetch(`${API_BASE_URL}/companies?user_id=${userId}`);
  if (!res.ok) throw new Error("Failed to fetch companies");
  return res.json();
}

export async function subscribe(userId: string, companyId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/users/${userId}/subscriptions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company_id: companyId }),
  });
  if (!res.ok && res.status !== 409) throw new Error("Failed to subscribe");
}

export async function unsubscribe(userId: string, companyId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/users/${userId}/subscriptions/${companyId}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 404) throw new Error("Failed to unsubscribe");
}
