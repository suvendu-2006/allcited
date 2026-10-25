import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing — Allcited",
  description: "Transparent, predictable pricing. Self-host free or cloud scale.",
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
