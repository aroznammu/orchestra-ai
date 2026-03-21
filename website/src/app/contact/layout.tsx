import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Get in touch with the OrchestraAI team. Email support, live chat, or GitHub issues.",
  openGraph: {
    title: "Contact | OrchestraAI",
    description:
      "Get in touch with the OrchestraAI team. Email support, live chat, or GitHub issues.",
  },
};

export default function ContactLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
