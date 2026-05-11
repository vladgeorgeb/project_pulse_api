interface EmptyStateProps {
  disabled: boolean;
  onCreateDemoData: () => Promise<void>;
}

export default function EmptyState({ disabled, onCreateDemoData }: EmptyStateProps) {
  return (
    <section className="empty-state">
      <h2>No client projects yet</h2>
      <p>
        Create your first client project manually, or generate a small sample
        dataset to see capacity, billable work, project progress, and task actions.
      </p>
      <button type="button" className="primary-button" onClick={onCreateDemoData} disabled={disabled}>
        Create demo data
      </button>
    </section>
  );
}
