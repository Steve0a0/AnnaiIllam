import Link from "next/link";
import { LEGAL_VERSION } from "@/content/legal-documents";

const links = [["Privacy", "privacy"], ["Client terms", "client-terms"], ["Worker terms", "worker-terms"], ["Refunds", "refund-cancellation"], ["Grievance", "grievance"]] as const;

export default function LegalFooter() {
  return (
    <footer className="border-t border-border px-4 py-5 md:px-8">
      <nav aria-label="Legal" className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted-foreground">
        {links.map(([label, slug]) => (
          <Link key={slug} className="hover:text-foreground hover:underline hover:underline-offset-4" href={`/legal/${slug}/${LEGAL_VERSION}`}>{label}</Link>
        ))}
        <span>Version {LEGAL_VERSION}</span>
      </nav>
    </footer>
  );
}

