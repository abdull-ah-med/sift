"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type Collection = { id: string; name: string; slug: string };
type Tenant = { id: string; name: string; slug: string };

/** Dashboard home — shadcn dashboard-01 stats + recent table, real list endpoints. */
export default function HomePage() {
  const [collections, setCollections] = useState<Collection[] | null>(null);
  const [tenants, setTenants] = useState<Tenant[] | null>(null);
  const [err, setErr] = useState("");

  async function load() {
    setErr("");
    const [cRes, tRes] = await Promise.all([
      apiFetch("/v1/collections"),
      apiFetch("/v1/tenants"),
    ]);
    if (!cRes.ok) {
      setErr("Collections could not be loaded. Check that you are signed in and retry.");
      setCollections([]);
    } else {
      setCollections(await cRes.json());
    }
    if (!tRes.ok) {
      setTenants([]);
    } else {
      setTenants(await tRes.json());
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const loading = collections === null;
  const recent = (collections || []).slice(0, 8);

  return (
    <>
      <PageHeader
        title="Home"
        description="Workspace overview from live collection and tenant lists."
        actions={
          <Button size="sm" asChild>
            <Link href="/collections">New collection</Link>
          </Button>
        }
      />
      {err ? <ErrorBanner message={err} onRetry={() => void load()} /> : null}
      {loading ? <LoadingState /> : null}
      {!loading ? (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader>
                <CardDescription>Collections</CardDescription>
                <CardTitle className="font-mono tabular-nums text-2xl">
                  {collections?.length ?? 0}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Tenants</CardDescription>
                <CardTitle className="font-mono tabular-nums text-2xl">
                  {tenants?.length ?? 0}
                </CardTitle>
              </CardHeader>
            </Card>
          </div>
          {recent.length === 0 ? (
            <EmptyState
              title="No collections yet"
              body="Create a collection to upload documents and start review."
              action={
                <Button asChild>
                  <Link href="/collections">Create a collection</Link>
                </Button>
              }
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Recent collections</CardTitle>
                <CardDescription>Open a collection to upload, search, or chat.</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Slug</TableHead>
                      <TableHead />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recent.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell>{c.name}</TableCell>
                        <TableCell className="font-mono text-[rgb(var(--sift-text-muted))]">
                          {c.slug}
                        </TableCell>
                        <TableCell>
                          <Link
                            href={`/collections/${encodeURIComponent(c.slug)}?id=${c.id}`}
                            className="text-sm"
                          >
                            Open
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      ) : null}
    </>
  );
}
