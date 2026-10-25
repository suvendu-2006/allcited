import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The exam — Allcited",
  description: "Our 46-question release exam. Public scores, per-release regression tracking, and failure receipts.",
};

export default function ExamLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
