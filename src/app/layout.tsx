import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Abdullah Ahmed - Digital Craftsman & Design Architect",
  description: "Crafting sophisticated digital experiences with timeless elegance. A portfolio showcasing the intersection of classical aesthetics and modern innovation.",
  keywords: ["Abdullah Ahmed", "frontend developer", "UI/UX designer", "digital craftsman", "sophisticated design", "elegant websites", "luxury digital experiences"],
  authors: [{ name: "Abdullah Ahmed" }],
  creator: "Abdullah Ahmed",
  metadataBase: new URL("https://abdull-ah-med.xyz"),
  openGraph: {
    type: "website",
    locale: "en_US",
    title: "Abdullah Ahmed - Digital Craftsman & Design Architect",
    description: "Crafting sophisticated digital experiences with timeless elegance. A portfolio showcasing the intersection of classical aesthetics and modern innovation.",
    siteName: "Abdullah Ahmed Portfolio",
  },
  twitter: {
    card: "summary_large_image",
    title: "Abdullah Ahmed - Digital Craftsman & Design Architect",
    description: "Crafting sophisticated digital experiences with timeless elegance.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className="font-sans antialiased bg-background text-foreground selection:bg-primary/20 selection:text-primary"
      >
        <div className="relative min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
