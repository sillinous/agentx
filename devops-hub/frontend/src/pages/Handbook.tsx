import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, Badge, LoadingScreen } from '../components/ui';
import {
  useHandbook,
  useGuide,
  useExamples,
  useAllAgentDocs,
} from '../api/hooks';

// Simple markdown-like renderer
function MarkdownContent({ content }: { content: string }) {
  const renderContent = (text: string): React.ReactNode[] => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeLines: string[] = [];

    lines.forEach((line, index) => {
      // Code block handling
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeLines = [];
        } else {
          elements.push(
            <pre
              key={`code-${index}`}
              className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm my-4"
            >
              <code>{codeLines.join('\n')}</code>
            </pre>
          );
          inCodeBlock = false;
        }
        return;
      }

      if (inCodeBlock) {
        codeLines.push(line);
        return;
      }

      // Headers
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={index} className="text-3xl font-bold text-gray-900 mt-8 mb-4">
            {line.slice(2)}
          </h1>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={index} className="text-2xl font-semibold text-gray-900 mt-6 mb-3">
            {line.slice(3)}
          </h2>
        );
      } else if (line.startsWith('### ')) {
        elements.push(
          <h3 key={index} className="text-xl font-semibold text-gray-800 mt-4 mb-2">
            {line.slice(4)}
          </h3>
        );
      }
      // Lists
      else if (line.startsWith('- ')) {
        elements.push(
          <li key={index} className="ml-4 text-gray-700">
            {renderInlineStyles(line.slice(2))}
          </li>
        );
      } else if (/^\d+\.\s/.test(line)) {
        elements.push(
          <li key={index} className="ml-4 text-gray-700 list-decimal">
            {renderInlineStyles(line.replace(/^\d+\.\s/, ''))}
          </li>
        );
      }
      // Tables (simple)
      else if (line.startsWith('|')) {
        const cells = line.split('|').filter(Boolean).map((c) => c.trim());
        if (cells.every((c) => c.match(/^-+$/))) {
          // Skip separator row
        } else {
          const isHeader = index > 0 && lines[index + 1]?.includes('---');
          elements.push(
            <tr key={index} className={isHeader ? 'bg-gray-100' : ''}>
              {cells.map((cell, i) =>
                isHeader ? (
                  <th key={i} className="border px-3 py-2 text-left font-medium">
                    {cell}
                  </th>
                ) : (
                  <td key={i} className="border px-3 py-2">
                    {cell}
                  </td>
                )
              )}
            </tr>
          );
        }
      }
      // Empty lines
      else if (line.trim() === '') {
        elements.push(<br key={index} />);
      }
      // Regular paragraphs
      else {
        elements.push(
          <p key={index} className="text-gray-700 my-2">
            {renderInlineStyles(line)}
          </p>
        );
      }
    });

    return elements;
  };

  const renderInlineStyles = (text: string) => {
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>');
    // Links
    text = text.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" class="text-blue-600 hover:underline">$1</a>'
    );

    return <span dangerouslySetInnerHTML={{ __html: text }} />;
  };

  // Wrap tables
  const elements = renderContent(content);
  const wrappedElements: React.ReactNode[] = [];
  let tableRows: React.ReactNode[] = [];

  elements.forEach((el, i) => {
    // Check if element is a table row by checking if it's a valid element with type 'tr'
    const isTableRow = el && typeof el === 'object' && 'type' in el && (el as React.ReactElement).type === 'tr';
    if (isTableRow) {
      tableRows.push(el);
    } else {
      if (tableRows.length > 0) {
        wrappedElements.push(
          <table key={`table-${i}`} className="w-full border-collapse my-4">
            <tbody>{tableRows}</tbody>
          </table>
        );
        tableRows = [];
      }
      wrappedElements.push(el);
    }
  });

  if (tableRows.length > 0) {
    wrappedElements.push(
      <table key="table-end" className="w-full border-collapse my-4">
        <tbody>{tableRows}</tbody>
      </table>
    );
  }

  return <div className="prose max-w-none">{wrappedElements}</div>;
}

// Sidebar navigation component
function TableOfContents({
  handbook,
  currentSlug,
  onSelect,
}: {
  handbook: ReturnType<typeof useHandbook>['data'];
  currentSlug: string;
  onSelect: (type: string, slug: string) => void;
}) {
  if (!handbook) return null;

  const categoryLabels: Record<string, string> = {
    'getting-started': 'Getting Started',
    reference: 'Reference',
    advanced: 'Advanced',
    agents: 'Agent Guides',
  };

  const categoryOrder = ['getting-started', 'agents', 'reference', 'advanced'];

  return (
    <nav className="space-y-6">
      {categoryOrder.map((category) => {
        const data = handbook.categories[category];
        if (!data || data.guides.length === 0) return null;

        return (
          <div key={category}>
            <h3 className="font-semibold text-gray-900 mb-2">
              {categoryLabels[category] || category}
            </h3>
            <ul className="space-y-1">
              {data.guides.map((guide) => (
                <li key={guide.id}>
                  <button
                    onClick={() => onSelect('guide', guide.slug)}
                    className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                      currentSlug === guide.slug
                        ? 'bg-blue-100 text-blue-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {guide.title}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        );
      })}

      {/* Agent Docs Link */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-2">Dynamic Agent Docs</h3>
        <button
          onClick={() => onSelect('agents', 'all')}
          className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
            currentSlug === 'agents/all'
              ? 'bg-blue-100 text-blue-700 font-medium'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          All Agent Documentation
        </button>
      </div>

      {/* Examples Section */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-2">Examples</h3>
        <button
          onClick={() => onSelect('examples', 'all')}
          className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
            currentSlug === 'examples/all'
              ? 'bg-blue-100 text-blue-700 font-medium'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          View All Examples
        </button>
      </div>
    </nav>
  );
}

// Examples list component
function ExamplesList() {
  const { data, isLoading } = useExamples();

  if (isLoading) return <LoadingScreen message="Loading examples..." />;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Examples</h1>
      <p className="text-gray-600 mb-6">
        Learn how to use agents and workflows with these practical examples.
      </p>

      <div className="grid gap-4">
        {data?.examples.map((example) => (
          <Card key={example.id}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">{example.title}</h3>
                <p className="text-sm text-gray-600 mb-3">{example.description}</p>
                <div className="flex flex-wrap gap-2 mb-3">
                  <Badge variant="info">{example.category}</Badge>
                  {example.agent_ids.map((agentId) => (
                    <Badge key={agentId} variant="default">
                      {agentId}
                    </Badge>
                  ))}
                  {example.tags.map((tag) => (
                    <Badge key={tag} variant="purple">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-2">Input Example:</p>
              <pre className="text-xs bg-white p-2 rounded border overflow-auto">
                {JSON.stringify(example.input_example, null, 2)}
              </pre>
            </div>

            {example.expected_output && (
              <p className="text-sm text-gray-600 mt-3">
                <strong>Expected:</strong> {example.expected_output}
              </p>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}

// Agent documentation list
function AgentDocsList() {
  const { data, isLoading } = useAllAgentDocs();

  if (isLoading) return <LoadingScreen message="Loading agent documentation..." />;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Agent Documentation</h1>
      <p className="text-gray-600 mb-6">
        Auto-generated documentation for all registered agents. This content updates
        automatically when agents are added or modified.
      </p>

      <div className="grid gap-4">
        {data?.agents.map((doc) => (
          <Card key={doc.id}>
            <div className="flex items-start justify-between mb-4">
              <h3 className="font-semibold text-gray-900 text-lg">{doc.title}</h3>
              <div className="flex gap-2">
                <Badge variant="info">{doc.metadata.domain}</Badge>
                <Badge variant="purple">{doc.metadata.type}</Badge>
              </div>
            </div>
            <MarkdownContent content={doc.content} />
          </Card>
        ))}
      </div>
    </div>
  );
}

// Main Handbook page
export default function Handbook() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [currentSlug, setCurrentSlug] = useState(searchParams.get('page') || 'welcome');
  const [viewType, setViewType] = useState<'guide' | 'agents' | 'examples'>(
    (searchParams.get('type') as 'guide' | 'agents' | 'examples') || 'guide'
  );

  const { data: handbook, isLoading: handbookLoading } = useHandbook();
  const { data: guide, isLoading: guideLoading } = useGuide(
    viewType === 'guide' ? currentSlug : ''
  );

  const handleSelect = (type: string, slug: string) => {
    if (type === 'agents') {
      setViewType('agents');
      setCurrentSlug('agents/all');
      setSearchParams({ type: 'agents', page: 'all' });
    } else if (type === 'examples') {
      setViewType('examples');
      setCurrentSlug('examples/all');
      setSearchParams({ type: 'examples', page: 'all' });
    } else {
      setViewType('guide');
      setCurrentSlug(slug);
      setSearchParams({ type: 'guide', page: slug });
    }
  };

  // Sync state from URL when navigating with browser back/forward
  // Only update if the URL value differs from current state
  useEffect(() => {
    const page = searchParams.get('page');
    const type = searchParams.get('type');
    if (page && page !== currentSlug) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCurrentSlug(page);
    }
    if (type && type !== viewType) {
      setViewType(type as 'guide' | 'agents' | 'examples');
    }
  }, [searchParams, currentSlug, viewType]);

  if (handbookLoading) {
    return <LoadingScreen message="Loading handbook..." />;
  }

  return (
    <div className="flex gap-8">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0">
        <Card className="sticky top-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-lg">📖</span>
            </div>
            <h2 className="font-bold text-gray-900">User Guide</h2>
          </div>

          <TableOfContents
            handbook={handbook}
            currentSlug={viewType === 'guide' ? currentSlug : `${viewType}/all`}
            onSelect={handleSelect}
          />

          {handbook && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-400">
                {handbook.guide_count} guides · {handbook.example_count} examples
              </p>
              <p className="text-xs text-gray-400">
                {handbook.agent_count} agents documented
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Content */}
      <div className="flex-grow min-w-0">
        <Card padding="lg">
          {viewType === 'agents' ? (
            <AgentDocsList />
          ) : viewType === 'examples' ? (
            <ExamplesList />
          ) : guideLoading ? (
            <LoadingScreen message="Loading guide..." />
          ) : guide ? (
            <MarkdownContent content={guide.content} />
          ) : (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📖</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Guide not found</h3>
              <p className="text-gray-500">
                The requested documentation page could not be found.
              </p>
              <button
                onClick={() => handleSelect('guide', 'welcome')}
                className="mt-4 text-blue-600 hover:underline"
              >
                Go to Welcome page
              </button>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
