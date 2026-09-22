import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "../src/components/Button.js";

const meta = {
  title: "Components/Button",
  component: Button,
  args: { children: "Naplati", variant: "primary", size: "md", block: false, disabled: false },
  argTypes: {
    variant: { control: "radio", options: ["primary", "secondary", "ghost"] },
    size: { control: "radio", options: ["md", "lg"] },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};
export const Secondary: Story = { args: { variant: "secondary", children: "Prebaci sto" } };
export const Ghost: Story = { args: { variant: "ghost", children: "Otkaži" } };
export const Large: Story = { args: { size: "lg", children: "+ Pivo 0,5" } };
export const Block: Story = { args: { block: true, children: "Fiskalizuj i štampaj" } };
export const Disabled: Story = { args: { disabled: true, children: "L-PFR nedostupan" } };

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      <Button>Naplati</Button>
      <Button variant="secondary">Prebaci sto</Button>
      <Button variant="ghost">Otkaži</Button>
      <Button size="lg">+ Pivo 0,5</Button>
      <Button disabled>L-PFR nedostupan</Button>
    </div>
  ),
};
