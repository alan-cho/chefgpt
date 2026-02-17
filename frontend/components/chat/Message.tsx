'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { Message } from '@/components/hooks/useChat'

interface ChatMessageProps {
    message: Message
    debug: boolean
}

export function ChatMessage({ message, debug }: ChatMessageProps) {
    const [showDebug, setShowDebug] = useState(false)
    const isUser = message.role === 'user'

    return (
        <div className={cn('flex flex-col gap-1', isUser ? 'items-end' : 'items-start')}>
            <div
                className={cn(
                    'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                    isUser
                        ? 'bg-primary text-primary-foreground rounded-br-sm'
                        : 'bg-muted text-foreground rounded-bl-sm',
                )}
            >
                <p className="whitespace-pre-wrap">{message.content || '…'}</p>
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
