import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Product — Allcited",
  description: "Six architectural defenses against hallucination. Built with receipts on everything.",
};

export default function ProductLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
