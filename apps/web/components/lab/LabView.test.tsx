import { act, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LabView } from "./LabView";

/**
 * What this page has to get right is the reading, not the fetching: which column
 * a stage lands in, what each result moved relative to the stage it is supposed
 * to improve on, and that a truncated list is not mistaken for a shrinking one.
 *
 * The settings store is stubbed rather than wrapped in a provider, because top_k
 * is incidental here and a real provider would make every test depend on it.
 */
vi.mock("@/lib/store/settings", () => ({
  useSettings: () => ({ topK: 5, setTopK: () => {} }),
}));

interface Hit {
  id: number;
  name: string;
  score: number;
}

function chunk({ id, name, score }: Hit) {
  return {
    id,
    startup_name: name,
    chunk_index: 0,
    text: `${name} does something.`,
    source_url: "https://example.com",
    score,
  };
}

function stageEvent(name: string, elapsed: number, total: number, hits: Hit[]) {
  return `data: ${JSON.stringify({
    type: "stage",
    name,
    elapsed_ms: elapsed,
    total,
    results: hits.map(chunk),
  })}\n\n`;
}

function controllableStream() {
  let push!: (chunk: string) => void;
  let close!: () => void;
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      const encoder = new TextEncoder();
      push = (c: string) => controller.enqueue(encoder.encode(c));
      close = () => controller.close();
    },
  });
  return { body, push, close };
}

function stubStream() {
  const stream = controllableStream();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, status: 200, body: stream.body }),
  );
  return stream;
}

/** Click the first example query, which runs it in one click. */
async function runFirstExample() {
  const example = screen.getByRole("button", {
    name: /Which Indian startup builds electric scooters/i,
  });
  await act(async () => {
    example.click();
  });
}

function column(title: RegExp) {
  // Each column's heading is unique, so walk up from it to the card.
  const heading = screen.getByText(title);
  const card = heading.closest("div.overflow-hidden");
  if (!card) throw new Error("column card not found");
  return card as HTMLElement;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("LabView", () => {
  it("offers example queries before anything has been run", () => {
    stubStream();
    render(<LabView />);
    expect(screen.getByText("Watch the pipeline resolve")).toBeInTheDocument();
    expect(screen.getByText("try one")).toBeInTheDocument();
  });

  it("shows the stages that have landed and marks the rest as not yet run", async () => {
    const stream = stubStream();
    render(<LabView />);
    await runFirstExample();

    await act(async () => {
      stream.push(stageEvent("vector", 20, 100, [{ id: 1, name: "Ola", score: 0.7 }]));
    });

    await waitFor(() => expect(screen.getByText(/1\. Vector search/i)).toBeInTheDocument());
    // The one being worked on says so; the ones after it are queued.
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getAllByText("queued")).toHaveLength(2);
    expect(screen.getByText("20ms")).toBeInTheDocument();
  });

  it("states how many candidates a stage produced, not just how many it shows", async () => {
    const stream = stubStream();
    render(<LabView />);
    await runFirstExample();

    await act(async () => {
      stream.push(stageEvent("vector", 20, 100, [{ id: 1, name: "Ola", score: 0.7 }]));
      stream.push(stageEvent("keyword", 24, 14, [{ id: 2, name: "Ather", score: 1.4 }]));
    });

    // Truncated for display -- the count keeps that legible.
    await waitFor(() => expect(screen.getByText(/1 of 100/)).toBeInTheDocument());
    expect(screen.getByText(/1 of 14/)).toBeInTheDocument();
  });

  it("says 'kept' when a stage selected rather than truncated", async () => {
    // The rerank column returns exactly what it chose, so "5 of 5" would read as
    // though something had been cut.
    const stream = stubStream();
    render(<LabView />);
    await runFirstExample();

    await act(async () => {
      stream.push(stageEvent("vector", 20, 100, [{ id: 1, name: "Ola", score: 0.7 }]));
      stream.push(stageEvent("keyword", 24, 14, [{ id: 1, name: "Ola", score: 1.4 }]));
      stream.push(stageEvent("fusion", 25, 100, [{ id: 1, name: "Ola", score: 0.03 }]));
      stream.push(stageEvent("rerank", 700, 1, [{ id: 1, name: "Ola", score: 0.9 }]));
    });

    await waitFor(() => expect(screen.getByText(/1 kept/)).toBeInTheDocument());
  });

  it("marks a result the keyword search found and vector search missed", async () => {
    // Those are exactly the chunks with the power to displace a correct one in
    // fusion, which is the project's least comfortable eval result.
    const stream = stubStream();
    render(<LabView />);
    await runFirstExample();

    await act(async () => {
      stream.push(stageEvent("vector", 20, 100, [{ id: 1, name: "Ola", score: 0.7 }]));
      stream.push(stageEvent("keyword", 24, 14, [{ id: 9, name: "Newcomer", score: 1.4 }]));
    });

    await waitFor(() => {
      expect(within(column(/2\. Keyword search/i)).getByText("new")).toBeInTheDocument();
    });
    // The baseline it is measured against is named, so the reader is not guessing.
    expect(within(column(/2\. Keyword search/i)).getByText(/vs vector/i)).toBeInTheDocument();
  });

  it("shows how far each result moved at the stage that moved it", async () => {
    const stream = stubStream();
    render(<LabView />);
    await runFirstExample();

    await act(async () => {
      // Vector order: A, B. Fusion order: B, A -- so B rose one and A fell one.
      stream.push(
        stageEvent("vector", 20, 100, [
          { id: 1, name: "Alpha", score: 0.7 },
          { id: 2, name: "Beta", score: 0.6 },
        ]),
      );
      stream.push(stageEvent("keyword", 24, 14, [{ id: 2, name: "Beta", score: 1.4 }]));
      stream.push(
        stageEvent("fusion", 25, 100, [
          { id: 2, name: "Beta", score: 0.03 },
          { id: 1, name: "Alpha", score: 0.02 },
        ]),
      );
    });

    await waitFor(() => {
      const fusion = within(column(/3\. RRF fusion/i));
      expect(fusion.getByTitle(/Moved up 1 place at this stage/)).toBeInTheDocument();
      expect(fusion.getByTitle(/Pushed down 1 place at this stage/)).toBeInTheDocument();
    });
  });

  it("leaves the first stage without movement, having nothing to move from", async () => {
    const stream = stubStream();
    render(<LabView />);
    await runFirstExample();

    await act(async () => {
      stream.push(stageEvent("vector", 20, 100, [{ id: 1, name: "Ola", score: 0.7 }]));
    });

    await waitFor(() => expect(screen.getByText(/1 of 100/)).toBeInTheDocument());
    const vector = column(/1\. Vector search/i);
    expect(within(vector).queryByText(/^vs /i)).not.toBeInTheDocument();
    expect(within(vector).queryByText("new")).not.toBeInTheDocument();
  });

  it("reports a failure instead of leaving the columns waiting forever", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 429,
        body: null,
        text: async () => JSON.stringify({ error: "Rate limit exceeded" }),
      }),
    );
    render(<LabView />);
    await runFirstExample();

    await waitFor(() => expect(screen.getByText("Retrieval failed")).toBeInTheDocument());
    expect(screen.getByText("Rate limit exceeded")).toBeInTheDocument();
  });
});
