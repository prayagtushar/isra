
export async function* parseSSE<T>(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<T, void, unknown> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const extract = (block: string): string | null => {
    
    const dataLines: string[] = [];
    for (const rawLine of block.split("\n")) {
      const line = rawLine.trimStart();
      
      const match = /^data\s*:(.*)$/.exec(line);
      if (match) dataLines.push(match[1]);
    }
    if (dataLines.length === 0) return null;
    return dataLines.join("\n").trim();
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";

      for (const block of blocks) {
        const payload = extract(block);
        if (!payload) continue;
        try {
          yield JSON.parse(payload) as T;
        } catch {
          
        }
      }
    }

    
    const payload = extract(buffer);
    if (payload) {
      try {
        yield JSON.parse(payload) as T;
      } catch {
        
      }
    }
  } finally {
    reader.releaseLock();
  }
}
