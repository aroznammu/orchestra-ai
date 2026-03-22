import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://www.useorchestra.dev"),
  title: {
    default: "OrchestraAI — AI-Native Marketing Orchestration",
    template: "%s | OrchestraAI",
  },
  description:
    "One AI layer for 9 ad platforms. Intent classification, compliance, content generation, AI video, and cross-platform publishing in a single natural-language request.",
  keywords: [
    "AI marketing",
    "marketing automation",
    "ad orchestration",
    "cross-platform marketing",
    "AI video generation",
    "marketing AI",
  ],
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "OrchestraAI",
    images: ["/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} noise-overlay min-h-screen bg-background font-sans text-zinc-50 antialiased`}
      >
        <Navbar />
        <main className="pt-16">{children}</main>
        <Footer />
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
