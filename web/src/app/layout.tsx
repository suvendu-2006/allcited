import type { Metadata } from "next";
import { Inter, Bricolage_Grotesque, JetBrains_Mono, Caveat } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
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
    <ClerkProvider
      appearance={{
        baseTheme: dark,
        variables: {
          colorBackground: "#171514",
          colorText: "#EFEAD9",
          colorTextSecondary: "#A8A69A",
          colorInputBackground: "#201D1B",
          colorInputText: "#EFEAD9",
          colorPrimary: "#E8765A",
          colorDanger: "#F0788C",
          borderRadius: "10px",
        },
        elements: {
          card: "bg-bg-surface border border-border shadow-md rounded-interactive text-ink-primary overflow-hidden",
          footer: "bg-bg-surface border-t border-border rounded-b-interactive text-ink-primary",
          footerAction: "bg-bg-surface text-ink-primary",
          footerActionText: "text-gray-warm text-xs",
          footerActionLink: "text-accent-primary hover:underline text-xs font-semibold",
          footerPages: "bg-bg-surface text-ink-primary",
          footerPagesLink: "text-gray-warm hover:text-ink-primary text-xs",
          lastAuthenticationStrategyBadge: "bg-bg-sunken text-accent-amber border border-border text-xs px-2 py-0.5 rounded-full shadow-none",
          socialButtonsBlockButton: "border border-border bg-bg-sunken hover:bg-bg-surface text-ink-primary text-xs h-10 transition-colors shadow-2xs",
          socialButtonsIconButton: "border border-border bg-bg-sunken hover:bg-bg-surface text-ink-primary transition-colors shadow-2xs",
          formButtonPrimary: "bg-accent-primary hover:opacity-90 text-white text-xs font-medium h-10 shadow-xs transition-opacity rounded-interactive",
          formFieldInput: "bg-bg-sunken border border-border text-ink-primary placeholder:text-gray-warm text-xs rounded-interactive focus:border-accent-primary focus:ring-1 focus:ring-accent-primary",
          formFieldLabel: "text-xs text-ink-primary font-medium",
          identityPreviewText: "text-ink-primary",
          identityPreviewEditButton: "text-accent-primary",
          dividerLine: "bg-border",
          dividerText: "text-ink-ghost text-xs font-mono",
        },
      }}
    >
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
