import type { Metadata } from "next";
import { Inter, Cormorant_Garamond } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-serif",
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

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
        className={`${inter.variable} ${cormorant.variable} font-sans antialiased bg-background text-foreground selection:bg-primary/20 selection:text-primary`}
      >
        <div className="relative min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
