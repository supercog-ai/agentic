import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MarkdownComponents = {
  // Style code blocks
  code(props: any) {
    const {children, className, node, ...rest} = props;
    const match = /language-(\w+)/.exec(className || '');
    return (
      <pre className="bg-muted/50 p-4 rounded-lg overflow-auto">
        <code className={className} {...rest}>
          {children}
        </code>
      </pre>
    );
  },
  // Style inline code
  inlineCode(props: any) {
    return (
      <code className="bg-muted/50 px-1.5 py-0.5 rounded-md text-sm" {...props} />
    );
  },
  // Style links
  a(props: any) {
    return (
      <a className="text-blue-500 hover:underline whitespace-pre-wrap break-all" target="_blank" {...props} />
    );
  },
  // Style lists
  ul(props: any) {
    return <ul className="list-disc list-inside my-4" {...props} />;
  },
  ol(props: any) {
    return <ol className="list-decimal list-inside my-4" {...props} />;
  },
  // Style headings
  h1(props: any) {
    return <h1 className="text-2xl font-bold my-4" {...props} />;
  },
  h2(props: any) {
    return <h2 className="text-xl font-bold my-3" {...props} />;
  },
  h3(props: any) {
    return <h3 className="text-lg font-bold my-2" {...props} />;
  },
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

export  default MarkdownRenderer;