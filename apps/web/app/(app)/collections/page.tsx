"use client";

import Link from "next/link";
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

type Collection = {
  id: string;
  name: string;
  slug: string;
};

export default function CollectionsPage() {
  const [rows, setRows] = useState<Collection[] | null>(null);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [open, setOpen] = useState(false);
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/collections");
    if (!r.ok) {
      setErr(formatApiError(r.status, "Collections could not be loaded"));
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
    const r = await apiFetch("/v1/collections", {
      method: "POST",
      body: JSON.stringify({ name, slug }),
    });
    if (!r.ok) {
      setErr(formatApiError(r.status, "Collection was not created"));
      return;
    }
    setName("");
    setSlug("");
    setOpen(false);
    toast.success("Collection created");
    await load();
  }

  return (
    <>
      <PageHeader
        title="Collections"
        description="Create and open document collections."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button size="sm">Create</Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={onCreate}>
                <DialogHeader>
                  <DialogTitle>Create collection</DialogTitle>
                  <DialogDescription>Name and slug are unique in this tenant.</DialogDescription>
                </DialogHeader>
                <div className="mt-4 grid gap-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="col-name">Name</Label>
                    <Input id="col-name" value={name} onChange={(e) => setName(e.target.value)} required />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="col-slug">Slug</Label>
                    <Input id="col-slug" value={slug} onChange={(e) => setSlug(e.target.value)} required />
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
        <EmptyState
          title="No collections yet"
          body="Create a collection to upload documents."
          action={
            <Button size="sm" onClick={() => setOpen(true)}>
              Create a collection
            </Button>
          }
        />
      ) : null}
      {rows && rows.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Slug</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((c) => (
              <TableRow key={c.id}>
                <TableCell>{c.name}</TableCell>
                <TableCell className="font-mono text-[rgb(var(--sift-text-muted))]">{c.slug}</TableCell>
                <TableCell>
                  <Link href={`/collections/${encodeURIComponent(c.slug)}?id=${c.id}`}>Open</Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </>
  );
}
