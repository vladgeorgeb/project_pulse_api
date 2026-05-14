import { FormEvent, useMemo, useState } from "react";
import type { PaymentMethod, PaymentRecord, PaymentRecordCreatePayload, PaymentRecordStatus, PaymentRecordUpdatePayload, Project } from "../api/types";
import { classNames, formatDate } from "../utils/format";

interface PaymentHistoryProps {
  project: Project;
  disabled: boolean;
  onCreatePaymentRecord: (projectId: number, payload: PaymentRecordCreatePayload) => Promise<void>;
  onUpdatePaymentRecord: (projectId: number, paymentRecordId: number, payload: PaymentRecordUpdatePayload) => Promise<void>;
  onDeletePaymentRecord: (projectId: number, paymentRecordId: number) => Promise<void>;
}

interface PaymentRecordFormProps {
  project: Project;
  disabled: boolean;
  submitLabel: string;
  paymentRecord?: PaymentRecord;
  onSubmit: (payload: PaymentRecordCreatePayload) => Promise<void>;
  onCancel: () => void;
}

const paymentStatuses: PaymentRecordStatus[] = ["pending", "paid", "cancelled"];
const paymentMethods: PaymentMethod[] = ["wire", "bank_transfer", "card", "cash", "other"];
const paymentCurrencies = ["USD", "EUR", "GBP", "RON"];

function centsToInput(value: number | null): string {
  if (value === null) return "";
  return (value / 100).toFixed(2);
}

function dateTimeToInput(value: string | null | undefined): string {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  const local = new Date(parsed.getTime() - parsed.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function inputToCents(value: string): number {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.round(numeric * 100);
}

function formatPaymentAmount(valueCents: number | null, currency: string): string {
  if (valueCents === null) return "No amount";
  return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 2 }).format(valueCents / 100);
}

function nowLocalDateTimeInput(): string {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "No date";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "No date";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(parsed);
}

function getAmountCents(record: PaymentRecord): number {
  return typeof record.amount_cents === "number" && Number.isFinite(record.amount_cents) ? record.amount_cents : 0;
}

function isPeriodBasedContract(project: Project): boolean {
  return project.contract_type === "hourly" || project.contract_type === "monthly_retainer";
}

function PaymentRecordForm({ project, disabled, submitLabel, paymentRecord, onSubmit, onCancel }: PaymentRecordFormProps) {
  const [amount, setAmount] = useState(centsToInput(paymentRecord?.amount_cents ?? null));
  const [currency, setCurrency] = useState(paymentRecord?.currency ?? project.billing_currency);
  const [status, setStatus] = useState<PaymentRecordStatus>(paymentRecord?.status ?? "paid");
  const [method, setMethod] = useState<PaymentMethod | "">(paymentRecord?.method ?? "");
  const [paidAt, setPaidAt] = useState(dateTimeToInput(paymentRecord?.paid_at) || nowLocalDateTimeInput());
  const [dueDate, setDueDate] = useState(paymentRecord?.due_date ?? "");
  const [periodStart, setPeriodStart] = useState(paymentRecord?.period_start ?? "");
  const [periodEnd, setPeriodEnd] = useState(paymentRecord?.period_end ?? "");
  const [notes, setNotes] = useState(paymentRecord?.notes ?? "");
  const showPeriod = isPeriodBasedContract(project);
  const isPaid = status === "paid";
  const isPending = status === "pending";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      amount_cents: inputToCents(amount),
      currency: currency.trim().toUpperCase() || project.billing_currency,
      status,
      method: method || null,
      paid_at: isPaid ? (paidAt || nowLocalDateTimeInput()) : null,
      due_date: isPending ? dueDate || null : null,
      period_start: showPeriod ? periodStart || null : null,
      period_end: showPeriod ? periodEnd || null : null,
      notes: notes.trim() || null,
    });
  }

  return (
    <form className="payment-record-form" onSubmit={submit}>
      <div className="four-column-form">
        <label>Amount ({currency})<input type="number" min={0.01} step={0.01} value={amount} onChange={(event) => setAmount(event.target.value)} required disabled={disabled} /></label>
        <label>Billing currency<select value={currency} onChange={(event) => setCurrency(event.target.value)} disabled={disabled}>{paymentCurrencies.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Status<select value={status} onChange={(event) => setStatus(event.target.value as PaymentRecordStatus)} disabled={disabled}>{paymentStatuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Method<select value={method} onChange={(event) => setMethod(event.target.value as PaymentMethod)} disabled={disabled}><option value="">Select</option>{paymentMethods.map((item) => <option key={item} value={item}>{item.replace("_", " ")}</option>)}</select></label>
      </div>

      <div className="four-column-form">
        {isPending ? <label>Expected payment date<input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} disabled={disabled} required /></label> : <div />}
        {isPaid ? <label>Payment received date<input type="datetime-local" value={paidAt} onChange={(event) => setPaidAt(event.target.value)} disabled={disabled} required /></label> : <div />}
        {showPeriod ? <label>Work period start<input type="date" value={periodStart} onChange={(event) => setPeriodStart(event.target.value)} disabled={disabled} /></label> : <div />}
        {showPeriod ? <label>Work period end<input type="date" value={periodEnd} onChange={(event) => setPeriodEnd(event.target.value)} disabled={disabled} /></label> : <div />}
      </div>

      <label>Notes<input value={notes} onChange={(event) => setNotes(event.target.value)} disabled={disabled} /></label>
      <div className="inline-form-actions">
        <button type="submit" className="small-button" disabled={disabled}>{submitLabel}</button>
        <button type="button" className="small-secondary-button" disabled={disabled} onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

export default function PaymentHistory({ project, disabled, onCreatePaymentRecord, onUpdatePaymentRecord, onDeletePaymentRecord }: PaymentHistoryProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingPaymentRecordId, setEditingPaymentRecordId] = useState<number | null>(null);
  const sortedPaymentRecords = useMemo(
    () => [...project.payment_records].sort((first, second) => (first.due_date ?? "9999-12-31").localeCompare(second.due_date ?? "9999-12-31") || first.id - second.id),
    [project.payment_records],
  );
  const paidTotalCents = sortedPaymentRecords.reduce((total, record) => total + (record.status === "paid" ? getAmountCents(record) : 0), 0);
  const pendingTotalCents = sortedPaymentRecords.reduce((total, record) => total + (record.status === "pending" ? getAmountCents(record) : 0), 0);
  const overdueCount = sortedPaymentRecords.filter((record) => record.is_overdue).length;

  return (
    <section className="payment-history">
      <div className="payment-history-header">
        <div>
          <strong>Payments</strong>
          <div className="payment-summary-row" aria-label="Payment summary">
            <span>{sortedPaymentRecords.length} records</span>
            <span className="payment-summary-paid">{formatPaymentAmount(paidTotalCents, project.billing_currency)} paid</span>
            <span className={classNames("payment-summary-pending", pendingTotalCents > 0 ? "has-pending" : undefined)}>
              {formatPaymentAmount(pendingTotalCents, project.billing_currency)} pending
            </span>
            {overdueCount > 0 ? <span className="payment-summary-overdue">{overdueCount} overdue</span> : null}
          </div>
        </div>
        <button type="button" className="small-secondary-button" disabled={disabled} onClick={() => { setIsAdding((current) => !current); setEditingPaymentRecordId(null); }}>
          {isAdding ? "Close" : "Add payment"}
        </button>
      </div>
      {isAdding ? <PaymentRecordForm project={project} disabled={disabled} submitLabel="Add payment" onCancel={() => setIsAdding(false)} onSubmit={async (payload) => { await onCreatePaymentRecord(project.id, payload); setIsAdding(false); }} /> : null}

      <div className="payment-record-list">
        {sortedPaymentRecords.map((paymentRecord) => {
          const isEditing = editingPaymentRecordId === paymentRecord.id;
          return (
            <article className="payment-record-row" key={paymentRecord.id}>
              <div className="payment-record-main">
                <span className={classNames("payment-pill", paymentRecord.is_overdue ? "overdue" : paymentRecord.status)}>{paymentRecord.is_overdue ? "Overdue" : paymentRecord.status}</span>
                <strong>{formatPaymentAmount(getAmountCents(paymentRecord), paymentRecord.currency)}</strong>
                {paymentRecord.status === "pending" && paymentRecord.due_date ? <span>Expected {formatDate(paymentRecord.due_date)}</span> : null}
                {paymentRecord.paid_at ? <span>Received {formatDateTime(paymentRecord.paid_at)}</span> : null}
              </div>
              {isEditing ? <PaymentRecordForm project={project} disabled={disabled} submitLabel="Save payment" paymentRecord={paymentRecord} onCancel={() => setEditingPaymentRecordId(null)} onSubmit={async (payload) => { await onUpdatePaymentRecord(project.id, paymentRecord.id, payload); setEditingPaymentRecordId(null); }} /> : null}
              <div className="inline-form-actions">
                <button type="button" className="small-quiet-button" disabled={disabled} onClick={() => { setEditingPaymentRecordId((current) => (current === paymentRecord.id ? null : paymentRecord.id)); setIsAdding(false); }}>{isEditing ? "Close edit" : "Edit"}</button>
                <button type="button" className="small-danger-button low-emphasis-danger" disabled={disabled} onClick={() => onDeletePaymentRecord(project.id, paymentRecord.id)}>Delete</button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
