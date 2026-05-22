import { http } from "@/lib/http";
import type {
  RequirementReportResponse,
  AssignmentReportResponse,
  ComplaintReportResponse,
  ReportFilters,
} from "@/types/report";

function triggerCsvDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export const reportsService = {
  getRequirementsReport: async (
    filters: ReportFilters = {},
  ): Promise<RequirementReportResponse> => {
    const res = await http.get("/admin/reports/requirements", { params: filters });
    return res.data;
  },

  getAssignmentsReport: async (
    filters: ReportFilters = {},
  ): Promise<AssignmentReportResponse> => {
    const res = await http.get("/admin/reports/assignments", { params: filters });
    return res.data;
  },

  getComplaintsReport: async (
    filters: ReportFilters = {},
  ): Promise<ComplaintReportResponse> => {
    const res = await http.get("/admin/reports/complaints", { params: filters });
    return res.data;
  },

  downloadRequirementsCsv: async (filters: ReportFilters = {}) => {
    const res = await http.get("/admin/reports/requirements", {
      params: { ...filters, format: "csv" },
      responseType: "blob",
    });
    triggerCsvDownload(res.data as Blob, "requirements_report.csv");
  },

  downloadAssignmentsCsv: async (filters: ReportFilters = {}) => {
    const res = await http.get("/admin/reports/assignments", {
      params: { ...filters, format: "csv" },
      responseType: "blob",
    });
    triggerCsvDownload(res.data as Blob, "assignments_report.csv");
  },

  downloadComplaintsCsv: async (filters: ReportFilters = {}) => {
    const res = await http.get("/admin/reports/complaints", {
      params: { ...filters, format: "csv" },
      responseType: "blob",
    });
    triggerCsvDownload(res.data as Blob, "complaints_report.csv");
  },
};
