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

type Tenant = {
  id: string;
  name: string;
  slug: string;
};

export default function TenantsPage() {
  const [rows, setRows] = useState<Tenant[] | null>(null);
  const [orgId, setOrgId] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [open, setOpen] = useState(false);
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/tenants");
    if (!r.ok) {
      setErr(formatApiError(r.status, "Tenants could not be loaded"));
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
    const r = await apiFetch("/v1/tenants", {
      method: "POST",
      body: JSON.stringify({ organization_id: orgId, name, slug }),
    });
    if (!r.ok) {
      setErr(formatApiError(r.status, "Tenant was not created"));
      return;
    }
    setName("");
    setSlug("");
    setOpen(false);
    toast.success("Tenant created");
    await load();
  }

  return (
    <>
      <PageHeader
        title="Tenants"
        description="Workspace tenants for isolation."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button size="sm">Create</Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={onCreate}>
                <DialogHeader>
                  <DialogTitle>Create tenant</DialogTitle>
                  <DialogDescription>Organization id comes from Zitadel.</DialogDescription>
                </DialogHeader>
                <div className="mt-4 grid gap-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="org-id">Organization id</Label>
                    <Input id="org-id" value={orgId} onChange={(e) => setOrgId(e.target.value)} required />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="tenant-name">Name</Label>
                    <Input id="tenant-name" value={name} onChange={(e) => setName(e.target.value)} required />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="tenant-slug">Slug</Label>
                    <Input id="tenant-slug" value={slug} onChange={(e) => setSlug(e.target.value)} required />
                  </div>
                </div>
                <DialogFooter className="mt-6">
                  <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">Create</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />
      {err ? <ErrorBanner message={err} onRetry={() => void load()} /> : null}
      {rows === null ? <LoadingState /> : null}
      {rows && rows.length === 0 ? (
        <EmptyState title="No tenants" body="Create a tenant to start isolating workspaces." />
      ) : null}
      {rows && rows.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Slug</TableHead>
              <TableHead>Id</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((t) => (
              <TableRow key={t.id}>
                <TableCell>{t.name}</TableCell>
                <TableCell className="font-mono text-[rgb(var(--sift-text-muted))]">{t.slug}</TableCell>
                <TableCell className="font-mono text-[rgb(var(--sift-text-muted))]">{t.id}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </>
  );
}
