import type { Meta, StoryObj } from "@storybook/react-vite";

import { Chip } from "../src/components/Chip.js";
import { Table, type Column } from "../src/components/Table.js";
import { formatPara, formatPercentBp } from "../src/format.js";
import { UiLocaleProvider } from "../src/i18n.js";

interface Line {
  id: string;
  name: string;
  qty: number;
  pricePara: number;
  foodCostBp: number;
  status: "ok" | "watch";
}

const LINES: ReadonlyArray<Line> = [
  { id: "1", name: "Pivo točeno 0,5", qty: 2, pricePara: 32000, foodCostBp: 2800, status: "ok" },
  { id: "2", name: "Ćevapi 10 kom", qty: 1, pricePara: 89000, foodCostBp: 3650, status: "watch" },
  { id: "3", name: "Šopska salata", qty: 1, pricePara: 45000, foodCostBp: 2400, status: "ok" },
];

const COLUMNS: ReadonlyArray<Column<Line>> = [
  { key: "name", header: "Stavka" },
  { key: "qty", header: "Kol.", numeric: true, width: "4rem" },
  { key: "price", header: "Cena", numeric: true, cell: (r) => formatPara(r.pricePara) },
  { key: "total", header: "Ukupno", numeric: true, cell: (r) => formatPara(r.pricePara * r.qty) },
  { key: "fc", header: "Food cost", numeric: true, cell: (r) => formatPercentBp(r.foodCostBp) },
  {
    key: "status",
    header: "Status",
    cell: (r) =>
      r.status === "ok" ? <Chip tone="green">u normi</Chip> : <Chip tone="ochre">prati</Chip>,
  },
];

const meta = {
  title: "Components/Table",
  component: Table<Line>,
  args: { columns: COLUMNS, rows: LINES, rowKey: (r: Line) => r.id, dense: false },
} satisfies Meta<typeof Table<Line>>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Basic: Story = {};
export const Dense: Story = { args: { dense: true } };
export const WithCaption: Story = { args: { caption: "Sto 7 — račun uživo" } };
export const HighlightedRow: Story = {
  args: { rowTone: (r: Line) => (r.status === "watch" ? "accent" : undefined) },
};
export const EmptySrLatn: Story = { args: { rows: [] } };
export const EmptyEn: Story = {
  args: { rows: [] },
  render: (args) => (
    <UiLocaleProvider value="en">
      <Table {...args} />
    </UiLocaleProvider>
  ),
};
