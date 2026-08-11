"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

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
  const [rows, setRows] = useState<Event[]>([]);
  const [filter, setFilter] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    void (async () => {
      const r = await apiFetch("/v1/audit/events");
      if (!r.ok) {
        setErr(await r.text());
        return;
      }
      setRows(await r.json());
    })();
  }, []);

  const shown = rows.filter((e) =>
    filter ? e.action.includes(filter) || e.actor.includes(filter) : true,
  );

  return (
    <>
      <h1>Audit</h1>
      {err ? <p className="err">{err}</p> : null}
      <label>
        Filter
        <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="action or actor" />
      </label>
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
    </>
  );
}
