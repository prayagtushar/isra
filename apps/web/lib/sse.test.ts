import { describe, expect, it } from "vitest";
import { parseSSE } from "./sse";

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

async function collect<T>(gen: AsyncGenerator<T>): Promise<T[]> {
  const out: T[] = [];
  for await (const item of gen) out.push(item);
  return out;
}

describe("parseSSE", () => {
  it("parses a simple event", async () => {
    const events = await collect(parseSSE(makeStream(["data: {\"x\":1}\n\n"])));
    expect(events).toEqual([{ x: 1 }]);
  });

  it("handles events split across chunks", async () => {
    const events = await collect(parseSSE(makeStream(["data: {\"x\":", "1}\n\n"])));
    expect(events).toEqual([{ x: 1 }]);
  });

  it("ignores malformed JSON", async () => {
    const events = await collect(parseSSE(makeStream(["data: not-json\n\ndata: {\"y\":2}\n\n"])));
    expect(events).toEqual([{ y: 2 }]);
  });

  it("tolerates whitespace around the colon", async () => {
    const events = await collect(parseSSE(makeStream(["data : {\"z\":3}\n\n"])));
    expect(events).toEqual([{ z: 3 }]);
  });
});
