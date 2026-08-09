import { AdminKey } from "@/components/ingest/AdminKey";
import { IngestView } from "@/components/ingest/IngestView";

export default function IngestPage() {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-line p-4">
        <AdminKey />
      </div>
      <div className="min-h-0 flex-1">
        <IngestView />
      </div>
    </div>
  );
}
