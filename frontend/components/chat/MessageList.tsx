'use client'

import { useEffect, useRef } from 'react'
import type { Message } from '@/components/hooks/useChat'
import { ChatMessage } from './Message'
import { TypingIndicator } from './TypingIndicator'

interface MessageListProps {
    messages: Message[]
    loading: boolean
    debug: boolean
}

export function MessageList({ messages, loading, debug }: MessageListProps) {
    const bottomRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading])

    if (messages.length === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-center px-4">
                <p className="text-4xl">👨‍🍳</p>
                <p className="text-muted-foreground text-sm">
                    Ask me about recipes, ingredients, or cooking techniques.
                </p>
            </div>
        )
    }

    const lastMsg = messages[messages.length - 1]
    const lastIsUser = lastMsg?.role === 'user'
    // Empty assistant bubble = streaming started but no tokens yet; show typing indicator instead
    const lastIsEmptyStream = lastMsg?.role === 'assistant' && !lastMsg.content && loading

    const displayMessages = lastIsEmptyStream ? messages.slice(0, -1) : messages
    const showTypingIndicator = loading && (lastIsUser || lastIsEmptyStream)

    return (
        <div className="flex-1 overflow-y-auto py-6 px-4">
            <div className="max-w-2xl mx-auto space-y-4">
                {displayMessages.map((msg, i) => (
                    <ChatMessage
                        key={i}
                        message={msg}
                        debug={debug}
                        isStreaming={loading && i === displayMessages.length - 1 && msg.role === 'assistant'}
                    />
                ))}
                {showTypingIndicator && <TypingIndicator />}
                <div ref={bottomRef} />
            </div>
        </div>
    )
}
