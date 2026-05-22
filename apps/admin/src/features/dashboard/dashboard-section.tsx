export default function DashboardSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        {title}
      </h2>
      {children}
    </section>
  );
}

