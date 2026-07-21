import { redirect } from "next/navigation";
import { LEGAL_VERSION } from "@/content/legal-documents";

export default function PrivacyAliasPage() {
  redirect(`/legal/privacy/${LEGAL_VERSION}`);
}

