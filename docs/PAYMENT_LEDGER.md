# Authoritative Client Payment Ledger

Status: engineering implementation complete; Product and Finance approval pending.

## Scope and unit

This ledger covers quotes and payments collected from clients by Annai Illam.
Every stored and API amount is an integer **whole INR rupee**. Decimal rupees
are rejected. Razorpay requires integer paise, so the gateway adapter alone
converts rupees × 100. Worker payroll and dispute-credit ledgers are separate
bounded contexts and do not determine a client charge.

## Authoritative values

**app/services/payment_ledger_service.py** is the only owner of these formulas:

- Quote total = rate per worker × worker count × duration days.
- Required advance = the quote's approved advance, from zero through quote total.
- Gross paid = confirmed non-refund payments.
- Refunded amount = confirmed refund entries, plus legacy rows marked refunded.
- Total paid = max(0, gross paid − refunded amount).
- Outstanding balance = max(0, quote total − total paid).
- Overpaid amount = max(0, total paid − quote total).

Client **amount** and **payment_model** fields are deprecated compatibility hints.
The create-order and reference endpoints derive both values from the approved
quote and current ledger. They never use those client hints to set a charge.

## Payment purposes and valid requirement states

| Purpose | Valid state | Rule |
| --- | --- | --- |
| advance | approved | Exact remaining advance due |
| balance | approved only when no advance is required; otherwise workers_assigned, in_progress, completed | No more than outstanding |
| adjustment | approved, workers_assigned, in_progress, completed | Finance-admin only; no more than outstanding |
| refund | approved, workers_assigned, in_progress, completed, cancelled | Finance-admin only; no more than net paid |

New overpayments are rejected. Existing overpaid legacy data remains visible as
**overpaid_amount** for Finance to reconcile. Gateway order/payment IDs are
unique, and a matching pending intent is reused. Mobile callbacks and Razorpay
webhooks converge on one row-locked reconciliation service that validates the
captured status, exact paise amount, and INR currency before marking paid.

## Lifecycle decision

    quoted --client approves quote--> approved
    approved --aggregate paid >= required advance--> assignment is permitted
    approved --admin assigns workers--> workers_assigned
    workers_assigned --work begins--> in_progress
    in_progress --operations confirms completion--> completed

Payment success never changes a requirement status. Finance confirms money;
Operations/Admin advances assignment and completion through their existing
actions. Admin approval of a manual payment changes only payment status.

## Required sign-off

| Approver | Decision | Date | Notes |
| --- | --- | --- | --- |
| Product owner | PENDING | — | Confirm collection timing and lifecycle diagram |
| Finance owner | PENDING | — | Confirm unit, refund, adjustment, and reconciliation rules |

PROD-004 cannot be marked DONE until both rows are approved.
