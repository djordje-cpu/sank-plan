import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "../src/components/Button.js";
import { Card } from "../src/components/Card.js";
import { Chip } from "../src/components/Chip.js";
import { formatRsd } from "../src/format.js";

const meta = {
  title: "Components/Card",
  component: Card,
  args: { title: "Sto 7", tone: "default", padding: "md", elevated: false },
  argTypes: {
    tone: { control: "radio", options: ["default", "ok", "night"] },
    padding: { control: "radio", options: ["md", "lg"] },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Basic: Story = {
  args: {
    children: <p className="m-0 text-sm text-ink-2">Dva piva, jedan ćevapi. Otvoren 14 minuta.</p>,
  },
};

export const WithAside: Story = {
  args: {
    aside: <Chip tone="green">Fiskalizovan</Chip>,
    children: (
      <div className="flex items-baseline justify-between">
        <span className="text-sm text-ink-2">Ukupno</span>
        <span className="font-display text-2xl font-semibold">{formatRsd(184000)}</span>
      </div>
    ),
  },
};

export const Ok: Story = {
  args: {
    tone: "ok",
    title: "Utrošak u granicama",
    children: <p className="m-0 text-sm">Teorijski 12,4 kg, stvarni 12,9 kg, kalo 4 %.</p>,
  },
};

export const Night: Story = {
  args: {
    tone: "night",
    elevated: true,
    title: "Račun uživo",
    children: (
      <>
        <p className="m-0 text-sm opacity-80">Vidljiv sve vreme dok se naručuje.</p>
        <Button block>Naplati {formatRsd(184000)}</Button>
      </>
    ),
  },
};

export const Elevated: Story = {
  args: { elevated: true, padding: "lg", children: <p className="m-0">Podignuta kartica.</p> },
};
