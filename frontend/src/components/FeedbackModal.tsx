import { useId, useState, type FormEvent } from "react";
import type { FeedbackCategory } from "../api/types";

const categories: Array<{ value: FeedbackCategory; label: string }> = [
  { value: "bug", label: "Bug" },
  { value: "idea", label: "Idea" },
  { value: "question", label: "Question" },
  { value: "other", label: "Other" },
];

interface FeedbackModalProps {
  isOpen: boolean;
  disabled: boolean;
  statusMessage: string | null;
  errorMessage: string | null;
  onClose: () => void;
  onSubmit: (payload: { category: FeedbackCategory; message: string }) => Promise<void>;
}

export default function FeedbackModal({
  isOpen,
  disabled,
  statusMessage,
  errorMessage,
  onClose,
  onSubmit,
}: FeedbackModalProps) {
  const titleId = useId();
  const [category, setCategory] = useState<FeedbackCategory>("idea");
  const [message, setMessage] = useState("");

  if (!isOpen) return null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({ category, message });
    setMessage("");
    setCategory("idea");
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="feedback-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className="feedback-modal-header">
          <div>
            <span className="eyebrow">Feedback</span>
            <h2 id={titleId}>Send feedback</h2>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            Close
          </button>
        </div>

        {statusMessage ? <div className="form-success">{statusMessage}</div> : null}
        {errorMessage ? <div className="form-error">{errorMessage}</div> : null}

        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            Category
            <select value={category} onChange={(event) => setCategory(event.target.value as FeedbackCategory)}>
              {categories.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Message
            <textarea
              value={message}
              minLength={10}
              maxLength={2000}
              rows={5}
              required
              onChange={(event) => setMessage(event.target.value)}
            />
          </label>

          <div className="feedback-modal-actions">
            <span>{message.length}/2000</span>
            <button type="submit" className="primary-button" disabled={disabled || message.trim().length < 10}>
              {disabled ? "Sending..." : "Send feedback"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
