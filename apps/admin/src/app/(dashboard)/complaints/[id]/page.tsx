"use client";

import { useParams } from "next/navigation";
import ComplaintDetailView from "@/features/complaints/complaint-detail-view";

export default function ComplaintDetailPage() {
  const params = useParams();
  const complaintId = Number(params.id);

  return <ComplaintDetailView complaintId={complaintId} />;
}
