import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen bg-zinc-950 font-sans text-zinc-50 antialiased`}
      >
        <Navbar />
        <main className="pt-16">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
