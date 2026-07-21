import Link from "next/link";
import type { ReactNode } from "react";

import { GRIEVANCE_EMAIL, LEGAL_EFFECTIVE_DATE, LEGAL_VERSION, primaryLegalDocuments } from "@/content/legal-documents";

export function LegalShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-5 sm:px-8">
          <Link href="/legal" className="text-base font-semibold tracking-tight text-emerald-950">Annai Illam</Link>
          <span className="text-xs font-medium text-stone-500">Legal and privacy</span>
        </div>
      </header>
      {children}
      <footer className="border-t border-stone-200 bg-white">
        <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
          <nav aria-label="Legal documents" className="flex flex-wrap gap-x-5 gap-y-3 text-sm text-stone-600">
            {primaryLegalDocuments.map((document) => (
              <Link key={document.slug} className="underline-offset-4 hover:text-emerald-800 hover:underline" href={`/legal/${document.slug}/${LEGAL_VERSION}`}>
                {document.title}
              </Link>
            ))}
            <Link className="underline-offset-4 hover:text-emerald-800 hover:underline" href={`/legal/account-deletion/${LEGAL_VERSION}`}>Account deletion</Link>
          </nav>
          <p className="mt-5 text-xs leading-5 text-stone-500">
            Version {LEGAL_VERSION}, effective {LEGAL_EFFECTIVE_DATE}. Contact{" "}
            <a className="underline underline-offset-4" href={`mailto:${GRIEVANCE_EMAIL}`}>{GRIEVANCE_EMAIL}</a>.
          </p>
        </div>
      </footer>
    </div>
  );
}

