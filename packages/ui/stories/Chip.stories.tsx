import type { Meta, StoryObj } from "@storybook/react-vite";

import { Chip, type ChipTone } from "../src/components/Chip.js";

const TONES: ReadonlyArray<ChipTone> = ["neutral", "accent", "green", "ochre", "blue", "purple"];

const meta = {
  title: "Components/Chip",
  component: Chip,
  args: { children: "Otvoren", tone: "neutral", emphasis: "soft" },
  argTypes: {
    tone: { control: "radio", options: TONES },
    emphasis: { control: "radio", options: ["soft", "solid"] },
  },
} satisfies Meta<typeof Chip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Neutral: Story = {};
export const Ok: Story = { args: { tone: "green", children: "Fiskalizovan" } };
export const Urgent: Story = {
  args: { tone: "accent", emphasis: "solid", children: "Kasni 12 min" },
};
export const Info: Story = { args: { tone: "blue", children: "Radni konj" } };
export const Note: Story = { args: { tone: "ochre", children: "Demo podaci" } };

export const AllTones: Story = {
  render: () => (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {TONES.map((tone) => (
          <Chip key={tone} tone={tone}>
            {tone}
          </Chip>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {TONES.map((tone) => (
          <Chip key={tone} tone={tone} emphasis="solid">
            {tone}
          </Chip>
        ))}
      </div>
    </div>
  ),
};
