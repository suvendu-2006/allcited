import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How it works — Allcited",
  description: "Three-step verification pipeline from document ingestion to cited answers.",
};

export default function HowItWorksLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
