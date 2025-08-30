import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group relative inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all duration-300 disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-background overflow-hidden",
  {
    variants: {
      variant: {
        primary:
          "bg-transparent border border-white text-white hover:bg-white hover:text-black hover:scale-[1.02] hover:shadow-[0_8px_32px_-8px_rgba(255,255,255,0.3)] active:scale-[0.98]",
        secondary:
          "bg-gradient-to-r from-white/10 to-white/5 text-white border border-white/30 hover:from-white/20 hover:to-white/10 hover:border-white/50 hover:scale-[1.02] hover:shadow-[0_8px_32px_-8px_rgba(255,255,255,0.2)] active:scale-[0.98]",
        outline:
          "border border-white text-white bg-transparent hover:bg-white hover:text-black hover:scale-[1.02] hover:shadow-[0_8px_32px_-8px_rgba(255,255,255,0.15)] active:scale-[0.98]",
        ghost:
          "text-white hover:bg-white/10 hover:scale-[1.02] active:scale-[0.98]",
        luxury:
          "bg-[#F0EAD6] text-black border border-transparent hover:bg-transparent hover:text-[#F0EAD6] hover:border-[#F0EAD6] hover:scale-[1.02] hover:shadow-[0_8px_32px_-8px_rgba(240,234,214,0.4)] active:scale-[0.98]",
        link: 
          "text-white/60 hover:text-white underline-offset-4 hover:underline p-0 h-auto bg-transparent relative after:absolute after:bottom-0 after:left-0 after:h-[1px] after:w-0 after:bg-white after:transition-all after:duration-300 hover:after:w-full hover:no-underline",
        minimal:
          "text-white/80 hover:text-white hover:bg-white/5 active:scale-[0.98]",
      },
      size: {
        sm: "h-8 px-4 text-xs rounded-lg",
        default: "h-9 px-5 text-xs rounded-lg",
        lg: "h-10 px-7 text-sm rounded-lg",
        xl: "h-12 px-10 text-base rounded-xl",
        icon: "size-9 rounded-lg",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  children,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  if (asChild) {
    return (
      <Comp
        data-slot="button"
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      >
        {children}
      </Comp>
    )
  }

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    >
      {/* Shimmer effect for luxury buttons */}
      {variant === "luxury" && (
        <div className="absolute inset-0 -top-px overflow-hidden rounded-[inherit]">
          <div className="absolute inset-0 rounded-[inherit] bg-gradient-to-r from-transparent via-[#F0EAD6]/30 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-out" />
        </div>
      )}
      
      {/* Ripple effect background */}
      <div className="absolute inset-0 rounded-[inherit] bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      {/* Content */}
      <span className="relative z-10 flex items-center gap-2">
        {children}
      </span>
    </Comp>
  )
}

export { Button, buttonVariants }
