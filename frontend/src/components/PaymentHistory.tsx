import { FormEvent, useMemo, useState } from "react";
import type {
  PaymentRecord,
  PaymentRecordCreatePayload,
  PaymentRecordStatus,
  PaymentRecordUpdatePayload,
  Project,
} from "../api/types";
import { classNames, formatDate } from "../utils/format";

interface PaymentHistoryProps {
  project: Project;
  disabled: boolean;
  onCreatePaymentRecord: (projectId: number, payload: PaymentRecordCreatePayload) => Promise<void>;
  onUpdatePaymentRecord: (
    projectId: number,
    paymentRecordId: number,
    payload: PaymentRecordUpdatePayload,
  ) => Promise<void>;
  onDeletePaymentRecord: (projectId: number, paymentRecordId: number) => Promise<void>;
}

interface PaymentRecordFormProps {
  projectCurrency: string;
  disabled: boolean;
  submitLabel: string;
  paymentRecord?: PaymentRecord;
  onSubmit: (payload: PaymentRecordCreatePayload) => Promise<void>;
  onCancel: () => void;
}

const paymentStatuses: PaymentRecordStatus[] = ["pending", "paid", "failed", "cancelled"];
const paymentCurrencies = ["USD", "EUR", "GBP", "RON"];

function optionLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function amountToInput(value: PaymentRecord["amount"] | null): string {
  if (value === null) return "";
  return Number(value).toString();
}

function dateTimeToInput(value: string | null): string {
  if (!value) return "";
  return value.slice(0, 16);
}

function optionalInvoiceId(value: string): number | null {
  if (value.trim() === "") return null;
  const numericValue = Number(value);
  return Number.isInteger(numericValue) && numericValue > 0 ? numericValue : null;
}

function formatPaymentAmount(value: PaymentRecord["amount"] | number | null, currency: string): string {
  if (value === null) return "No amount";
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(Number(value));
  } catch {
    return `${Number(value).toFixed(2)} ${currency}`;
  }
}

function formatDateTime(value: string | null): string {
  if (!value) return "No date";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function PaymentRecordForm({
  projectCurrency,
  disabled,
  submitLabel,
  paymentRecord,
  onSubmit,
  onCancel,
}: PaymentRecordFormProps) {
  const [amount, setAmount] = useState(amountToInput(paymentRecord?.amount ?? null));
  const [currency, setCurrency] = useState(paymentRecord?.currency ?? projectCurrency);
  const [status, setStatus] = useState<PaymentRecordStatus>(paymentRecord?.status ?? "pending");
  const [method, setMethod] = useState(paymentRecord?.method ?? "");
  const [paidAt, setPaidAt] = useState(dateTimeToInput(paymentRecord?.paid_at ?? null));
  const [dueDate, setDueDate] = useState(paymentRecord?.due_date ?? "");
  const [periodStart, setPeriodStart] = useState(paymentRecord?.period_start ?? "");
  const [periodEnd, setPeriodEnd] = useState(paymentRecord?.period_end ?? "");
  const [notes, setNotes] = useState(paymentRecord?.notes ?? "");
  const [invoiceId, setInvoiceId] = useState(paymentRecord?.invoice_id ? String(paymentRecord.invoice_id) : "");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const numericAmount = Number(amount);
    await onSubmit({
      amount: Number.isFinite(numericAmount) ? numericAmount : 0,
      currency: currency.trim().toUpperCase() || projectCurrency,
      status,
      method: method.trim() || null,
      paid_at: paidAt || null,
      due_date: dueDate || null,
      period_start: periodStart || null,
      period_end: periodEnd || null,
      notes: notes.trim() || null,
      invoice_id: optionalInvoiceId(invoiceId),
    });
  }

  return (
    <form className="payment-record-form" onSubmit={submit}>
      <div className="four-column-form">
        <label>
          Amount
          <input
            type="number"
            min={0.01}
            step={0.01}
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            required
            disabled={disabled}
          />
        </label>
        <label>
          Currency
          <select value={currency} onChange={(event) => setCurrency(event.target.value)} disabled={disabled}>
            {paymentCurrencies.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={status} onChange={(event) => setStatus(event.target.value as PaymentRecordStatus)} disabled={disabled}>
            {paymentStatuses.map((item) => (
              <option key={item} value={item}>
                {optionLabel(item)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Method
          <input value={method} onChange={(event) => setMethod(event.target.value)} disabled={disabled} />
        </label>
      </div>

      <div className="four-column-form">
        <label>
          Due date
          <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} disabled={disabled} />
        </label>
        <label>
          Paid at
          <input
            type="datetime-local"
            value={paidAt}
            onChange={(event) => setPaidAt(event.target.value)}
            disabled={disabled}
          />
        </label>
        <label>
          Period start
          <input
            type="date"
            value={periodStart}
            onChange={(event) => setPeriodStart(event.target.value)}
            disabled={disabled}
          />
        </label>
        <label>
          Period end
          <input type="date" value={periodEnd} onChange={(event) => setPeriodEnd(event.target.value)} disabled={disabled} />
        </label>
      </div>

      <div className="two-column-form">
        <label>
          Invoice
          <input
            type="number"
            min={1}
            step={1}
            value={invoiceId}
            onChange={(event) => setInvoiceId(event.target.value)}
            disabled={disabled}
          />
        </label>
        <label>
          Notes
          <input value={notes} onChange={(event) => setNotes(event.target.value)} disabled={disabled} />
        </label>
      </div>

      <div className="inline-form-actions">
        <button type="submit" className="small-button" disabled={disabled}>
          {submitLabel}
        </button>
        <button type="button" className="small-secondary-button" disabled={disabled} onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function PaymentHistory({
  project,
  disabled,
  onCreatePaymentRecord,
  onUpdatePaymentRecord,
  onDeletePaymentRecord,
}: PaymentHistoryProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingPaymentRecordId, setEditingPaymentRecordId] = useState<number | null>(null);
  const sortedPaymentRecords = useMemo(
    () =>
      [...project.payment_records].sort((first, second) => {
        const firstDate = first.due_date ?? "9999-12-31";
        const secondDate = second.due_date ?? "9999-12-31";
        return firstDate.localeCompare(secondDate) || first.id - second.id;
      }),
    [project.payment_records],
  );
  const paidTotal = sortedPaymentRecords.reduce(
    (total, paymentRecord) => total + (paymentRecord.status === "paid" ? Number(paymentRecord.amount) : 0),
    0,
  );
  const pendingTotal = sortedPaymentRecords.reduce(
    (total, paymentRecord) =>
      total + (paymentRecord.status !== "paid" && paymentRecord.status !== "cancelled" ? Number(paymentRecord.amount) : 0),
    0,
  );
  const hasRecords = sortedPaymentRecords.length > 0;

  return (
    <section className="payment-history">
      <div className="payment-history-header">
        <div>
          <strong>Payment history</strong>
          {hasRecords ? (
            <span>
              {sortedPaymentRecords.length} records | {formatPaymentAmount(paidTotal, project.currency)} paid |{" "}
              {formatPaymentAmount(pendingTotal, project.currency)} open
            </span>
          ) : (
            <span>No records tracked yet</span>
          )}
        </div>
        <button
          type="button"
          className="small-secondary-button"
          disabled={disabled}
          onClick={() => {
            setIsAdding((current) => !current);
            setEditingPaymentRecordId(null);
          }}
        >
          {isAdding ? "Close" : "Add payment"}
        </button>
      </div>

      {isAdding ? (
        <PaymentRecordForm
          projectCurrency={project.currency}
          disabled={disabled}
          submitLabel="Add payment"
          onCancel={() => setIsAdding(false)}
          onSubmit={async (payload) => {
            await onCreatePaymentRecord(project.id, payload);
            setIsAdding(false);
          }}
        />
      ) : null}

      <div className="payment-record-list">
        {!hasRecords ? <p className="muted">No payment records yet.</p> : null}
        {sortedPaymentRecords.map((paymentRecord) => {
          const isEditing = editingPaymentRecordId === paymentRecord.id;

          return (
            <article className="payment-record-row" key={paymentRecord.id}>
              <div className="payment-record-main">
                <span className={classNames("payment-pill", paymentRecord.is_overdue ? "overdue" : paymentRecord.status)}>
                  {paymentRecord.is_overdue ? "Overdue" : optionLabel(paymentRecord.status)}
                </span>
                <strong>{formatPaymentAmount(paymentRecord.amount, paymentRecord.currency)}</strong>
                <span>Due {formatDate(paymentRecord.due_date)}</span>
                {paymentRecord.paid_at ? <span>Paid {formatDateTime(paymentRecord.paid_at)}</span> : null}
                {paymentRecord.method ? <span>{paymentRecord.method}</span> : null}
              </div>
              {paymentRecord.period_start || paymentRecord.period_end ? (
                <p>
                  Period {formatDate(paymentRecord.period_start)} to {formatDate(paymentRecord.period_end)}
                </p>
              ) : null}
              {paymentRecord.notes ? <p>{paymentRecord.notes}</p> : null}
              {isEditing ? (
                <PaymentRecordForm
                  key={paymentRecord.id}
                  projectCurrency={project.currency}
                  disabled={disabled}
                  submitLabel="Save payment"
                  paymentRecord={paymentRecord}
                  onCancel={() => setEditingPaymentRecordId(null)}
                  onSubmit={async (payload) => {
                    await onUpdatePaymentRecord(project.id, paymentRecord.id, payload);
                    setEditingPaymentRecordId(null);
                  }}
                />
              ) : null}
              <div className="inline-form-actions">
                <button
                  type="button"
                  className="small-secondary-button"
                  disabled={disabled}
                  onClick={() => {
                    setEditingPaymentRecordId((current) => (current === paymentRecord.id ? null : paymentRecord.id));
                    setIsAdding(false);
                  }}
                >
                  {isEditing ? "Close edit" : "Edit"}
                </button>
                <button
                  type="button"
                  className="small-danger-button"
                  disabled={disabled}
                  onClick={() => onDeletePaymentRecord(project.id, paymentRecord.id)}
                >
                  Delete
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
