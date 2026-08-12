import type { Metadata } from "next";
import { Toaster } from "@sift/ui";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "sift",
    template: "%s · sift",
  },
  description: "Privacy-first document intelligence",
};

/** Root chrome — skip link, toaster, dark canvas. */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[rgb(var(--sift-bg))] font-sans text-[rgb(var(--sift-text))] antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-[rgb(var(--sift-surface))] focus:px-3 focus:py-2 focus:text-sm"
        >
          Skip to content
        </a>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
