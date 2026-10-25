import type { Metadata } from "next";
import { Inter, Bricolage_Grotesque, JetBrains_Mono, Caveat } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import { cn } from "@/lib/utils";
import { ThemeProvider } from "@/lib/theme";
import { ThemeTransitionOverlay } from "@/components/ThemeTransitionOverlay";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

const caveat = Caveat({
  subsets: ["latin"],
  variable: "--font-handwriting",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Allcited — Answers, with receipts.",
  description: "Drop in any document. Ask real questions. Every claim stamped with the exact section it came from.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html
        lang="en"
        className={cn(
          "font-sans",
          inter.variable,
          bricolage.variable,
          jetbrainsMono.variable,
          caveat.variable
        )}
        suppressHydrationWarning
      >
        <body className="antialiased min-h-screen bg-bg-base text-ink-primary selection:bg-accent-primary/20 selection:text-ink-primary">
          <ThemeProvider>
            <ThemeTransitionOverlay />
            {children}
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
