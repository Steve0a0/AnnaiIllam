import Link from "next/link";

import type { LegalDocument } from "@/content/legal-documents";
import { LEGAL_EFFECTIVE_DATE, LEGAL_VERSION } from "@/content/legal-documents";

export function LegalDocumentView({ document }: { document: LegalDocument }) {
  return (
    <main className="mx-auto grid max-w-6xl gap-10 px-5 py-10 sm:px-8 md:grid-cols-[220px_minmax(0,720px)] md:py-16">
      <aside className="md:sticky md:top-8 md:self-start">
        <Link href="/legal" className="text-sm font-medium text-emerald-800 underline-offset-4 hover:underline">All legal documents</Link>
        <dl className="mt-6 space-y-4 border-l-2 border-emerald-800 pl-4 text-sm">
          <div><dt className="text-xs font-medium uppercase tracking-wider text-stone-500">Version</dt><dd className="mt-1 font-medium text-stone-800">{LEGAL_VERSION}</dd></div>
          <div><dt className="text-xs font-medium uppercase tracking-wider text-stone-500">Effective</dt><dd className="mt-1 text-stone-800">{LEGAL_EFFECTIVE_DATE}</dd></div>
          <div><dt className="text-xs font-medium uppercase tracking-wider text-stone-500">Applies to</dt><dd className="mt-1 text-stone-800">{document.audience}</dd></div>
        </dl>
      </aside>
      <article>
        <p className="text-sm font-semibold text-emerald-800">Annai Illam legal document</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-emerald-950 sm:text-4xl">{document.title}</h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-stone-600">{document.summary}</p>
        <div className="mt-10 border-t border-stone-200">
          {document.sections.map((section) => (
            <section key={section.heading} className="border-b border-stone-200 py-8">
              <h2 className="text-xl font-semibold tracking-tight text-stone-900">{section.heading}</h2>
              {section.paragraphs?.map((paragraph) => <p key={paragraph} className="mt-4 text-[15px] leading-7 text-stone-700">{paragraph}</p>)}
              {section.bullets ? (
                <ul className="mt-4 list-disc space-y-3 pl-5 text-[15px] leading-7 text-stone-700 marker:text-emerald-700">
                  {section.bullets.map((item) => <li key={item}>{item}</li>)}
                </ul>
              ) : null}
            </section>
          ))}
        </div>
      </article>
    </main>
  );
}

