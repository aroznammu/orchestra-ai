import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Security & Compliance",
  description:
    "Enterprise-grade security at every layer. Encryption at rest, tenant isolation, GDPR compliance, and full audit trails.",
  openGraph: {
    title: "Security & Compliance | OrchestraAI",
    description:
      "Enterprise-grade security at every layer. Encryption at rest, tenant isolation, GDPR compliance, and full audit trails.",
  },
};

export default function SecurityLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
