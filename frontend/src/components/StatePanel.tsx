interface StatePanelProps {
  title: string;
  message?: string;
  action?: React.ReactNode;
}

export function StatePanel({ title, message, action }: StatePanelProps) {
  return (
    <section className="state-panel" role="status" aria-live="polite">
      <h2>{title}</h2>
      {message ? <p>{message}</p> : null}
      {action ? <div>{action}</div> : null}
    </section>
  );
}
