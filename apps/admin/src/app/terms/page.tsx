import { redirect } from "next/navigation";
import { LEGAL_VERSION } from "@/content/legal-documents";

export default function TermsAliasPage() {
  redirect(`/legal/client-terms/${LEGAL_VERSION}`);
}
