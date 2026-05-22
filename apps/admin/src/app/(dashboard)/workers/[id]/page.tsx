"use client";

import { useParams } from "next/navigation";
import WorkerDetailView from "@/features/workers/worker-detail-view";

export default function WorkerDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  return <WorkerDetailView workerProfileId={id} />;
}
