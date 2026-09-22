import { render, screen, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { Button } from "../src/components/Button.js";
import { Card } from "../src/components/Card.js";
import { Chip } from "../src/components/Chip.js";
import { Stepper } from "../src/components/Stepper.js";
import { Table, type Column } from "../src/components/Table.js";
import { Tabs } from "../src/components/Tabs.js";
import { UiLocaleProvider } from "../src/i18n.js";

describe("Button", () => {
  it("defaults to type=button and the 44 px touch class", () => {
    render(<Button>Naplati</Button>);
    const b = screen.getByRole("button", { name: "Naplati" });
    expect(b).toHaveAttribute("type", "button");
    expect(b.className).toContain("min-h-touch");
  });

  it("applies variant, size and block classes", () => {
    render(
      <Button variant="secondary" size="lg" block>
        X
      </Button>,
    );
    const b = screen.getByRole("button");
    expect(b.className).toContain("border-line-strong");
    expect(b.className).toContain("min-h-14");
    expect(b.className).toContain("w-full");
  });

  it("forwards native props", async () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} disabled>
        X
      </Button>,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe("Chip", () => {
  it("soft green uses the tint background and green text", () => {
    render(<Chip tone="green">ok</Chip>);
    const c = screen.getByText("ok");
    expect(c.className).toContain("bg-green-tint");
    expect(c.className).toContain("text-on-green-tint");
  });

  it("solid accent uses on-accent text", () => {
    render(
      <Chip tone="accent" emphasis="solid">
        kasni
      </Chip>,
    );
    expect(screen.getByText("kasni").className).toContain("text-on-accent");
  });
});

describe("Card", () => {
  it("renders title as a heading and the aside slot", () => {
    render(
      <Card title="Sto 7" aside={<Chip>otvoren</Chip>}>
        body
      </Card>,
    );
    expect(screen.getByRole("heading", { level: 3, name: "Sto 7" })).toBeInTheDocument();
    expect(screen.getByText("otvoren")).toBeInTheDocument();
    expect(screen.getByText("body")).toBeInTheDocument();
  });

  it("omits the header entirely without title/aside", () => {
    const { container } = render(<Card>body</Card>);
    expect(container.querySelector("header")).toBeNull();
  });
});

interface Row {
  id: string;
  name: string;
  qty: number;
}
const COLS: ReadonlyArray<Column<Row>> = [
  { key: "name", header: "Stavka" },
  { key: "qty", header: "Kol.", numeric: true },
];

describe("Table", () => {
  it("renders headers, rows and numeric cells right-aligned in mono", () => {
    render(
      <Table columns={COLS} rows={[{ id: "1", name: "Pivo", qty: 2 }]} rowKey={(r) => r.id} />,
    );
    expect(screen.getByRole("columnheader", { name: "Kol." })).toBeInTheDocument();
    const cell = screen.getByRole("cell", { name: "2" });
    expect(cell.className).toContain("text-right");
    expect(cell.className).toContain("font-mono");
  });

  it("empty state is sr-Latn by default and en under the provider", () => {
    const { rerender } = render(<Table columns={COLS} rows={[]} rowKey={(r) => r.id} />);
    expect(screen.getByText("Nema podataka")).toBeInTheDocument();
    rerender(
      <UiLocaleProvider value="en">
        <Table columns={COLS} rows={[]} rowKey={(r) => r.id} />
      </UiLocaleProvider>,
    );
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("row tone highlights a row", () => {
    render(
      <Table
        columns={COLS}
        rows={[{ id: "1", name: "Pivo", qty: 2 }]}
        rowKey={(r) => r.id}
        rowTone={() => "accent"}
      />,
    );
    const row = screen.getByRole("cell", { name: "Pivo" }).closest("tr");
    expect(row?.className).toContain("bg-accent-tint");
  });
});

function StepperHarness(props: { initial: number; min?: number; max?: number; step?: number }) {
  const [v, setV] = useState(props.initial);
  return (
    <Stepper
      value={v}
      onChange={setV}
      min={props.min}
      max={props.max}
      step={props.step}
      label="Pivo"
    />
  );
}

describe("Stepper", () => {
  it("has localized accessible names and 44 px buttons", () => {
    render(<StepperHarness initial={1} />);
    const inc = screen.getByRole("button", { name: "Dodaj jedan" });
    const dec = screen.getByRole("button", { name: "Oduzmi jedan" });
    expect(inc.className).toContain("size-touch");
    expect(dec.className).toContain("size-touch");
    expect(screen.getByRole("group", { name: "Pivo" })).toBeInTheDocument();
  });

  it("increments, decrements and clamps to bounds", async () => {
    render(<StepperHarness initial={1} min={0} max={2} />);
    const inc = screen.getByRole("button", { name: "Dodaj jedan" });
    const dec = screen.getByRole("button", { name: "Oduzmi jedan" });
    await userEvent.click(inc);
    expect(screen.getByRole("status")).toHaveTextContent("2");
    expect(inc).toBeDisabled();
    await userEvent.click(dec);
    await userEvent.click(dec);
    expect(screen.getByRole("status")).toHaveTextContent("0");
    expect(dec).toBeDisabled();
  });

  it("formats large values with Serbian grouping", () => {
    render(<StepperHarness initial={1250} max={9999} />);
    expect(screen.getByRole("status")).toHaveTextContent("1.250");
  });
});

function TabsHarness(props: { disabledId?: string }) {
  const [v, setV] = useState("a");
  return (
    <Tabs
      value={v}
      onChange={setV}
      items={[
        { id: "a", label: "A" },
        { id: "b", label: "B", disabled: props.disabledId === "b" },
        { id: "c", label: "C" },
      ]}
    />
  );
}

describe("Tabs", () => {
  it("exposes tablist/tab roles with a localized default name", () => {
    render(<TabsHarness />);
    const list = screen.getByRole("tablist", { name: "Sekcije" });
    expect(within(list).getAllByRole("tab")).toHaveLength(3);
    expect(screen.getByRole("tab", { name: "A" })).toHaveAttribute("aria-selected", "true");
  });

  it("moves with arrow keys, skipping disabled tabs, and wraps", async () => {
    render(<TabsHarness disabledId="b" />);
    const a = screen.getByRole("tab", { name: "A" });
    a.focus();
    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "C" })).toHaveAttribute("aria-selected", "true");
    await userEvent.keyboard("{ArrowRight}");
    expect(a).toHaveAttribute("aria-selected", "true");
    await userEvent.keyboard("{End}");
    expect(screen.getByRole("tab", { name: "C" })).toHaveAttribute("aria-selected", "true");
  });

  it("every tab is a 44 px touch target", () => {
    render(<TabsHarness />);
    for (const tab of screen.getAllByRole("tab")) expect(tab.className).toContain("min-h-touch");
  });
});
