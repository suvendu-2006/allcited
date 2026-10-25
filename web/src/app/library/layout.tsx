import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Library — Allcited",
  description: "Your document library and cited passage archive.",
};

export default function LibraryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
