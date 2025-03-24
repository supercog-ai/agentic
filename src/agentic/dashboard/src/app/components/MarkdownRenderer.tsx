import React from 'react';
import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Define the components using the correct typing from react-markdown
const MarkdownComponents: Components = {
  // Style code blocks
  code({ className, children, ...props }) {
    return (
      <pre className="bg-muted/50 p-4 rounded-lg overflow-auto">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    );
  },
  // Style links
  a({ children, ...props }) {
    return (
      <a className="text-blue-500 hover:underline whitespace-pre-wrap break-all" target="_blank" rel="noopener noreferrer" {...props}>
        {children}
      </a>
    );
  },
  // Style lists
  ul({ children, ...props }) {
    return <ul className="list-disc list-inside my-4 [&>li>p]:inline [&>li>p]:m-0" {...props}>{children}</ul>;
  },
  ol({ children, ...props }) {
    return <ol className="list-decimal list-inside my-4 [&>li>p]:inline [&>li>p]:m-0" {...props}>{children}</ol>;
  },
  // Style headings
  h1({ children, ...props }) {
    return <h1 className="text-2xl font-bold my-4" {...props}>{children}</h1>;
  },
  h2({ children, ...props }) {
    return <h2 className="text-xl font-bold my-3" {...props}>{children}</h2>;
  },
  h3({ children, ...props }) {
    return <h3 className="text-lg font-bold my-2" {...props}>{children}</h3>;
  },
  hr({ ...props }) {
    return <hr className="my-4" {...props} />;
  }
};

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={MarkdownComponents}
    >
      {content}
    </ReactMarkdown>
  );
}

export default MarkdownRenderer;
