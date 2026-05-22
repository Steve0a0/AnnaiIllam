"use client";

import { useParams } from "next/navigation";
import ClientDetailView from "@/features/clients/client-detail-view";

export default function ClientDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  return <ClientDetailView clientId={id} />;
}
