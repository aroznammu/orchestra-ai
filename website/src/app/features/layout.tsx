import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Features",
  description:
    "Eight powerful capabilities working in concert. AI orchestration, video generation, financial guardrails, cross-platform intelligence, and more.",
  openGraph: {
    title: "Features | OrchestraAI",
    description:
      "Eight powerful capabilities working in concert. AI orchestration, video generation, financial guardrails, cross-platform intelligence, and more.",
  },
};

export default function FeaturesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
