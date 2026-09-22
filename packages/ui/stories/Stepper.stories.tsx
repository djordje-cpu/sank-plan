import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";

import { Stepper, type StepperProps } from "../src/components/Stepper.js";

function Controlled(props: Omit<StepperProps, "value" | "onChange"> & { initial?: number }) {
  const { initial = 2, ...rest } = props;
  const [value, setValue] = useState(initial);
  return <Stepper {...rest} value={value} onChange={setValue} />;
}

const meta = {
  title: "Components/Stepper",
  component: Stepper,
  args: {
    value: 2,
    onChange: () => undefined,
    min: 0,
    max: 99,
    step: 1,
    disabled: false,
    label: "Pivo točeno 0,5",
  },
  render: (args) => <Controlled {...args} initial={args.value} />,
} satisfies Meta<typeof Stepper>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Basic: Story = {};
export const AtMinimum: Story = { args: { value: 0 } };
export const AtMaximum: Story = { args: { value: 99 } };
export const StepOfSix: Story = {
  args: { value: 6, step: 6, max: 60, label: "Ćevapi (porcija 6)" },
};
export const Disabled: Story = { args: { disabled: true } };
export const LargeValue: Story = { args: { value: 1250, max: 9999 } };
