import type { ComponentProps } from "react";

import { cx } from "../cx.js";

export type ChipTone = "neutral" | "accent" | "green" | "ochre" | "blue" | "purple";
export type ChipEmphasis = "soft" | "solid";

export interface ChipProps extends Omit<ComponentProps<"span">, "className"> {
  tone?: ChipTone | undefined;
  /** soft = tint background (prototype `.chip.ok`), solid = filled (prototype `.chip.urgent`). */
  emphasis?: ChipEmphasis | undefined;
  className?: string | undefined;
}

const SOFT: Record<ChipTone, string> = {
  neutral: "bg-surface-2 text-ink-2 border-line",
  accent: "bg-accent-tint text-on-accent-tint border-transparent",
  green: "bg-green-tint text-on-green-tint border-transparent",
  ochre: "bg-ochre-tint text-on-ochre-tint border-transparent",
  blue: "bg-blue-tint text-on-blue-tint border-transparent",
  purple: "bg-purple-tint text-on-purple-tint border-transparent",
};

const SOLID: Record<ChipTone, string> = {
  neutral: "bg-ink text-paper border-transparent",
  accent: "bg-accent text-on-accent border-transparent",
  green: "bg-green text-on-accent border-transparent",
  ochre: "bg-ochre text-on-accent border-transparent",
  blue: "bg-blue text-on-accent border-transparent",
  purple: "bg-purple text-on-accent border-transparent",
};

/** Prototype `.chip`: 24 px, pill, 12 px semibold, one tone per meaning. */
export function Chip({ tone = "neutral", emphasis = "soft", className, ...rest }: ChipProps) {
  return (
    <span
      className={cx(
        "inline-flex h-chip items-center rounded-pill border px-2.5 text-xs font-semibold",
        "whitespace-nowrap font-sans",
        emphasis === "solid" ? SOLID[tone] : SOFT[tone],
        className,
      )}
      {...rest}
    />
  );
}
