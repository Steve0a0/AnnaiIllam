from types import SimpleNamespace

import pytest

from app.core.payment_constants import PaymentPurpose
from app.services.payment_ledger_service import (
    CLIENT_LEDGER_UNIT,
    PaymentLedgerError,
    build_payment_ledger,
    calculate_quote_total,
    derive_client_payment_intent,
    has_required_advance,
    validate_manual_payment,
)


def quote(total=30000, advance=5000, model="client_pays_company"):
    return SimpleNamespace(
        quoted_amount=total,
        advance_amount=advance,
        payment_model=model,
    )


def requirement(status="approved"):
    return SimpleNamespace(status=status)


def payment(amount, status="paid", purpose=PaymentPurpose.ADJUSTMENT.value):
    return SimpleNamespace(amount=amount, payment_status=status, purpose=purpose)


def test_unit_and_quote_total_are_single_authoritative_contract():
    assert CLIENT_LEDGER_UNIT == "INR_WHOLE_RUPEES"
    assert calculate_quote_total(1200, 3, 10) == 36000
    with pytest.raises(PaymentLedgerError):
        calculate_quote_total(0, 3, 10)


def test_ledger_tracks_paid_refunded_outstanding_and_overpayment():
    ledger = build_payment_ledger(
        quote(total=10000, advance=3000),
        [
            payment(7000),
            payment(1000, purpose=PaymentPurpose.REFUND.value),
        ],
    )
    assert ledger.gross_paid == 7000
    assert ledger.refunded_amount == 1000
    assert ledger.total_paid == 6000
    assert ledger.outstanding_balance == 4000
    assert ledger.advance_due == 0
    assert ledger.overpaid_amount == 0


def test_client_intent_uses_quote_and_remaining_ledger_not_client_values():
    intent = derive_client_payment_intent(
        requirement(),
        quote(total=30000, advance=5000, model="mixed"),
        [payment(2000)],
    )
    assert intent.amount == 3000
    assert intent.payment_model == "mixed"
    assert intent.purpose == PaymentPurpose.ADVANCE.value


def test_advance_is_aggregate_and_balance_waits_for_assignment():
    payments = [payment(2000), payment(3000)]
    assert has_required_advance(quote(), payments) is True
    with pytest.raises(PaymentLedgerError, match="assign workers"):
        derive_client_payment_intent(requirement(), quote(), payments)

    intent = derive_client_payment_intent(
        requirement("workers_assigned"),
        quote(),
        payments,
    )
    assert intent.amount == 25000
    assert intent.purpose == PaymentPurpose.BALANCE.value


def test_overpayment_and_excess_refund_are_rejected():
    with pytest.raises(PaymentLedgerError, match="exceed"):
        validate_manual_payment(
            requirement(),
            quote(total=10000, advance=1000),
            [payment(9000)],
            amount=1001,
            purpose=PaymentPurpose.ADJUSTMENT.value,
        )

    with pytest.raises(PaymentLedgerError, match="Refund"):
        validate_manual_payment(
            requirement("cancelled"),
            quote(total=10000, advance=1000),
            [payment(3000)],
            amount=3001,
            purpose=PaymentPurpose.REFUND.value,
        )


def test_direct_worker_quote_cannot_create_company_charge():
    with pytest.raises(PaymentLedgerError, match="does not collect"):
        derive_client_payment_intent(
            requirement(),
            quote(model="client_pays_worker_directly"),
            [],
        )
