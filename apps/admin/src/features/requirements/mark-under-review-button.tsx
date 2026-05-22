"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { requirementsService } from "@/services/requirements.service";
import { getErrorMessage } from "@/lib/get-error-message";

export default function MarkUnderReviewButton({
  requirementId,
  onSuccess,
}: {
  requirementId: number;
  onSuccess: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleClick = async () => {
    setLoading(true);
    setMessage("");

    try {
      await requirementsService.markRequirementUnderReview(requirementId);
      setMessage("Requirement marked under review.");
      onSuccess();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <Button
        onClick={handleClick}
        disabled={loading}
        variant="secondary"
      >
        {loading ? "Updating..." : "Mark Under Review"}
      </Button>
      {message ? (
        <p className="text-sm text-muted-foreground">{message}</p>
      ) : null}
    </div>
  );
}
