import Link from "next/link";
import { LEGAL_EFFECTIVE_DATE, LEGAL_VERSION, primaryLegalDocuments } from "@/content/legal-documents";

export default function LegalIndexPage() {
  return (
    <main className="mx-auto max-w-4xl px-5 py-12 sm:px-8 md:py-20">
      <p className="text-sm font-semibold text-emerald-800">Version {LEGAL_VERSION}</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight text-emerald-950">Legal documents</h1>
      <p className="mt-5 max-w-2xl text-base leading-7 text-stone-600">Current policies and terms for the Annai Illam client and worker services. Effective {LEGAL_EFFECTIVE_DATE}.</p>
      <div className="mt-12 divide-y divide-stone-200 border-y border-stone-200">
        {primaryLegalDocuments.map((document) => (
          <Link key={document.slug} href={`/legal/${document.slug}/${LEGAL_VERSION}`} className="group grid gap-2 py-6 sm:grid-cols-[220px_1fr]">
            <span className="font-semibold text-stone-900 group-hover:text-emerald-800">{document.title}</span>
            <span className="text-sm leading-6 text-stone-600">{document.summary}</span>
          </Link>
        ))}
        <Link href={`/legal/account-deletion/${LEGAL_VERSION}`} className="group grid gap-2 py-6 sm:grid-cols-[220px_1fr]">
          <span className="font-semibold text-stone-900 group-hover:text-emerald-800">Account deletion</span>
          <span className="text-sm leading-6 text-stone-600">Request account deletion inside either app or without app access.</span>
        </Link>
      </div>
    </main>
  );
}

