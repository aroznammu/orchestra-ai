import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Demo",
  description:
    "See OrchestraAI in action. Watch how AI orchestrates campaigns across 9 ad platforms in a single natural-language request.",
  openGraph: {
    title: "Demo | OrchestraAI",
    description:
      "See OrchestraAI in action. Watch how AI orchestrates campaigns across 9 ad platforms in a single natural-language request.",
  },
};

export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
