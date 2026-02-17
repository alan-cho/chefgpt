'use client'

import { useRef, useEffect } from 'react'
import type { SubmitEvent } from 'react'
import { SendHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface ChatInputProps {
    value: string
    onChange: (value: string) => void
    onSubmit: (e: SubmitEvent<HTMLFormElement>) => void
    loading: boolean
    isFollowUp: boolean
}

export function ChatInput({
    value,
    onChange,
    onSubmit,
    loading,
    isFollowUp,
}: ChatInputProps) {
    const formRef = useRef<HTMLFormElement>(null)
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    useEffect(() => {
        const el = textareaRef.current
        if (!el) return
        el.style.height = 'auto'
        el.style.height = `${Math.min(el.scrollHeight, 160)}px`
    }, [value])

    function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            formRef.current?.requestSubmit()
        }
    }

    return (
        <div className="border-t border-border bg-background px-4 py-4">
            <form
                ref={formRef}
                onSubmit={onSubmit}
                className="max-w-2xl mx-auto"
            >
                {isFollowUp && (
                    <p className="text-xs text-muted-foreground mb-2 pl-1">
                        Answering a follow-up question
                    </p>
                )}
                <div
                    className={cn(
                        'flex items-center gap-2 rounded-xl border border-input bg-input/30 px-3 py-2',
                        'focus-within:border-ring focus-within:ring-1 focus-within:ring-ring/30 transition-all'
                    )}
                >
                    <textarea
                        ref={textareaRef}
                        rows={1}
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={
                            isFollowUp
                                ? 'Type your answer…'
                                : 'Ask about a recipe, ingredient, or technique…'
                        }
                        disabled={loading}
                        className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none disabled:opacity-50 py-0.5 leading-relaxed"
                    />
                    <Button
                        type="submit"
                        size="icon-sm"
                        disabled={loading || !value.trim()}
                    >
                        <SendHorizontal />
                    </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-1.5 pl-1">
                    Enter to send · Shift+Enter for new line
                </p>
            </form>
        </div>
    )
}
