import { FormEvent, useEffect, useMemo, useState } from "react";
import type {
  BillingModel,
  ContractType,
  LegalChannel,
  PaymentCadence,
  Priority,
  ProjectCreatePayload,
  ProjectStatus,
  WorkSourceType,
} from "../api/types";
import { usdToCents } from "../utils/format";

interface ProjectComposerProps {
  disabled: boolean;
  placement?: "card" | "toolbar";
  onCreate: (payload: ProjectCreatePayload) => Promise<void>;
}

const priorities: Priority[] = ["low", "medium", "high", "urgent"];
const statuses: ProjectStatus[] = ["planned", "active", "paused"];
const contractTypes: ContractType[] = ["hourly", "monthly_retainer", "fixed_price", "non_billable"];
const sourceTypes: WorkSourceType[] = ["employment", "freelance", "retainer", "fixed_project", "hourly_project"];
const legalChannels: LegalChannel[] = ["personal", "pfa", "srl", "cim"];
const billingModels: BillingModel[] = ["hourly", "salary", "fixed", "retainer"];
const paymentCadences: PaymentCadence[] = ["weekly", "biweekly", "monthly", "milestone", "manual", "none"];

function optionLabel(value: string): string {
  return value.replace(/_/g, " ");
}

export default function ProjectComposer({ disabled, placement = "card", onCreate }: ProjectComposerProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [title, setTitle] = useState("");
  const [clientName, setClientName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<ProjectStatus>("planned");
  const [priority, setPriority] = useState<Priority>("medium");
  const [sourceType, setSourceType] = useState<WorkSourceType>("freelance");
  const [legalChannel, setLegalChannel] = useState<LegalChannel>("pfa");
  const [billingModel, setBillingModel] = useState<BillingModel>("hourly");
  const [contractType, setContractType] = useState<ContractType>("hourly");
  const [currency, setCurrency] = useState("USD");
  const [hourlyRate, setHourlyRate] = useState("50");
  const [expectedHoursPerWeek, setExpectedHoursPerWeek] = useState("20");
  const [monthlyCommitmentHours, setMonthlyCommitmentHours] = useState("");
  const [monthlyRate, setMonthlyRate] = useState("3000");
  const [fixedPrice, setFixedPrice] = useState("5000");
  const [startDate, setStartDate] = useState("");
  const [estimatedEndDate, setEstimatedEndDate] = useState("");
  const [deadline, setDeadline] = useState("");
  const [paymentCadence, setPaymentCadence] = useState<PaymentCadence>("monthly");
  const [billingNotes, setBillingNotes] = useState("");

  const allowedCadence = useMemo(
    () => (contractType === "non_billable" ? (["none"] as PaymentCadence[]) : paymentCadences.filter((item) => item !== "none")),
    [contractType],
  );
  const resolvedCadence = allowedCadence.includes(paymentCadence) ? paymentCadence : allowedCadence[0];

  useEffect(() => {
    if (sourceType === "employment") {
      setLegalChannel("cim");
      setBillingModel("salary");
      setContractType("monthly_retainer");
      setPaymentCadence("monthly");
      return;
    }
    if (sourceType === "freelance") {
      setLegalChannel("pfa");
      setBillingModel("hourly");
      setContractType("hourly");
      setPaymentCadence("manual");
      return;
    }
    if (sourceType === "retainer") {
      setBillingModel("retainer");
      setContractType("monthly_retainer");
      setPaymentCadence("monthly");
      return;
    }
    if (sourceType === "fixed_project") {
      setBillingModel("fixed");
      setContractType("fixed_price");
      setPaymentCadence("milestone");
      return;
    }
    setBillingModel("hourly");
    setContractType("hourly");
  }, [sourceType]);

  useEffect(() => {
    if (placement !== "toolbar" || !isExpanded) return;

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsExpanded(false);
      }
    }

    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isExpanded, placement]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCreate({
      title,
      client_name: clientName,
      description: description.trim() || null,
      status,
      priority,
      source_type: sourceType,
      legal_channel: legalChannel,
      billing_model: billingModel,
      contract_type: contractType,
      billing_currency: currency.trim().toUpperCase() || "USD",
      hourly_rate_cents: contractType === "hourly" ? usdToCents(hourlyRate) : null,
      expected_hours_per_week: contractType === "hourly" ? Number(expectedHoursPerWeek || "0") : null,
      monthly_commitment_hours: monthlyCommitmentHours ? Number(monthlyCommitmentHours) : null,
      monthly_rate_cents: contractType === "monthly_retainer" ? usdToCents(monthlyRate) : null,
      fixed_price_cents: contractType === "fixed_price" ? usdToCents(fixedPrice) : null,
      start_date: startDate || null,
      estimated_end_date: estimatedEndDate || null,
      deadline: deadline || null,
      payment_cadence: contractType === "non_billable" ? "none" : resolvedCadence,
      billing_notes: billingNotes.trim() || null,
    });
    setIsExpanded(false);
  }

  const projectForm = (
    <form onSubmit={submit} className="form-stack compact-form collapsible-card-body">
      <div className="two-column-form">
        <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} required disabled={disabled} /></label>
        <label>Client<input value={clientName} onChange={(event) => setClientName(event.target.value)} required disabled={disabled} /></label>
      </div>
      <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} disabled={disabled} /></label>

      <div className="three-column-form">
        <label>Status<select value={status} onChange={(event) => setStatus(event.target.value as ProjectStatus)} disabled={disabled}>{statuses.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
        <label>Priority<select value={priority} onChange={(event) => setPriority(event.target.value as Priority)} disabled={disabled}>{priorities.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Source type<select value={sourceType} onChange={(event) => setSourceType(event.target.value as WorkSourceType)} disabled={disabled}>{sourceTypes.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
      </div>

      <div className="three-column-form">
        <label>Legal channel<select value={legalChannel} onChange={(event) => setLegalChannel(event.target.value as LegalChannel)} disabled={disabled}>{legalChannels.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
        <label>Billing model<select value={billingModel} onChange={(event) => setBillingModel(event.target.value as BillingModel)} disabled={disabled}>{billingModels.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
        <label>Contract type<select value={contractType} onChange={(event) => setContractType(event.target.value as ContractType)} disabled={disabled}>{contractTypes.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
      </div>

      <div className="three-column-form">
        <label>Billing currency<input value={currency} onChange={(event) => setCurrency(event.target.value.toUpperCase().slice(0, 3))} maxLength={3} required disabled={disabled} /></label>
        <label>Monthly commitment h<input type="number" min={0} step={0.25} value={monthlyCommitmentHours} onChange={(event) => setMonthlyCommitmentHours(event.target.value)} disabled={disabled} /></label>
        <label>Start date<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} disabled={disabled} /></label>
      </div>

      <div className="two-column-form">
        <label>Estimated end date<input type="date" value={estimatedEndDate} onChange={(event) => setEstimatedEndDate(event.target.value)} disabled={disabled} /></label>
        <label>Billing notes<input value={billingNotes} onChange={(event) => setBillingNotes(event.target.value)} disabled={disabled} /></label>
      </div>

      {contractType === "hourly" ? <div className="three-column-form">
        <label>Hourly rate ({currency})<input type="number" min={0} value={hourlyRate} onChange={(event) => setHourlyRate(event.target.value)} disabled={disabled} /></label>
        <label>Expected hours/week<input type="number" min={0} step={0.25} value={expectedHoursPerWeek} onChange={(event) => setExpectedHoursPerWeek(event.target.value)} disabled={disabled} /></label>
        <label>Payment cadence<select value={resolvedCadence} onChange={(event) => setPaymentCadence(event.target.value as PaymentCadence)} disabled={disabled}>{allowedCadence.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
      </div> : null}

      {contractType === "monthly_retainer" ? <div className="two-column-form">
        <label>Monthly rate ({currency})<input type="number" min={0} value={monthlyRate} onChange={(event) => setMonthlyRate(event.target.value)} disabled={disabled} /></label>
        <label>Payment cadence<select value={resolvedCadence} onChange={(event) => setPaymentCadence(event.target.value as PaymentCadence)} disabled={disabled}>{allowedCadence.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
      </div> : null}

      {contractType === "fixed_price" ? <div className="three-column-form">
        <label>Fixed price ({currency})<input type="number" min={0} value={fixedPrice} onChange={(event) => setFixedPrice(event.target.value)} disabled={disabled} /></label>
        <label>Deadline<input type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} disabled={disabled} /></label>
        <label>Payment cadence<select value={resolvedCadence} onChange={(event) => setPaymentCadence(event.target.value as PaymentCadence)} disabled={disabled}>{allowedCadence.map((item) => <option key={item} value={item}>{optionLabel(item)}</option>)}</select></label>
      </div> : null}

      <button type="submit" className="primary-button" disabled={disabled}>Create source</button>
    </form>
  );

  if (placement === "toolbar") {
    return (
      <>
        <button type="button" className="primary-button compact-toggle-button toolbar-action-button" disabled={disabled} aria-expanded={isExpanded} onClick={() => setIsExpanded(true)}>
          New source
        </button>
        {isExpanded ? (
          <div
            className="modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) setIsExpanded(false);
            }}
          >
            <section className="feedback-modal project-composer-modal" role="dialog" aria-modal="true" aria-labelledby="new-project-title">
              <div className="feedback-modal-header">
                <div className="panel-heading compact-panel-heading">
                  <span className="eyebrow">Work sources</span>
                  <h2 id="new-project-title">Create work source</h2>
                  <p>Capture how this source pays you, then track work and income against it.</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setIsExpanded(false)}>
                  Close
                </button>
              </div>
              {projectForm}
            </section>
          </div>
        ) : null}
      </>
    );
  }

  return (
    <section className="panel-card collapsible-card create-project-card">
      <div className="collapsible-card-header">
        <div className="panel-heading compact-panel-heading">
          <h2>Create work source</h2>
          <p>Capture how this source pays you, then track work and income against it.</p>
        </div>
        <button type="button" className="primary-button compact-toggle-button" disabled={disabled} aria-expanded={isExpanded} onClick={() => setIsExpanded((current) => !current)}>
          {isExpanded ? "Collapse" : "New source"}
        </button>
      </div>

      {isExpanded ? projectForm : null}
    </section>
  );
}
