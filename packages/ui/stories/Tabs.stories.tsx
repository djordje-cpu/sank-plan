import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";

import { TabPanel, Tabs, type TabsProps } from "../src/components/Tabs.js";

const ITEMS = [
  { id: "sala", label: "Sala", badge: 12 },
  { id: "basta", label: "Bašta", badge: 4 },
  { id: "sank", label: "Šank" },
  { id: "poneti", label: "Za poneti", disabled: true },
];

function Controlled(props: Omit<TabsProps, "value" | "onChange"> & { initial?: string }) {
  const { initial = "sala", ...rest } = props;
  const [value, setValue] = useState(initial);
  return (
    <div className="flex flex-col gap-4">
      <Tabs {...rest} value={value} onChange={setValue} />
      {rest.items.map((item) => (
        <TabPanel key={item.id} id={`panel-${item.id}`} active={item.id === value}>
          <p className="m-0 text-sm text-ink-2">Sadržaj: {item.label}</p>
        </TabPanel>
      ))}
    </div>
  );
}

const meta = {
  title: "Components/Tabs",
  component: Tabs,
  args: {
    items: ITEMS,
    value: "sala",
    onChange: () => undefined,
    variant: "underline",
    fill: false,
  },
  argTypes: { variant: { control: "radio", options: ["underline", "segmented"] } },
  render: (args) => <Controlled {...args} initial={args.value} />,
} satisfies Meta<typeof Tabs>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Underline: Story = {};
export const Segmented: Story = { args: { variant: "segmented" } };
export const Fill: Story = { args: { fill: true } };
export const SegmentedFill: Story = { args: { variant: "segmented", fill: true } };
