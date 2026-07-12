"use client";

import { useEffect, useState } from "react";
import { Company, DEMO_USER_ID, fetchCompanies, subscribe, unsubscribe } from "@/lib/api";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [refreshIndex, setRefreshIndex] = useState(0);

  useEffect(() => {
    let ignore = false;

    fetchCompanies(DEMO_USER_ID)
      .then((data) => {
        if (ignore) return;
        setCompanies(data);
        setError(null);
      })
      .catch(() => {
        if (!ignore) setError("Could not load companies. Is the API running?");
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [refreshIndex]);

  async function toggleSubscription(company: Company) {
    setPendingId(company.id);
    try {
      if (company.subscribed) {
        await unsubscribe(DEMO_USER_ID, company.id);
      } else {
        await subscribe(DEMO_USER_ID, company.id);
      }
      setRefreshIndex((i) => i + 1);
    } finally {
      setPendingId(null);
    }
  }

  if (loading) {
    return (
      <main>
        <p>Loading companies…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <p>{error}</p>
      </main>
    );
  }

  return (
    <main>
      <h1>Companies</h1>
      <p>Browse the catalog and subscribe to companies you want monitored.</p>
      <ul>
        {companies.map((company) => (
          <li key={company.id}>
            <span>{company.name}</span>{" "}
            <button onClick={() => toggleSubscription(company)} disabled={pendingId === company.id}>
              {company.subscribed ? "Unsubscribe" : "Subscribe"}
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
