"use client";

import { useQuery } from "@tanstack/react-query";
import { attendanceService } from "@/services/attendance.service";
import { assignmentsService } from "@/services/assignments.service";
import type { EnrichedAttendanceItem } from "@/types/attendance";

export type AttendanceLookupMode = "requirement" | "assignment";

async function fetchByRequirement(requirementId: number): Promise<EnrichedAttendanceItem[]> {
  const resp = await assignmentsService.getAssignmentsByRequirement(requirementId);
  const assignments = resp.data;
  if (!assignments.length) return [];

  const chunks = await Promise.all(
    assignments.map((a) =>
      attendanceService
        .getAttendanceByAssignment(a.id)
        .then((r) =>
          r.data.map((rec) => ({
            ...rec,
            worker_name: a.worker_name,
            assignment_id: a.id,
            requirement_id: requirementId,
          }))
        )
    )
  );

  return chunks
    .flat()
    .sort((a, b) => a.attendance_date.localeCompare(b.attendance_date));
}

async function fetchByAssignment(assignmentId: number): Promise<EnrichedAttendanceItem[]> {
  const resp = await attendanceService.getAttendanceByAssignment(assignmentId);
  return resp.data.map((rec) => ({
    ...rec,
    worker_name: `Worker #${rec.worker_profile_id}`,
    assignment_id: assignmentId,
    requirement_id: null,
  }));
}

export function useAttendanceLookup(
  mode: AttendanceLookupMode | null,
  id: number | null
) {
  return useQuery({
    queryKey: ["attendance-lookup", mode, id],
    queryFn: (): Promise<EnrichedAttendanceItem[]> => {
      if (!mode || !id) return Promise.resolve([]);
      return mode === "requirement" ? fetchByRequirement(id) : fetchByAssignment(id);
    },
    enabled: mode !== null && id !== null,
    staleTime: 30_000,
    retry: 1,
  });
}
