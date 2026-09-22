import type { ComponentProps } from "react";

import { cx } from "../cx.js";

export type ButtonVariant = "primary" | "secondary" | "ghost";
export type ButtonSize = "md" | "lg";

export interface ButtonProps extends Omit<ComponentProps<"button">, "className"> {
  variant?: ButtonVariant | undefined;
  /** md = 44 px (rule 8 minimum), lg = 56 px for the beer path on tablets. */
  size?: ButtonSize | undefined;
  /** Stretch to the container width. */
  block?: boolean | undefined;
  className?: string | undefined;
}

const VARIANT: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-on-accent border border-transparent font-semibold " +
    "hover:brightness-95 active:brightness-90",
  secondary:
    "bg-surface text-ink border border-line-strong font-medium " +
    "hover:bg-surface-2 active:bg-line",
  ghost:
    "bg-transparent text-ink border border-transparent font-medium " +
    "hover:bg-surface-2 active:bg-line",
};

const SIZE: Record<ButtonSize, string> = {
  md: "min-h-touch px-4 text-sm",
  lg: "min-h-14 px-5 text-base",
};

/** Prototype `.btn` / `.btn.primary`, lifted from 42 px to the 44 px touch minimum. */
export function Button({
  variant = "primary",
  size = "md",
  block = false,
  className,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-sm font-sans",
        "cursor-pointer select-none whitespace-nowrap transition-[filter,background-color]",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        "disabled:cursor-not-allowed disabled:opacity-50",
        VARIANT[variant],
        SIZE[size],
        block && "w-full",
        className,
      )}
      {...rest}
    />
  );
}
