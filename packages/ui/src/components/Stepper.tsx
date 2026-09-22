import { cx } from "../cx.js";
import { formatInt } from "../format.js";
import { useT } from "../i18n.js";

export interface StepperProps {
  value: number;
  onChange: (next: number) => void;
  min?: number | undefined;
  max?: number | undefined;
  step?: number | undefined;
  disabled?: boolean | undefined;
  /** Accessible name for the whole control, e.g. the line item's name. */
  label?: string | undefined;
  className?: string | undefined;
}

function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n));
}

/**
 * Prototype `.stepper`: [−] mono value [+]. Buttons lifted from 34 px to the
 * 44 px touch minimum (CLAUDE.md rule 8). Integer-only, clamped to bounds.
 */
export function Stepper({
  value,
  onChange,
  min = 0,
  max = Number.MAX_SAFE_INTEGER,
  step = 1,
  disabled = false,
  label,
  className,
}: StepperProps) {
  const t = useT();
  const canDec = !disabled && value - step >= min;
  const canInc = !disabled && value + step <= max;
  const set = (next: number) => onChange(clamp(next, min, max));

  const btn =
    "grid size-touch place-items-center rounded-sm border border-line bg-surface-2 text-ink " +
    "text-lg leading-none cursor-pointer select-none " +
    "hover:bg-line active:bg-line-strong/40 " +
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent " +
    "disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <div
      role="group"
      aria-label={label}
      className={cx("inline-flex items-center gap-2.5 font-sans", className)}
    >
      <button
        type="button"
        className={btn}
        aria-label={t("ui.stepper.decrement")}
        disabled={!canDec}
        onClick={() => set(value - step)}
      >
        −
      </button>
      <output
        aria-live="polite"
        className="min-w-[2ch] text-center font-mono text-base tabular-nums text-ink"
      >
        {formatInt(value)}
      </output>
      <button
        type="button"
        className={btn}
        aria-label={t("ui.stepper.increment")}
        disabled={!canInc}
        onClick={() => set(value + step)}
      >
        +
      </button>
    </div>
  );
}
