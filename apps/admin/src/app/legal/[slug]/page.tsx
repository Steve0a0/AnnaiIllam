import { redirect } from "next/navigation";
import { LEGAL_VERSION } from "@/content/legal-documents";

export default async function CurrentLegalPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  redirect(`/legal/${slug}/${LEGAL_VERSION}`);
}

