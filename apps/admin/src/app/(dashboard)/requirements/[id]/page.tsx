"use client";

import { useParams } from "next/navigation";
import RequirementDetailView from "@/features/requirements/requirement-detail-view";

export default function RequirementDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  return <RequirementDetailView requirementId={id} />;
}
