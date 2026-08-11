"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";

const STORAGE_KEY = "isra-admin-key";

export function getAdminKey(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

/** Holds the key that unlocks re-ingest. A shared secret in a browser, not authentication. */
export function AdminKey() {
  const [key, setKey] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const existing = getAdminKey();
    setKey(existing);
    setSaved(Boolean(existing));
  }, []);

  const save = () => {
    try {
      if (key) localStorage.setItem(STORAGE_KEY, key);
      else localStorage.removeItem(STORAGE_KEY);
      setSaved(Boolean(key));
    } catch {
      // Private browsing with storage disabled: the key just won't persist.
    }
  };

  return (
    <div className="border border-line bg-panel p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="label">admin key</span>
        <span className="font-mono text-[10px] text-faint">
          {saved ? "key set" : "read-only"}
        </span>
      </div>
      <p className="mt-2 text-[12px] leading-relaxed text-muted">
        Reading the corpus is open to everyone. Re-ingesting rewrites it and runs
        the scrapers, so it needs the key. This is a speed bump, not
        authentication.
      </p>
      <div className="mt-3 flex gap-2">
        <input
          type="password"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="paste key"
          className="min-w-0 flex-1 border border-line bg-base px-3 py-2 font-mono text-[12px] text-ink placeholder:text-faint focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus/40"
        />
        <Button variant="primary" size="sm" onClick={save}>
          Save
        </Button>
      </div>
    </div>
  );
}
