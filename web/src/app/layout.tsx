import type { Metadata } from "next";
import { Inter, Bricolage_Grotesque, JetBrains_Mono, Caveat } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import "./globals.css";
import { cn } from "@/lib/utils";
import { ThemeProvider } from "@/lib/theme";

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
          colorPrimary: "#E8765A",
          colorBackground: "#171514",
          colorInputBackground: "#0D0C0B",
          colorInputText: "#EFEAD9",
          colorText: "#EFEAD9",
          colorTextSecondary: "#A8A69A",
          colorNeutral: "#EFEAD9",
          colorDanger: "#F0788C",
          borderRadius: "10px",
        },
        elements: {
          card: "bg-[#171514] border border-[rgba(239,234,217,0.14)] shadow-2xl rounded-interactive text-[#EFEAD9] overflow-hidden",
          headerTitle: "text-[#EFEAD9] font-bold",
          headerSubtitle: "text-[#A8A69A]",
          footer: "bg-[#121110] border-t border-[rgba(239,234,217,0.10)] rounded-b-interactive text-[#EFEAD9]",
          footerAction: "bg-[#121110] text-[#EFEAD9]",
          footerActionText: "text-[#A8A69A] text-xs",
          footerActionLink: "text-accent-primary hover:underline text-xs font-semibold",
          footerPages: "bg-[#121110] text-[#EFEAD9]",
          footerPagesLink: "text-[#A8A69A] hover:text-[#EFEAD9] text-xs",
          lastAuthenticationStrategyBadge: "bg-[#201D1B] text-[#EFEAD9] border border-[rgba(239,234,217,0.14)] text-xs px-2 py-0.5 rounded-full shadow-none",
          socialButtonsBlockButton: "border border-[rgba(239,234,217,0.14)] bg-[#201D1B] hover:bg-[#2A2724] text-[#EFEAD9] text-xs h-10 transition-colors shadow-2xs",
          socialButtonsIconButton: "border border-[rgba(239,234,217,0.14)] bg-[#201D1B] hover:bg-[#2A2724] text-[#EFEAD9] transition-colors shadow-2xs",
          formButtonPrimary: "bg-accent-primary hover:opacity-90 text-white text-xs font-medium h-10 shadow-xs transition-opacity rounded-interactive",
          formFieldInput: "bg-[#0D0C0B] border border-[rgba(239,234,217,0.16)] text-[#EFEAD9] placeholder:text-[#A8A69A] text-xs rounded-interactive focus:border-accent-primary focus:ring-1 focus:ring-accent-primary",
          formFieldLabel: "text-xs text-[#EFEAD9] font-medium",
          identityPreviewText: "text-[#EFEAD9]",
          identityPreviewEditButton: "text-accent-primary",
          dividerLine: "bg-[rgba(239,234,217,0.12)]",
          dividerText: "text-[#A8A69A] text-xs font-mono",
          // UserProfile Account Section specific elements:
          rootBox: "text-[#EFEAD9]",
          modalBackdrop: "bg-black/80 backdrop-blur-sm",
          modalContent: "bg-[#171514] border border-[rgba(239,234,217,0.14)] rounded-2xl shadow-2xl overflow-hidden",
          modalCloseButton: "text-[#A8A69A] hover:text-[#EFEAD9] hover:bg-[#201D1B] rounded-lg transition-colors",
          navbar: "bg-[#121110] border-r border-[rgba(239,234,217,0.10)]",
          navbarButton: "text-[#A8A69A] hover:text-[#EFEAD9] hover:bg-[#201D1B] rounded-lg text-xs font-medium transition-colors",
          navbarButtonActive: "bg-[rgba(232,118,90,0.15)] text-[#E8765A] font-semibold rounded-lg",
          profileSection: "border-b border-[rgba(239,234,217,0.08)] py-4",
          profileSectionTitle: "text-[#EFEAD9] font-semibold text-sm",
          profileSectionTitleText: "text-[#EFEAD9] font-semibold text-sm",
          profileSectionContent: "text-[#EFEAD9] text-xs",
          profileSectionPrimaryButton: "text-[#E8765A] hover:underline font-medium text-xs",
          userButtonPopoverCard: "bg-[#171514] border border-[rgba(239,234,217,0.14)] shadow-2xl rounded-xl text-[#EFEAD9]",
          userButtonPopoverActions: "text-[#EFEAD9]",
          userButtonPopoverActionButton: "hover:bg-[#201D1B] text-[#EFEAD9] text-xs transition-colors",
          userButtonPopoverFooter: "bg-[#121110] border-t border-[rgba(239,234,217,0.10)] text-[#A8A69A]",
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
            {children}
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
