import type { ReactNode } from "react";

import { cx } from "../cx.js";
import { useT } from "../i18n.js";

export interface Column<T> {
  /** Stable id; also the default accessor when `cell` is omitted. */
  key: string;
  header: ReactNode;
  cell?: ((row: T) => ReactNode) | undefined;
  /** Numbers go right, in the mono face, per the design system. */
  align?: "left" | "right" | undefined;
  numeric?: boolean | undefined;
  width?: string | undefined;
}

export interface TableProps<T> {
  columns: ReadonlyArray<Column<T>>;
  rows: ReadonlyArray<T>;
  rowKey: (row: T) => string;
  caption?: ReactNode | undefined;
  /** Overrides the localized default (`ui.table.empty`). */
  empty?: ReactNode | undefined;
  /** Highlight a row (selected table on the floor, flagged line in Normativ). */
  rowTone?: ((row: T) => "default" | "accent" | "ok" | undefined) | undefined;
  dense?: boolean | undefined;
  className?: string | undefined;
}

const ROW_TONE = {
  default: "",
  accent: "bg-accent-tint",
  ok: "bg-green-tint",
} as const;

function defaultCell<T>(row: T, key: string): ReactNode {
  const value = (row as Record<string, unknown>)[key];
  switch (typeof value) {
    case "string":
    case "number":
      return value;
    case "boolean":
    case "bigint":
      return String(value);
    default:
      return null;
  }
}

/** Prototype `.table`: line-separated rows, numeric columns right-aligned in mono. */
export function Table<T>({
  columns,
  rows,
  rowKey,
  caption,
  empty,
  rowTone,
  dense = false,
  className,
}: TableProps<T>) {
  const t = useT();
  const cellPad = dense ? "px-3 py-2" : "px-3 py-3";

  return (
    <div className={cx("overflow-x-auto", className)}>
      <table className="w-full border-collapse font-sans text-sm text-ink">
        {caption !== undefined ? (
          <caption className="mb-2 text-left font-display text-base font-semibold">
            {caption}
          </caption>
        ) : null}
        <thead>
          <tr className="border-b-2 border-ink text-xs uppercase tracking-wide text-ink-2">
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                style={c.width !== undefined ? { width: c.width } : undefined}
                className={cx(
                  cellPad,
                  "font-semibold",
                  (c.align ?? (c.numeric ? "right" : "left")) === "right"
                    ? "text-right"
                    : "text-left",
                )}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={cx(cellPad, "text-center text-ink-2")}>
                {empty ?? t("ui.table.empty")}
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const tone = rowTone?.(row) ?? "default";
              return (
                <tr key={rowKey(row)} className={cx("border-b border-line", ROW_TONE[tone])}>
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      className={cx(
                        cellPad,
                        (c.align ?? (c.numeric ? "right" : "left")) === "right"
                          ? "text-right"
                          : "text-left",
                        c.numeric && "font-mono tabular-nums",
                      )}
                    >
                      {c.cell ? c.cell(row) : defaultCell(row, c.key)}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
