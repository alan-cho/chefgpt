export function TypingIndicator() {
    return (
        <div className="flex justify-start">
            <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-3.5">
                <div className="flex gap-1.5 items-center h-4">
                    {[0, 1, 2].map((i) => (
                        <span
                            key={i}
                            className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                            style={{
                                animation: `dot-pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    )
}
