import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Demo",
};

export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
