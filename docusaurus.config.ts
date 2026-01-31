import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'BBj AI Strategy',
  tagline: 'Intelligent Code Assistance Across Four Generations of Business BASIC',
  favicon: 'img/favicon.ico',

  url: 'https://beff.github.io',
  baseUrl: '/bbj-ai-strategy/',
  organizationName: 'beff',
  projectName: 'bbj-ai-strategy',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  future: {
    v4: true,
    experimental_faster: true,
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'BBj AI Strategy',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'strategySidebar',
          position: 'left',
          label: 'Strategy',
        },
        {
          href: 'https://github.com/beff/bbj-ai-strategy',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      copyright: `Copyright ${new Date().getFullYear()} BASIS International Ltd.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
