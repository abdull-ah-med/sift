import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "sift",
  description: "Privacy-first document intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav>
          <Link href="/">sift</Link>
          <Link href="/login">Login</Link>
          <Link href="/tenants">Tenants</Link>
          <Link href="/collections">Collections</Link>
          <Link href="/settings/api-keys">API keys</Link>
          <Link href="/settings/audit">Audit</Link>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
