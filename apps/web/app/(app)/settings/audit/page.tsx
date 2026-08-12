"use client";

import { useEffect, useState } from "react";
import { Input, Label, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { formatApiError } from "@/lib/ui-error";
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
        setErr(formatApiError(r.status, "Audit events could not be loaded"));
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
      <div className="mb-4 flex max-w-sm flex-col gap-1.5">
        <Label htmlFor="audit-filter">Filter</Label>
        <Input
          id="audit-filter"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="action or actor"
        />
      </div>
      {rows === null ? <LoadingState /> : null}
      {rows && shown.length === 0 ? (
        <EmptyState
          title={filter ? `No results for ${filter}` : "No events"}
          body={filter ? "Clear the filter to see the full chain." : "Audit events appear as the product is used."}
        />
      ) : null}
      {rows && shown.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>#</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>When</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {shown.map((e) => (
              <TableRow key={e.event_id}>
                <TableCell className="font-mono tabular-nums">{e.chain_index}</TableCell>
                <TableCell>{e.action}</TableCell>
                <TableCell>{e.actor}</TableCell>
                <TableCell className="font-mono text-[rgb(var(--sift-text-muted))]">
                  {e.target_kind}:{e.target_id}
                </TableCell>
                <TableCell className="text-[rgb(var(--sift-text-muted))]">{e.occurred_at}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </>
  );
}
