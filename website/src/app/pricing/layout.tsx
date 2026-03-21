import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Simple, transparent pricing. Starter at $99/month, Agency at $999/month, or self-host free with Apache 2.0.",
  openGraph: {
    title: "Pricing | OrchestraAI",
    description:
      "Simple, transparent pricing. Starter at $99/month, Agency at $999/month, or self-host free with Apache 2.0.",
  },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
