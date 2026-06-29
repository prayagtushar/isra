import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ChatInput } from "./ChatInput";

describe("ChatInput", () => {
  it("sends on button click", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} onStop={() => {}} isStreaming={false} autoFocusOnMount={false} />);
    const input = screen.getByPlaceholderText("Ask about an Indian startup…");
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.click(screen.getByLabelText("Send message"));
    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("sends on Enter and inserts newline on Shift+Enter", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} onStop={() => {}} isStreaming={false} autoFocusOnMount={false} />);
    const input = screen.getByPlaceholderText("Ask about an Indian startup…");
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalledWith("hello");

    fireEvent.change(input, { target: { value: "line" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("calls onStop when streaming", () => {
    const onStop = vi.fn();
    render(<ChatInput onSend={() => {}} onStop={onStop} isStreaming={true} autoFocusOnMount={false} />);
    fireEvent.click(screen.getByLabelText("Stop generating"));
    expect(onStop).toHaveBeenCalled();
  });

  it("does not send empty input", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} onStop={() => {}} isStreaming={false} autoFocusOnMount={false} />);
    fireEvent.click(screen.getByLabelText("Send message"));
    expect(onSend).not.toHaveBeenCalled();
  });
});
