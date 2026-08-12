"use client";

import { useEffect, useState } from "react";
import { Input } from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type Event = {
  event_id: string;
  chain_index: number;
  action: string;
  actor: string;
  target_kind: string;
  target_id: string;
  occurred_at: string;
};

export default function AuditPage() {
  const [rows, setRows] = useState<Event[] | null>(null);
  const [filter, setFilter] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    void (async () => {
      const r = await apiFetch("/v1/audit/events");
      if (!r.ok) {
        setErr(await r.text());
        setRows([]);
        return;
      }
      setRows(await r.json());
    })();
  }, []);

  const shown = (rows || []).filter((e) =>
    filter ? e.action.includes(filter) || e.actor.includes(filter) : true,
  );

  return (
    <>
      <PageHeader title="Audit" description="Tamper-evident event chain (hashes only in UI)." />
      {err ? <ErrorBanner message={err} /> : null}
      <label className="mb-4 flex max-w-sm flex-col gap-1 text-sm">
        Filter
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="action or actor"
        />
      </label>
      {rows === null ? <LoadingState /> : null}
      {rows && shown.length === 0 ? (
        <EmptyState title="No events" body="Audit events appear as the product is used." />
      ) : null}
      {rows && shown.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Action</th>
              <th>Actor</th>
              <th>Target</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((e) => (
              <tr key={e.event_id}>
                <td>{e.chain_index}</td>
                <td>{e.action}</td>
                <td>{e.actor}</td>
                <td className="muted">
                  {e.target_kind}:{e.target_id}
                </td>
                <td className="muted">{e.occurred_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </>
  );
}
