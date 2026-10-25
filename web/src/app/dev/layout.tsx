import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Design System Showcase — Allcited",
  description: "Interactive tokens, components, and animations showcase.",
};

export default function DevLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
