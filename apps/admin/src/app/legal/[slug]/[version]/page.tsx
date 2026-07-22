import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LegalDocumentView } from "@/components/legal/legal-document-view";
import { getLegalDocument, LEGAL_VERSION, legalDocuments } from "@/content/legal-documents";

type PageProps = { params: Promise<{ slug: string; version: string }> };

export function generateStaticParams() {
  return legalDocuments.map((document) => ({ slug: document.slug, version: LEGAL_VERSION }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug, version } = await params;
  const document = version === LEGAL_VERSION ? getLegalDocument(slug) : undefined;
  return document ? { title: `${document.title} | Annai Illam`, description: document.summary } : {};
}

export default async function VersionedLegalPage({ params }: PageProps) {
  const { slug, version } = await params;
  const document = version === LEGAL_VERSION ? getLegalDocument(slug) : undefined;
  if (!document) notFound();
  return <LegalDocumentView document={document} />;
}

