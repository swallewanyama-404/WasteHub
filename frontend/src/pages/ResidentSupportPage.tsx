import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectionRequest,
  Complaint,
  Feedback,
  Notification,
} from "../types";

export function ResidentSupportPage() {
  const { token } = useAuth();
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
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
      const [requestData, complaintData, feedbackData, notificationData] =
        await Promise.all([
          apiRequest<CollectionRequest[]>("/collection-requests", {}, token),
          apiRequest<Complaint[]>("/complaints/mine", {}, token),
          apiRequest<Feedback[]>("/feedback/mine", {}, token),
          apiRequest<Notification[]>("/notifications", {}, token),
        ]);

      setRequests(requestData);
      setComplaints(complaintData);
      setFeedback(feedbackData);
      setNotifications(notificationData);

      if (!feedbackRequestId && completedRequests.length === 0) {
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
  }, [token, feedbackRequestId, completedRequests.length]);

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
      setError(
        err instanceof ApiError ? err.message : "Could not submit complaint.",
      );
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
      setError(
        err instanceof ApiError ? err.message : "Could not submit feedback.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function markRead(notificationId: number) {
    await apiRequest(
      `/notifications/${notificationId}/read`,
      { method: "POST" },
      token,
    );
    await load();
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Resident support</p>
          <h1>Feedback, complaints & notifications</h1>
          <p className="muted">
            Keep a record of service issues and follow WasteHub updates.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="two-column-grid">
        <section className="panel">
          <h2>Submit a complaint</h2>
          <form className="form-stack" onSubmit={submitComplaint}>
            <label>
              Related request
              <select
                value={complaintRequestId}
                onChange={(event) => setComplaintRequestId(event.target.value)}
              >
                <option value="">General complaint</option>
                {requests.map((request) => (
                  <option key={request.id} value={request.id}>
                    #{request.id} · {request.pickup_address}
                  </option>
                ))}
              </select>
            </label>
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
            <label>
              Description
              <textarea
                rows={4}
                required
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </label>
            <button className="button primary" disabled={busy}>
              Submit complaint
            </button>
          </form>

          <div className="section-spacer" />

          <h2>Your complaints</h2>
          {loading ? (
            <StatePanel title="Loading complaints…" />
          ) : complaints.length === 0 ? (
            <StatePanel title="No complaints" />
          ) : (
            <div className="list-stack">
              {complaints.map((complaint) => (
                <article className="list-card" key={complaint.id}>
                  <div className="section-heading">
                    <strong>Complaint #{complaint.id}</strong>
                    <span className="status-badge">{complaint.status}</span>
                  </div>
                  <p>{complaint.description}</p>
                  {complaint.resolution ? (
                    <p className="success-text">Resolution: {complaint.resolution}</p>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </section>

        <div className="page-stack">
          <section className="panel">
            <h2>Rate completed collection</h2>
            {completedRequests.length === 0 ? (
              <StatePanel
                title="No completed request available"
                message="Feedback can be submitted after a collection is completed."
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
                    rows={3}
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                  />
                </label>
                <button className="button primary" disabled={busy || !feedbackRequestId}>
                  Submit feedback
                </button>
              </form>
            )}

            {feedback.length > 0 ? (
              <p className="muted section-spacer">
                Feedback submitted: {feedback.length}
              </p>
            ) : null}
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Notifications</h2>
              <span className="status-badge">
                {notifications.filter((item) => !item.is_read).length} unread
              </span>
            </div>

            {notifications.length === 0 ? (
              <StatePanel title="No notifications yet" />
            ) : (
              <div className="list-stack">
                {notifications.map((notification) => (
                  <article
                    className={notification.is_read ? "list-card" : "list-card unread-card"}
                    key={notification.id}
                  >
                    <strong>{notification.title}</strong>
                    <p>{notification.message}</p>
                    <div className="section-heading">
                      <span className="muted">
                        {new Date(notification.created_at).toLocaleString()}
                      </span>
                      {!notification.is_read ? (
                        <button
                          className="button secondary"
                          onClick={() => void markRead(notification.id)}
                        >
                          Mark read
                        </button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}
