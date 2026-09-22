import { withThemeByDataAttribute } from "@storybook/addon-themes";
import type { Preview } from "@storybook/react-vite";

import "../src/styles/theme.css";

// Light/dark via <html data-theme="…">, the same mechanism tokens.css uses in apps.
const preview: Preview = {
  decorators: [
    withThemeByDataAttribute({
      themes: { light: "light", dark: "dark" },
      defaultTheme: "light",
      attributeName: "data-theme",
    }),
  ],
  parameters: {
    layout: "padded",
    backgrounds: { disable: true },
    controls: { expanded: true },
  },
};

export default preview;
