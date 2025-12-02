import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

export default function MarkdownRenderer({ text }) {
    return (
        <div className="prose prose-neutral max-w-none break-words">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                    h1: ({ node, ...props }) => (
                        <h1 className="text-3xl font-bold mt-6 mb-4 text-neutral-900" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                        <h2 className="text-2xl font-semibold mt-5 mb-3 text-neutral-900" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                        <h3 className="text-xl font-medium mt-4 mb-2 text-neutral-900" {...props} />
                    ),
                    p: ({ node, ...props }) => (
                        <p className="my-2 text-[15px] leading-6 text-neutral-800" {...props} />
                    ),
                    a: ({ node, ...props }) => (
                        <a className="text-blue-600 underline hover:text-blue-800" {...props} />
                    ),
                    pre: ({ node, ...props }) => (
                        <pre className="bg-neutral-300 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                        <ol className="list-decimal list-outside ml-6 my-2 space-y-1" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                        <ul className="list-disc list-outside ml-6 my-2 space-y-1" {...props} />
                    ),
                    li: ({ node, ...props }) => (
                        <li className="text-base" {...props} />
                    ),
                }}
            >
                {text}
            </ReactMarkdown>
        </div>
    );
}
