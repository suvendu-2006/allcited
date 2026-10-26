import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { ArrowRight } from "lucide-react"

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center rounded-interactive text-sm font-medium transition-all duration-150 ease-out outline-none select-none active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-accent-primary motion-reduce:transform-none motion-reduce:transition-none",
  {
    variants: {
      variant: {
        default:
          "bg-accent-primary text-primary-foreground hover:brightness-95 hover:-translate-y-[1px] hover:shadow-sm active:translate-y-0 shadow-xs",
        primary:
          "bg-accent-primary text-primary-foreground hover:brightness-95 hover:-translate-y-[1px] hover:shadow-sm active:translate-y-0 shadow-xs",
        outline:
          "border border-border bg-bg-surface text-ink-primary hover:bg-bg-sunken hover:border-ink-primary/30 hover:-translate-y-[1px] hover:shadow-xs active:translate-y-0",
        secondary:
          "bg-bg-sunken text-ink-primary hover:bg-bg-surface hover:-translate-y-[1px] hover:shadow-xs active:translate-y-0 border border-border/60",
        ghost:
          "bg-transparent text-ink-primary hover:bg-bg-sunken hover:text-ink-primary active:scale-[0.97]",
        ferrari:
          "bg-transparent text-ink-primary uppercase tracking-widest text-xs font-semibold hover:text-accent-primary flex items-center gap-1.5 active:scale-[0.98]",
        destructive:
          "bg-danger/10 text-danger hover:bg-danger/20 hover:-translate-y-[1px] active:translate-y-0 border border-danger/20",
        link: "text-accent-primary underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-6 text-base",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  showArrow?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, showArrow = false, children, ...props }, ref) => {
    return (
      <button
        className={cn("group", buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      >
        {children}
        {(variant === "ferrari" || showArrow) && (
          <ArrowRight className="w-3.5 h-3.5 transition-transform duration-150 ease-out group-hover:translate-x-1" />
        )}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
