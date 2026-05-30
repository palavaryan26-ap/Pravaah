import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  description: ReactNode;
};

const FeatureList = [
  {
    title: 'Plugin Architecture',
    description: (
      <>
        Build modular applications through reusable plugins that can register
        models, routers, services, and workflows.
      </>
    ),
  },
  {
    title: 'Dynamic CRUD Engine',
    description: (
      <>
        Generate production-ready CRUD APIs automatically from model
        definitions with minimal boilerplate.
      </>
    ),
  },
  {
    title: 'Event System',
    description: (
      <>
        Trigger business logic through events and hooks instead of tightly
        coupling application components.
      </>
    ),
  },
  {
    title: 'AI Layer',
    description: (
      <>
        Integrate AI-powered actions, lead scoring, content generation, and
        intelligent workflows directly into applications.
      </>
    ),
  },
  {
    title: 'Workflow Orchestration',
    description: (
      <>
        Coordinate multi-step business processes through event-driven
        automation and future workflow engine capabilities.
      </>
    ),
  },
  {
    title: 'Production Ready',
    description: (
      <>
        Docker support, async architecture, plugin isolation, and cloud
        deployment support out of the box.
      </>
    ),
  },
];

function Feature({title, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}