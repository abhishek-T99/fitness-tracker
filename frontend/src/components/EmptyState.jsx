export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="card p-10 text-center">
      {Icon && (
        <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-400 mb-4">
          <Icon className="w-7 h-7" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      {description && <p className="text-slate-500 mt-1">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
