'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, Tag, Utensils, ChefHat, Search, MessageCircle, Bot, XCircle, Wrench } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface NodeStep {
    node: string
    delta: Record<string, unknown>
}

interface DebugPanelProps {
    data: {
        nodes: NodeStep[]
        state: Record<string, unknown>
    }
}

const NODE_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
    classify: {
        label: 'Classify',
        icon: <Tag className="size-3" />,
        color: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
    },
    check_cookware: {
        label: 'Cookware Check',
        icon: <Utensils className="size-3" />,
        color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    },
    inquire: {
        label: 'Inquire',
        icon: <MessageCircle className="size-3" />,
        color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    },
    generate_recipe: {
        label: 'Generate Recipe',
        icon: <ChefHat className="size-3" />,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    },
    assistant: {
        label: 'Assistant',
        icon: <Bot className="size-3" />,
        color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    },
    tools: {
        label: 'Tool Call',
        icon: <Search className="size-3" />,
        color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    },
    respond_not_cooking: {
        label: 'Refused',
        icon: <XCircle className="size-3" />,
        color: 'text-red-400 bg-red-500/10 border-red-500/20',
    },
}

const FALLBACK_META = {
    label: 'Node',
    icon: <Wrench className="size-3" />,
    color: 'text-muted-foreground bg-muted border-border',
}

function extractSummary(node: string, delta: Record<string, unknown>): string[] {
    const lines: string[] = []

    if (node === 'classify') {
        if ('is_cooking_related' in delta)
            lines.push(`Cooking related: ${delta.is_cooking_related ? 'yes' : 'no'}`)
        if (delta.query_intent)
            lines.push(`Intent: ${delta.query_intent}`)
    }

    if (node === 'check_cookware') {
        if (Array.isArray(delta.required_cookware) && delta.required_cookware.length)
            lines.push(`Required: ${(delta.required_cookware as string[]).join(', ')}`)
        if (Array.isArray(delta.missing_cookware) && delta.missing_cookware.length)
            lines.push(`Missing: ${(delta.missing_cookware as string[]).join(', ')}`)
        else if ('missing_cookware' in delta)
            lines.push('Missing: none')
    }

    if (node === 'inquire') {
        if (delta.user_preferences)
            lines.push(`User answered: ${delta.user_preferences}`)
        else
            lines.push('No clarification needed')
    }

    if (node === 'tools') {
        const msgs = delta.messages as Array<Record<string, unknown>> | undefined
        if (Array.isArray(msgs)) {
            msgs.forEach((m) => {
                if (m.name) lines.push(`Tool: ${m.name}`)
            })
        }
    }

    if (node === 'generate_recipe' || node === 'assistant') {
        const msgs = delta.messages as Array<Record<string, unknown>> | undefined
        if (Array.isArray(msgs)) {
            const last = msgs[msgs.length - 1]
            const toolCalls = last?.tool_calls as Array<Record<string, unknown>> | undefined
            if (Array.isArray(toolCalls) && toolCalls.length) {
                toolCalls.forEach((tc) => {
                    lines.push(`Calling tool: ${tc.name}`)
                })
            } else {
                lines.push('Generated response')
            }
        }
    }

    return lines
}

function NodeStepCard({ step, index }: { step: NodeStep; index: number }) {
    const [expanded, setExpanded] = useState(false)
    const meta = NODE_META[step.node] ?? FALLBACK_META
    const summary = extractSummary(step.node, step.delta)

    return (
        <div className="flex gap-2.5">
            {/* Timeline spine */}
            <div className="flex flex-col items-center">
                <div className={cn('flex items-center justify-center size-5 rounded-full border text-[10px] font-bold shrink-0', meta.color)}>
                    {index + 1}
                </div>
                <div className="w-px flex-1 bg-border mt-1" />
            </div>

            {/* Card */}
            <div className="flex-1 pb-3 min-w-0">
                <div className={cn('rounded-lg border px-3 py-2', meta.color)}>
                    <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5">
                            {meta.icon}
                            <span className="text-xs font-medium">{meta.label}</span>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon-xs"
                            className="opacity-60 hover:opacity-100 -mr-1"
                            onClick={() => setExpanded((v) => !v)}
                        >
                            {expanded ? <ChevronUp /> : <ChevronDown />}
                        </Button>
                    </div>

                    {summary.length > 0 && (
                        <ul className="mt-1.5 space-y-0.5">
                            {summary.map((line, i) => (
                                <li key={i} className="text-xs opacity-80">{line}</li>
                            ))}
                        </ul>
                    )}

                    {expanded && (
                        <pre className="mt-2 text-[10px] leading-relaxed bg-black/20 rounded p-2 overflow-x-auto opacity-80 whitespace-pre-wrap">
                            {JSON.stringify(step.delta, null, 2)}
                        </pre>
                    )}
                </div>
            </div>
        </div>
    )
}

export function DebugPanel({ data }: DebugPanelProps) {
    return (
        <div className="mt-2 rounded-xl border border-border bg-background/50 px-3 pt-3 pb-1 text-xs max-w-[85%]">
            <p className="text-muted-foreground font-medium mb-3 flex items-center gap-1.5">
                <Wrench className="size-3" />
                Reasoning chain · {data.nodes.length} step{data.nodes.length !== 1 ? 's' : ''}
            </p>
            <div>
                {data.nodes.map((step, i) => (
                    <NodeStepCard key={i} step={step} index={i} />
                ))}
            </div>
        </div>
    )
}
