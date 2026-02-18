'use client'

import { useState } from 'react'
import type { SubmitEvent } from 'react'

export interface Message {
    role: 'user' | 'assistant'
    content: string
    error?: boolean
    debug?: { nodes: unknown[]; state: Record<string, unknown> }
}

export function useChat({
    stream,
    debug,
}: {
    stream: boolean
    debug: boolean
}) {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [threadId, setThreadId] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)

    async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
        e.preventDefault()

        const query = input.trim()
        if (!query || loading) return

        setInput('')
        setMessages((prev) => [...prev, { role: 'user', content: query }])
        setLoading(true)

        const streaming = stream && !debug

        try {
            const body = threadId
                ? {
                      query: '',
                      thread_id: threadId,
                      resume: query,
                      stream: streaming,
                      debug,
                  }
                : { query, stream: streaming, debug }

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            })

            if (streaming) {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: '' },
                ])
                if (!res.body) {
                    setLoading(false)
                    return
                }

                const reader = res.body.getReader()
                const decoder = new TextDecoder()
                let buffer = ''

                while (true) {
                    const { done, value } = await reader.read()
                    if (done) break

                    buffer += decoder.decode(value, { stream: true })
                    const parts = buffer.split('\n\n')
                    buffer = parts.pop()!

                    for (const part of parts) {
                        processSSEEvent(part.trim())
                    }
                }

                if (buffer.trim()) {
                    processSSEEvent(buffer.trim())
                }

                setLoading(false)
            } else {
                const data = await res.json()
                if (data.type === 'interrupt') {
                    setThreadId(data.thread_id)
                    setMessages((prev) => [
                        ...prev,
                        {
                            role: 'assistant',
                            content: data.question,
                            debug: data.debug,
                        },
                    ])
                } else {
                    setThreadId(null)
                    setMessages((prev) => [
                        ...prev,
                        {
                            role: 'assistant',
                            content: data.response,
                            debug: data.debug,
                        },
                    ])
                }

                setLoading(false)
            }
        } catch {
            setThreadId(null)
            setMessages((prev) => {
                // Strip any empty assistant bubble added at the start of streaming
                const withoutEmpty =
                    prev[prev.length - 1]?.role === 'assistant' && prev[prev.length - 1]?.content === ''
                        ? prev.slice(0, -1)
                        : prev
                return [
                    ...withoutEmpty,
                    { role: 'assistant', content: 'Something went wrong. Please try again.', error: true },
                ]
            })
            setLoading(false)
        }
    }

    function processSSEEvent(line: string) {
        if (!line.startsWith('data: ')) return
        const event = JSON.parse(line.slice(6))

        switch (event.type) {
            case 'token':
                setMessages((prev) => {
                    const updated = [...prev]
                    const last = updated[updated.length - 1]
                    updated[updated.length - 1] = {
                        ...last,
                        content: last.content + event.content,
                    }
                    return updated
                })
                break
            case 'response':
                setMessages((prev) => {
                    const updated = [...prev]
                    updated[updated.length - 1] = {
                        ...updated[updated.length - 1],
                        content: event.content,
                    }
                    return updated
                })
                setThreadId(null)
                break
            case 'interrupt':
                setMessages((prev) => {
                    const updated = [...prev]
                    updated[updated.length - 1] = {
                        ...updated[updated.length - 1],
                        content: event.question,
                    }
                    return updated
                })
                setThreadId(event.thread_id)
                break
            case 'done':
                setLoading(false)
                break
        }
    }

    return { messages, input, setInput, loading, threadId, handleSubmit }
}
