"use client";

import { useParams } from "next/navigation";
import AssignmentAttendanceList from "@/features/attendance/assignment-attendance-list";

export default function AssignmentDetailPage() {
  const params = useParams();
  const assignmentId = Number(params.id);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Assignment #{assignmentId}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          View and correct attendance records for this assignment.
        </p>
      </div>

      <AssignmentAttendanceList assignmentId={assignmentId} />
    </div>
  );
}
