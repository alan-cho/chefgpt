'use client'

import { useState } from 'react'
import { Bug, Zap } from 'lucide-react'
import { useChat } from '@/components/hooks/useChat'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export default function Home() {
    const [stream, setStream] = useState(true)
    const [debug, setDebug] = useState(false)

    const { messages, input, setInput, loading, threadId, handleSubmit } = useChat({
        stream,
        debug,
    })

    return (
        <div className="flex flex-col h-screen bg-background">
            <header className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
                <div>
                    <h1 className="text-base font-semibold tracking-tight">ChefGPT</h1>
                    <p className="text-xs text-muted-foreground">Your AI cooking assistant</p>
                </div>
                <div className="flex items-center gap-1">
                    <Button
                        variant="ghost"
                        size="icon-sm"
                        disabled={debug}
                        onClick={() => setStream((s) => !s)}
                        title={debug ? 'Streaming unavailable in debug mode' : stream ? 'Streaming on' : 'Streaming off'}
                        className={cn(
                            !debug && stream
                                ? 'bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 hover:text-amber-300'
                                : 'text-muted-foreground opacity-40',
                        )}
                    >
                        <Zap className={cn('size-4', !debug && stream && 'fill-current')} />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => {
                            setDebug((d) => {
                                if (!d) setStream(false)
                                return !d
                            })
                        }}
                        title={debug ? 'Debug on' : 'Debug off'}
                        className={cn(
                            debug
                                ? 'bg-violet-500/15 text-violet-400 hover:bg-violet-500/25 hover:text-violet-300'
                                : 'text-muted-foreground',
                        )}
                    >
                        <Bug className="size-4" />
                    </Button>
                </div>
            </header>

            <MessageList messages={messages} loading={loading} debug={debug} />

            <ChatInput
                value={input}
                onChange={setInput}
                onSubmit={handleSubmit}
                loading={loading}
                isFollowUp={!!threadId}
            />
        </div>
    )
}
