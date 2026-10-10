import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectionRequest,
  Complaint,
  Feedback,
} from "../types";

export function ResidentSupportPage() {
  const { token } = useAuth();
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [complaintRequestId, setComplaintRequestId] = useState("");
  const [category, setCategory] = useState("missed_collection");
  const [priority, setPriority] = useState("normal");
  const [description, setDescription] = useState("");

  const [feedbackRequestId, setFeedbackRequestId] = useState("");
  const [rating, setRating] = useState("5");
  const [comment, setComment] = useState("");

  const completedRequests = useMemo(
    () => requests.filter((request) => request.status === "completed"),
    [requests],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [requestData, complaintData, feedbackData] = await Promise.all([
        apiRequest<CollectionRequest[]>("/collection-requests", {}, token),
        apiRequest<Complaint[]>("/complaints/mine", {}, token),
        apiRequest<Feedback[]>("/feedback/mine", {}, token),
      ]);

      setRequests(requestData);
      setComplaints(complaintData);
      setFeedback(feedbackData);

      if (!feedbackRequestId) {
        const firstCompleted = requestData.find(
          (request) => request.status === "completed",
        );
        if (firstCompleted) setFeedbackRequestId(String(firstCompleted.id));
      }
    } catch {
      setError("Could not load support information.");
    } finally {
      setLoading(false);
    }
  }, [token, feedbackRequestId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function submitComplaint(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      await apiRequest<Complaint>(
        "/complaints",
        {
          method: "POST",
          body: JSON.stringify({
            request_id: complaintRequestId ? Number(complaintRequestId) : null,
            category,
            priority,
            description,
          }),
        },
        token,
      );
      setDescription("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit complaint.");
    } finally {
      setBusy(false);
    }
  }

  async function submitFeedback(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      await apiRequest<Feedback>(
        "/feedback",
        {
          method: "POST",
          body: JSON.stringify({
            request_id: Number(feedbackRequestId),
            rating: Number(rating),
            comment: comment || null,
          }),
        },
        token,
      );
      setComment("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit feedback.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Help & support</p>
          <h1>Complaints and service feedback</h1>
          <p className="muted">
            Report a service issue or rate a completed collection. Notifications are shown on your Dashboard.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="support-grid">
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Need help?</p>
              <h2>Submit a complaint</h2>
            </div>
          </div>

          <form className="form-stack" onSubmit={submitComplaint}>
            <label>
              Related request
              <select
                value={complaintRequestId}
                onChange={(event) => setComplaintRequestId(event.target.value)}
              >
                <option value="">General service issue</option>
                {requests.map((request) => (
                  <option key={request.id} value={request.id}>
                    #{request.id} · {request.pickup_address}
                  </option>
                ))}
              </select>
            </label>

            <div className="form-grid-two">
              <label>
                Category
                <select value={category} onChange={(event) => setCategory(event.target.value)}>
                  <option value="missed_collection">Missed collection</option>
                  <option value="late_collection">Late collection</option>
                  <option value="service_quality">Service quality</option>
                  <option value="billing">Billing</option>
                  <option value="other">Other</option>
                </select>
              </label>

              <label>
                Priority
                <select value={priority} onChange={(event) => setPriority(event.target.value)}>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </label>
            </div>

            <label>
              What happened?
              <textarea
                rows={5}
                required
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Describe the issue so the operations team can follow it up."
              />
            </label>

            <button className="button primary" disabled={busy}>
              Submit complaint
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Your experience</p>
              <h2>Rate completed collection</h2>
            </div>
          </div>

          {completedRequests.length === 0 ? (
            <StatePanel
              title="No completed collection to rate"
              message="Feedback becomes available after a collection is completed."
            />
          ) : (
            <form className="form-stack" onSubmit={submitFeedback}>
              <label>
                Completed request
                <select
                  required
                  value={feedbackRequestId}
                  onChange={(event) => setFeedbackRequestId(event.target.value)}
                >
                  <option value="">Select a request</option>
                  {completedRequests.map((request) => (
                    <option key={request.id} value={request.id}>
                      #{request.id} · {request.pickup_address}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Rating
                <select value={rating} onChange={(event) => setRating(event.target.value)}>
                  <option value="5">5 - Excellent</option>
                  <option value="4">4 - Good</option>
                  <option value="3">3 - Average</option>
                  <option value="2">2 - Poor</option>
                  <option value="1">1 - Very poor</option>
                </select>
              </label>

              <label>
                Comment
                <textarea
                  rows={4}
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="What went well, or what could we improve?"
                />
              </label>

              <button className="button primary" disabled={busy || !feedbackRequestId}>
                Submit feedback
              </button>
            </form>
          )}

          {feedback.length > 0 ? (
            <p className="muted section-spacer">Feedback submitted: {feedback.length}</p>
          ) : null}
        </section>
      </div>

      <section className="panel section-spacer">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Case history</p>
            <h2>Your complaints</h2>
          </div>
          <span className="status-badge">{complaints.length} total</span>
        </div>

        {loading ? (
          <StatePanel title="Loading complaints…" />
        ) : complaints.length === 0 ? (
          <StatePanel title="No complaints submitted" message="Any complaint you send will remain visible here with its resolution status." />
        ) : (
          <div className="list-stack">
            {complaints.map((complaint) => (
              <article className="list-card support-case-card" key={complaint.id}>
                <div className="section-heading">
                  <div>
                    <strong>Complaint #{complaint.id}</strong>
                    <p className="muted">{complaint.category.replaceAll("_", " ")} · {complaint.priority} priority</p>
                  </div>
                  <span className={`status-badge status-${complaint.status}`}>{complaint.status}</span>
                </div>
                <p>{complaint.description}</p>
                {complaint.resolution ? (
                  <div className="case-resolution">
                    <strong>Resolution</strong>
                    <p>{complaint.resolution}</p>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
