import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const chapters = [
  {
    title: 'The BBj Challenge',
    href: '/docs/bbj-challenge',
    description: 'Why generic LLMs fail on four generations of Business BASIC.',
  },
  {
    title: 'Strategic Architecture',
    href: '/docs/strategic-architecture',
    description: 'A unified infrastructure powering all AI capabilities.',
  },
  {
    title: 'Fine-Tuning the Model',
    href: '/docs/fine-tuning',
    description: 'Training a BBj-aware language model with LoRA and Ollama.',
  },
  {
    title: 'IDE Integration',
    href: '/docs/ide-integration',
    description: 'Bringing BBj intelligence into the developer\'s editor.',
  },
  {
    title: 'Documentation Chat',
    href: '/docs/documentation-chat',
    description: 'Generation-aware answers embedded in the docs site.',
  },
  {
    title: 'RAG Database Design',
    href: '/docs/rag-database',
    description: 'Multi-generation retrieval for precise, context-aware results.',
  },
  {
    title: 'Implementation Roadmap',
    href: '/docs/implementation-roadmap',
    description: 'Progress summary and forward plan for the BBj AI strategy.',
  },
];

const initiatives = [
  {
    title: 'Fine-Tuned BBj Model',
    description:
      'A LoRA-trained language model hosted via Ollama that understands all four generations of BBj -- from legacy Business BASIC to modern DWC applications.',
  },
  {
    title: 'IDE Integration',
    description:
      'A VSCode extension powered by Langium that delivers intelligent completions, diagnostics, and generation-aware suggestions directly in the editor.',
  },
  {
    title: 'Documentation Chat',
    description:
      'A RAG-powered conversational interface embedded in this documentation site, providing generation-aware answers grounded in real BBj knowledge.',
  },
];

const audiences = [
  {
    title: 'For Developers',
    description:
      'How the fine-tuned model, IDE extension, and RAG pipeline work -- technical depth for implementers.',
    links: [
      {label: 'Fine-Tuning the Model', href: '/docs/fine-tuning'},
      {label: 'IDE Integration', href: '/docs/ide-integration'},
      {label: 'RAG Database Design', href: '/docs/rag-database'},
    ],
  },
  {
    title: 'For Leadership',
    description:
      'Strategic vision, architecture decisions, and implementation roadmap -- the business case for BBj AI.',
    links: [
      {label: 'Strategic Architecture', href: '/docs/strategic-architecture'},
      {label: 'The BBj Challenge', href: '/docs/bbj-challenge'},
      {label: 'Implementation Roadmap', href: '/docs/implementation-roadmap'},
    ],
  },
  {
    title: 'For Customers & Partners',
    description:
      'What this means for your BBj applications -- the developer experience improvements ahead.',
    links: [
      {label: 'The BBj Challenge', href: '/docs/bbj-challenge'},
      {label: 'Strategic Architecture', href: '/docs/strategic-architecture'},
      {label: 'Implementation Roadmap', href: '/docs/implementation-roadmap'},
    ],
  },
];

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          Generic LLMs Fail on BBj
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <p className={styles.heroHook}>
          BBj spans four decades of Business BASIC evolution, but virtually none
          of that code exists in public training data. Copilot hallucinates.
          ChatGPT guesses. A custom AI strategy is the only path forward.
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/bbj-challenge">
            Read the Strategy
          </Link>
        </div>
      </div>
    </header>
  );
}

function ExecutiveSummary() {
  return (
    <section className={styles.executiveSummary}>
      <div className="container">
        <Heading as="h2" className={styles.sectionHeading}>
          Why This Strategy Exists
        </Heading>
        <div className={styles.summaryText}>
          <p>
            BBj is the modern face of a language lineage that began in the 1980s
            with Business BASIC. Over four generations -- BBx, PRO/5, Visual
            PRO/5, and BBj -- the platform evolved from character-mode terminal
            applications to browser-based DWC apps running on the JVM. Thousands
            of production systems still rely on this stack, many carrying code
            from multiple generations in the same codebase.
          </p>
          <p>
            Large language models trained on public data have effectively zero
            coverage of BBj. When developers ask Copilot or ChatGPT for help,
            they get plausible-looking code that uses wrong syntax, invents
            nonexistent functions, and confuses generation-specific APIs. The
            hallucination rate is not a minor inconvenience -- it makes generic
            AI tools actively harmful for BBj development.
          </p>
          <p>
            This strategy proposes three integrated initiatives, built on a
            shared AI infrastructure, to deliver real code intelligence for BBj
            developers.
          </p>
        </div>
        <div className={styles.initiativeGrid}>
          {initiatives.map((initiative, idx) => (
            <div key={idx} className={styles.initiativeCard}>
              <Heading as="h3">{initiative.title}</Heading>
              <p>{initiative.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AudienceRouting() {
  return (
    <section className={styles.audienceRouting}>
      <div className="container">
        <Heading as="h2" className={styles.sectionHeading}>
          Find What Matters to You
        </Heading>
        <div className={styles.audienceGrid}>
          {audiences.map((audience, idx) => (
            <div key={idx} className={styles.audienceCard}>
              <Heading as="h3">{audience.title}</Heading>
              <p>{audience.description}</p>
              <ul className={styles.audienceLinks}>
                {audience.links.map((link, linkIdx) => (
                  <li key={linkIdx}>
                    <Link to={link.href}>{link.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ChapterOverview() {
  return (
    <section className={styles.chapters}>
      <div className="container">
        <Heading as="h2" className={styles.sectionHeading}>
          All Chapters
        </Heading>
        <div className={styles.chapterGrid}>
          {chapters.map((chapter, idx) => (
            <Link key={idx} className={styles.chapterCard} to={chapter.href}>
              <span className={styles.chapterNumber}>{idx + 1}</span>
              <Heading as="h3">{chapter.title}</Heading>
              <p>{chapter.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout
      title="Home"
      description="Intelligent Code Assistance Across Four Generations of Business BASIC">
      <HomepageHeader />
      <main>
        <ExecutiveSummary />
        <AudienceRouting />
        <ChapterOverview />
      </main>
    </Layout>
  );
}
