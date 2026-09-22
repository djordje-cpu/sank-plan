import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  framework: { name: "@storybook/react-vite", options: {} },
  stories: ["../stories/**/*.stories.@(ts|tsx)"],
  addons: ["@storybook/addon-themes"],
  // vite.config.ts (react + tailwind plugins) is picked up automatically.
};

export default config;
