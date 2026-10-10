import { useEffect, useState } from "react";
import { apiBlob, apiRequest } from "../lib/api";
import type { Evidence } from "../types";

type LoadedEvidence = Evidence & { objectUrl: string };

export function EvidenceGallery({
  assignmentId,
  token,
  compact = false,
}: {
  assignmentId: number;
  token: string | null;
  compact?: boolean;
}) {
  const [items, setItems] = useState<LoadedEvidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const objectUrls: string[] = [];

    async function load() {
      setLoading(true);
      setError("");
      try {
        const evidence = await apiRequest<Evidence[]>(
          `/evidence/assignments/${assignmentId}`,
          {},
          token,
        );

        const loaded = await Promise.all(
          evidence.map(async (item) => {
            const blob = await apiBlob(`/evidence/${item.id}/download`, token);
            const objectUrl = URL.createObjectURL(blob);
            objectUrls.push(objectUrl);
            return { ...item, objectUrl };
          }),
        );

        if (!cancelled) setItems(loaded);
      } catch {
        if (!cancelled) setError("Evidence could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();

    return () => {
      cancelled = true;
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [assignmentId, token]);

  if (loading) {
    return <p className="muted evidence-note">Loading evidence…</p>;
  }

  if (error) {
    return <p className="muted evidence-note">{error}</p>;
  }

  if (items.length === 0) {
    return <p className="muted evidence-note">No collection evidence has been uploaded.</p>;
  }

  return (
    <div className={compact ? "evidence-gallery compact" : "evidence-gallery"}>
      {items.map((item) => (
        <a
          key={item.id}
          href={item.objectUrl}
          target="_blank"
          rel="noreferrer"
          className="evidence-item"
          title="Open full image"
        >
          <img src={item.objectUrl} alt={item.original_filename} />
          <span>
            <strong>{item.original_filename}</strong>
            <small>{new Date(item.created_at).toLocaleString()}</small>
          </span>
        </a>
      ))}
    </div>
  );
}
