import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "sift",
  description: "Privacy-first document intelligence",
};

/** Root chrome only — marketing pages own SiteHeader; app shell lands in p4-8. */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[rgb(var(--sift-bg))] font-sans text-[rgb(var(--sift-text))] antialiased">
        {children}
      </body>
    </html>
  );
}
