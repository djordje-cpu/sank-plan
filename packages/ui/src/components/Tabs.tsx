import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";

import { cx } from "../cx.js";
import { useT } from "../i18n.js";

export interface TabItem {
  id: string;
  label: ReactNode;
  /** Optional count/badge on the right of the label (open tables, tickets). */
  badge?: ReactNode | undefined;
  disabled?: boolean | undefined;
}

export interface TabsProps {
  items: ReadonlyArray<TabItem>;
  value: string;
  onChange: (id: string) => void;
  /** Accessible name of the tab list; defaults to the localized `ui.tabs.label`. */
  label?: string | undefined;
  /** underline = section navigation; segmented = filter/mode switch. */
  variant?: "underline" | "segmented" | undefined;
  /** Stretch tabs to fill the row (POS category bar). */
  fill?: boolean | undefined;
  className?: string | undefined;
}

/**
 * WAI-ARIA tabs with roving focus: ←/→ move, Home/End jump, activation on
 * focus. Every tab is a ≥44 px touch target (CLAUDE.md rule 8).
 */
export function Tabs({
  items,
  value,
  onChange,
  label,
  variant = "underline",
  fill = false,
  className,
}: TabsProps) {
  const t = useT();
  const baseId = useId();
  const listRef = useRef<HTMLDivElement>(null);

  const enabled = items.filter((i) => !i.disabled);

  const move = (from: string, delta: number) => {
    const idx = enabled.findIndex((i) => i.id === from);
    if (idx === -1 || enabled.length === 0) return;
    const next = enabled[(idx + delta + enabled.length) % enabled.length];
    if (next) activate(next.id);
  };

  const activate = (id: string) => {
    onChange(id);
    listRef.current?.querySelector<HTMLButtonElement>(`[data-tab-id="${id}"]`)?.focus();
  };

  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>, id: string) => {
    switch (e.key) {
      case "ArrowRight":
        e.preventDefault();
        move(id, 1);
        break;
      case "ArrowLeft":
        e.preventDefault();
        move(id, -1);
        break;
      case "Home":
        e.preventDefault();
        if (enabled[0]) activate(enabled[0].id);
        break;
      case "End": {
        e.preventDefault();
        const last = enabled[enabled.length - 1];
        if (last) activate(last.id);
        break;
      }
      default:
        break;
    }
  };

  const segmented = variant === "segmented";

  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label={label ?? t("ui.tabs.label")}
      className={cx(
        "flex font-sans",
        segmented
          ? "gap-1 rounded-sm border border-line bg-surface-2 p-1"
          : "gap-1 border-b border-line",
        className,
      )}
    >
      {items.map((item) => {
        const selected = item.id === value;
        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`${baseId}-tab-${item.id}`}
            data-tab-id={item.id}
            aria-selected={selected}
            aria-controls={`${baseId}-panel-${item.id}`}
            tabIndex={selected ? 0 : -1}
            disabled={item.disabled}
            onClick={() => onChange(item.id)}
            onKeyDown={(e) => onKeyDown(e, item.id)}
            className={cx(
              "inline-flex min-h-touch items-center justify-center gap-2 px-4 text-sm",
              "cursor-pointer select-none whitespace-nowrap",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
              "disabled:cursor-not-allowed disabled:opacity-40",
              fill && "flex-1",
              segmented
                ? cx(
                    "rounded-sm",
                    selected
                      ? "bg-surface text-ink font-semibold shadow-card"
                      : "text-ink-2 font-medium hover:text-ink",
                  )
                : cx(
                    "-mb-px border-b-2",
                    selected
                      ? "border-accent text-ink font-semibold"
                      : "border-transparent text-ink-2 font-medium hover:text-ink",
                  ),
            )}
          >
            {item.label}
            {item.badge !== undefined ? (
              <span className="font-mono text-xs tabular-nums text-ink-2">{item.badge}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

/** Pair with `Tabs`: panel ids match `aria-controls` when `baseId` is shared via `useId` in the parent. */
export interface TabPanelProps {
  id: string;
  active: boolean;
  children: ReactNode;
  className?: string | undefined;
}

export function TabPanel({ id, active, children, className }: TabPanelProps) {
  return (
    <div role="tabpanel" id={id} hidden={!active} className={className}>
      {children}
    </div>
  );
}
