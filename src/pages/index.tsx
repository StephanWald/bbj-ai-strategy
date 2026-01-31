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
    description: 'Phased delivery, resources, risks, and success metrics.',
  },
];

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
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

function ChapterOverview() {
  return (
    <section className={styles.chapters}>
      <div className="container">
        <div className={styles.chapterGrid}>
          {chapters.map((chapter, idx) => (
            <Link key={idx} className={styles.chapterCard} to={chapter.href}>
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
        <section className={styles.about}>
          <div className="container">
            <p>
              This site presents a comprehensive strategy for building AI-powered
              developer tools tailored to BBj -- a language that spans four
              generations of Business BASIC. From fine-tuned models to IDE
              extensions to documentation chat, each chapter covers a key piece
              of the architecture.
            </p>
          </div>
        </section>
        <ChapterOverview />
      </main>
    </Layout>
  );
}
