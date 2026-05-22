"use client";

import { useQuery } from "@tanstack/react-query";
import { attendanceService } from "@/services/attendance.service";

export function useAssignmentAttendance(assignmentId: number) {
  return useQuery({
    queryKey: ["assignment-attendance", assignmentId],
    queryFn: () => attendanceService.getAttendanceByAssignment(assignmentId),
    enabled: !!assignmentId,
  });
}
