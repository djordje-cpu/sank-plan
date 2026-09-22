import type { ComponentProps, ReactNode } from "react";

import { cx } from "../cx.js";

export type CardTone = "default" | "ok" | "night";

export interface CardProps extends Omit<ComponentProps<"section">, "className" | "title"> {
  /** Rendered in the display face (Fraunces) above the content. */
  title?: ReactNode | undefined;
  /** Right-aligned slot next to the title (chips, actions). */
  aside?: ReactNode | undefined;
  tone?: CardTone | undefined;
  padding?: "md" | "lg" | undefined;
  /** Lift with the token shadow (prototype hero cards). */
  elevated?: boolean | undefined;
  className?: string | undefined;
}

const TONE: Record<CardTone, string> = {
  default: "bg-surface border-line text-ink",
  ok: "bg-green-tint border-green/30 text-ink",
  night: "bg-night border-night-2 text-on-night",
};

/** Prototype `.card`: surface, 1 px line, 12 px radius, vertical gap. */
export function Card({
  title,
  aside,
  tone = "default",
  padding = "md",
  elevated = false,
  className,
  children,
  ...rest
}: CardProps) {
  return (
    <section
      className={cx(
        "flex flex-col gap-3.5 rounded-md border",
        padding === "lg" ? "p-6" : "p-4",
        elevated && "shadow-card",
        TONE[tone],
        className,
      )}
      {...rest}
    >
      {title !== undefined || aside !== undefined ? (
        <header className="flex items-baseline justify-between gap-3">
          {title !== undefined ? (
            <h3 className="m-0 font-display text-lg font-semibold leading-tight">{title}</h3>
          ) : (
            <span />
          )}
          {aside}
        </header>
      ) : null}
      {children}
    </section>
  );
}
