import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FAQ",
  description:
    "Everything you need to know about OrchestraAI. Frequently asked questions about features, pricing, security, and more.",
  openGraph: {
    title: "FAQ | OrchestraAI",
    description:
      "Everything you need to know about OrchestraAI. Frequently asked questions about features, pricing, security, and more.",
  },
};

export default function FAQLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
