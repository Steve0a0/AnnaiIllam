import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";

type StatusBadgeProps = {
  value: string;
};

const statusStyles: Record<string, string> = {
  draft:             "bg-[#F5F5F4] text-[#78716C] border-[#E7E5E4]",
  submitted:         "bg-[#DBEAFE] text-[#1D4ED8] border-[#BFDBFE]",
  under_review:      "bg-[#EDE9FE] text-[#6D28D9] border-[#DDD6FE]",
  quoted:            "bg-[#F5F5F4] text-[#78716C] border-[#E7E5E4]",
  approved:          "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
  workers_assigned:  "bg-[#D1FAE5] text-[#065F46] border-[#A7F3D0]",
  rejected:          "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]",
  cancelled:         "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]",
  assigned:          "bg-[#DBEAFE] text-[#1D4ED8] border-[#BFDBFE]",
  accepted:          "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
  declined:          "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]",
  replaced:          "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]",
  active:            "bg-[#CFFAFE] text-[#0E7490] border-[#A5F3FC]",
  in_progress:       "bg-[#CFFAFE] text-[#0E7490] border-[#A5F3FC]",
  completed:         "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
  not_started:       "bg-[#F5F5F4] text-[#78716C] border-[#E7E5E4]",
  checked_in:        "bg-[#CFFAFE] text-[#0E7490] border-[#A5F3FC]",
  checked_out:       "bg-[#DBEAFE] text-[#1D4ED8] border-[#BFDBFE]",
  verified:          "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
  present:           "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
  corrected:         "bg-[#DBEAFE] text-[#1D4ED8] border-[#BFDBFE]",
  half_day:          "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]",
  absent:            "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]",
  late:              "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]",
  open:              "bg-[#DBEAFE] text-[#1D4ED8] border-[#BFDBFE]",
  in_review:         "bg-[#EDE9FE] text-[#6D28D9] border-[#DDD6FE]",
  resolved:          "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
  closed:            "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]",
};

const pulseDotStatuses = new Set(["checked_in", "in_progress"]);

export default function StatusBadge({ value }: StatusBadgeProps) {
  const classes = statusStyles[value] ?? "bg-slate-100 text-slate-700 border-slate-200";
  const hasPulseDot = pulseDotStatuses.has(value);
  return (
    <Badge variant="outline" className={cn("h-[22px] whitespace-nowrap rounded-full px-2.5 text-xs font-medium capitalize", classes)}>
      {hasPulseDot && (
        <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-[pulseDot_1.4s_ease-in-out_infinite] rounded-full bg-current" />
      )}
      {value.replaceAll("_", " ")}
    </Badge>
  );
}
