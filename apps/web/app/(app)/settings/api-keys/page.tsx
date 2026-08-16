"use client";

import { FormEvent, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Input,
  Label,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { formatApiError } from "@/lib/ui-error";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type KeyRow = {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  revoked_at: string | null;
};

export default function ApiKeysPage() {
  const [rows, setRows] = useState<KeyRow[] | null>(null);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState("documents:read,documents:write,search,chat");
  const [created, setCreated] = useState("");
  const [open, setOpen] = useState(false);
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/api-keys");
    if (!r.ok) {
      setErr(formatApiError(r.status, "API keys could not be loaded"));
      setRows([]);
      return;
    }
    setErr("");
    setRows(await r.json());
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setCreated("");
    const r = await apiFetch("/v1/api-keys", {
      method: "POST",
      body: JSON.stringify({
        name,
        scopes: scopes.split(",").map((s) => s.trim()).filter(Boolean),
      }),
    });
    if (!r.ok) {
      setErr(formatApiError(r.status, "API key was not created"));
      return;
    }
    const body = await r.json();
    setCreated(body.raw_key);
    setName("");
    setOpen(false);
    toast.success("API key created. Copy it now; it is shown once.");
    await load();
  }

  return (
    <>
      <PageHeader
        title="API keys"
        description="Machine credentials for CLI and local bootstrap."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button size="sm">Create key</Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={onCreate}>
                <DialogHeader>
                  <DialogTitle>Create API key</DialogTitle>
                  <DialogDescription>The raw secret is shown once after create.</DialogDescription>
                </DialogHeader>
                <div className="mt-4 grid gap-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="key-name">Name</Label>
                    <Input id="key-name" value={name} onChange={(e) => setName(e.target.value)} required />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="key-scopes">Scopes (comma-separated)</Label>
                    <Input id="key-scopes" value={scopes} onChange={(e) => setScopes(e.target.value)} />
                  </div>
                </div>
                <DialogFooter className="mt-6">
                  <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">Create key</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />
      {err ? <ErrorBanner message={err} onRetry={() => void load()} /> : null}
      {created ? (
        <p className="mb-4 rounded-md border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] px-3 py-2 text-sm">
          Raw key (shown once): <code className="font-mono">{created}</code>
        </p>
      ) : null}
      {rows === null ? <LoadingState /> : null}
      {rows && rows.length === 0 ? (
        <EmptyState title="No API keys" body="Create a key for CLI access." />
      ) : null}
      {rows && rows.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Prefix</TableHead>
              <TableHead>Scopes</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((k) => (
              <TableRow key={k.id}>
                <TableCell>{k.name}</TableCell>
                <TableCell className="font-mono">{k.prefix}</TableCell>
                <TableCell className="text-[rgb(var(--sift-text-muted))]">{k.scopes.join(", ")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </>
  );
}
