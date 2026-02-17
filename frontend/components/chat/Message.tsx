'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { Message } from '@/components/hooks/useChat'

interface ChatMessageProps {
    message: Message
    debug: boolean
    isStreaming?: boolean
}

const markdownComponents: React.ComponentProps<typeof ReactMarkdown>['components'] = {
    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
    em: ({ children }) => <em className="italic">{children}</em>,
    h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1 first:mt-0">{children}</h1>,
    h2: ({ children }) => <h2 className="text-sm font-bold mt-3 mb-1 first:mt-0">{children}</h2>,
    h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 first:mt-0">{children}</h3>,
    ul: ({ children }) => <ul className="list-disc list-outside ml-4 mb-2 space-y-0.5">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal list-outside ml-4 mb-2 space-y-0.5">{children}</ol>,
    li: ({ children }) => <li>{children}</li>,
    code: ({ children }) => (
        <code className="bg-black/20 rounded px-1 py-0.5 font-mono text-xs">{children}</code>
    ),
    pre: ({ children }) => (
        <pre className="bg-black/20 rounded-lg p-3 overflow-x-auto font-mono text-xs mb-2">{children}</pre>
    ),
    hr: () => <hr className="border-border my-3" />,
    a: ({ href, children }) => (
        <a href={href} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2 hover:opacity-80">
            {children}
        </a>
    ),
}

export function ChatMessage({ message, debug, isStreaming }: ChatMessageProps) {
    const [showDebug, setShowDebug] = useState(false)
    const isUser = message.role === 'user'

    return (
        <div className={cn('flex flex-col gap-1', isUser ? 'items-end' : 'items-start')}>
            <div
                className={cn(
                    'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                    isUser && 'bg-primary text-primary-foreground rounded-br-sm',
                    !isUser && !message.error && 'bg-muted text-foreground rounded-bl-sm',
                    !isUser && message.error && 'bg-destructive/15 text-destructive rounded-bl-sm',
                )}
            >
                {isUser ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                    <div className={cn(isStreaming && 'streaming-bubble')}>
                        <ReactMarkdown components={markdownComponents}>
                            {message.content || '…'}
                        </ReactMarkdown>
                    </div>
                )}
            </div>

            {debug && message.debug && (
                <div className="max-w-[85%] w-full">
                    <Button
                        variant="ghost"
                        size="xs"
                        className="text-muted-foreground h-5 gap-1"
                        onClick={() => setShowDebug((v) => !v)}
                    >
                        {showDebug ? <ChevronUp /> : <ChevronDown />}
                        Debug
                    </Button>
                    {showDebug && (
                        <pre className="mt-1 text-xs bg-muted rounded-lg p-3 overflow-x-auto text-muted-foreground">
                            {JSON.stringify(message.debug, null, 2)}
                        </pre>
                    )}
                </div>
            )}
        </div>
    )
}
