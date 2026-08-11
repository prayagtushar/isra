import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StartupsView } from "./StartupsView";

/** Two defects worth pinning: a hundred rows reported as the total, and seventy chips in alphabetical order. */

// The detail drawer reaches for the router and conversation store, neither of which exists in jsdom.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: () => {} }),
  usePathname: () => "/startups",
}));
vi.mock("@/lib/store/conversations", () => ({
  useConversations: () => ({ newConversation: () => {} }),
}));

function startup(id: number, name: string, sectors: string[], extra = {}) {
  return {
    id,
    name,
    normalized_name: name.toLowerCase(),
    one_liner: null,
    description: `${name} is an Indian startup.`,
    sectors,
    tags: [],
    founders: ["Someone"],
    founded_year: null,
    headquarters: null,
    fundings: null,
    source_url: "https://en.wikipedia.org/wiki/X",
    ...extra,
  };
}

/** 14 distinct sectors, so the twelve-chip cap has something to hide. */
function corpus() {
  const rows = [
    startup(1, "Alpha", ["Financial Technology"]),
    startup(2, "Bravo", ["Financial Technology"]),
    startup(3, "Charlie", ["Financial Technology"]),
    startup(4, "Delta", ["Healthcare"]),
    startup(5, "Echo", ["Healthcare"]),
  ];
  // One company each, alphabetically ahead of the big ones.
  const singles = [
    "Adware",
    "Agriculture",
    "Backup",
    "Blockchain",
    "Cryptocurrency",
    "Diagnostics",
    "Energy",
    "Hospitality",
    "Insurance",
    "Marketplace",
    "Retail",
    "Web3",
  ];
  singles.forEach((sector, i) => rows.push(startup(100 + i, `Solo${i}`, [sector])));
  return rows;
}

function mockCorpus(rows: ReturnType<typeof corpus>, total = rows.length) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ total, startups: rows }),
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("StartupsView", () => {
  it("requests the whole corpus, not one page of it", async () => {
    const fetchMock = mockCorpus(corpus());
    await act(async () => {
      render(<StartupsView />);
    });

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const url = String(fetchMock.mock.calls[0][0]);
    // It asked for 100 before, which silently hid everything past the hundredth.
    const limit = Number(new URL(url, "http://localhost").searchParams.get("limit"));
    expect(limit).toBeGreaterThanOrEqual(200);
  });

  it("orders sector chips by how many companies they hold", async () => {
    mockCorpus(corpus());
    await act(async () => {
      render(<StartupsView />);
    });

    await waitFor(() => expect(screen.getByText(/17 startups/i)).toBeInTheDocument());

    // Chips are uppercased in CSS, so the text nodes keep the canonical case.
    const chips = screen.getAllByRole("button").map((b) => b.textContent ?? "");
    const financial = chips.findIndex((t) => t.includes("Financial Technology"));
    const adware = chips.findIndex((t) => t.includes("Adware"));
    expect(financial).toBeGreaterThan(-1);
    expect(financial).toBeLessThan(adware === -1 ? Number.MAX_SAFE_INTEGER : adware);
    expect(chips.some((t) => /Financial Technology\s*3/.test(t))).toBe(true);
  });

  it("hides the long tail of sectors behind an expander", async () => {
    mockCorpus(corpus());
    await act(async () => {
      render(<StartupsView />);
    });

    await waitFor(() => expect(screen.getByText(/All 14 sectors/i)).toBeInTheDocument());

    await act(async () => {
      screen.getByText(/All 14 sectors/i).click();
    });
    expect(screen.getByText(/Fewer sectors/i)).toBeInTheDocument();
  });

  it("keeps the selected sector visible even when the list is collapsed", async () => {
    // Filtering by a chip that then disappears leaves the reader unable to clear it.
    mockCorpus(corpus());
    await act(async () => {
      render(<StartupsView />);
    });
    await waitFor(() => expect(screen.getByText(/All 14 sectors/i)).toBeInTheDocument());

    await act(async () => {
      screen.getByText(/All 14 sectors/i).click();
    });
    // Scoped to the filter row: the company's card carries the same sector as a tag.
    const chip = () =>
      screen.getAllByRole("button").find((b) => /^Web3/.test(b.textContent ?? ""));
    const tailChip = chip();
    expect(tailChip).toBeDefined();
    await act(async () => {
      tailChip!.click();
    });
    await act(async () => {
      screen.getByText(/Fewer sectors/i).click();
    });

    expect(chip()).toBeDefined();
    // The count label is several text nodes, so match the element's whole text.
    expect(
      screen.getByText(
        (_content, el) =>
          el?.tagName === "P" && /1\s+Web3\s+·\s+startup/.test(el.textContent ?? ""),
      ),
    ).toBeInTheDocument();
  });

  it("falls back to the description for a company with no one-liner", async () => {
    // Only YC records carry a one_liner, so more than half the grid was a bare name.
    mockCorpus([startup(1, "Zepto", ["Quick-Commerce"], { one_liner: null })]);
    await act(async () => {
      render(<StartupsView />);
    });

    await waitFor(() =>
      expect(screen.getByText("Zepto is an Indian startup.")).toBeInTheDocument(),
    );
  });

  it("prefers the one-liner when there is one", async () => {
    mockCorpus([
      startup(1, "Razorpay", ["Payments"], { one_liner: "Payments for businesses" }),
    ]);
    await act(async () => {
      render(<StartupsView />);
    });

    await waitFor(() =>
      expect(screen.getByText("Payments for businesses")).toBeInTheDocument(),
    );
  });

  it("says the corpus is empty rather than showing a bare grid", async () => {
    mockCorpus([], 0);
    await act(async () => {
      render(<StartupsView />);
    });

    await waitFor(() => expect(screen.getByText("No startups found")).toBeInTheDocument());
  });
});
