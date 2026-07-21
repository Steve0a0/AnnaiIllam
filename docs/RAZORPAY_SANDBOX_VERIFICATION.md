# Razorpay Test-Mode Reconciliation Runbook

Use this runbook before enabling live Razorpay keys. Never paste key secrets,
checkout signatures, or webhook secrets into tickets, logs, or screenshots.

## Preconditions

- A staging backend is deployed over HTTPS with `APP_ENV=staging`.
- `RAZORPAY_KEY_ID` starts with `rzp_test_`.
- `RAZORPAY_KEY_SECRET` and `PAYMENT_WEBHOOK_SECRET` come from the same
  Razorpay test-mode account.
- Razorpay Dashboard has a test-mode webhook pointing to:
  `https://<staging-host>/api/v1/payments/webhook/razorpay`.
- Only `payment.captured` is required for this proof.
- Automatic capture is enabled for the test account.

## End-to-end proof

1. Create a controlled staging client, approved requirement, and approved quote
   with an amount that Finance has authorised for test mode.
2. In the client app, open the payment screen and create the order. Record only
   the local payment ID and Razorpay order ID.
3. Confirm the returned amount in paise equals the authoritative local rupee
   amount multiplied by 100 and the currency is INR.
4. Complete Razorpay Checkout using a test-mode instrument. Do not use a real
   card or live key.
5. Confirm the mobile success callback returns HTTP 200 from
   `POST /api/v1/client/payments/verify`.
6. In Razorpay Dashboard, confirm the payment status is `captured` and deliver
   or replay its `payment.captured` webhook.
7. Confirm the webhook returns HTTP 200.
8. Query the staging ledger:

   ```sql
   SELECT id, requirement_id, amount, payment_status,
          gateway_order_id, gateway_payment_id, paid_at
   FROM client_payments
   WHERE gateway_order_id = '<recorded test order id>';
   ```

9. Verify there is exactly one row, it is `paid`, its amount matches the quote,
   and its gateway payment ID matches Razorpay.
10. Replay the identical webhook and retry the mobile callback. Both must return
    HTTP 200 without changing `gateway_payment_id` or `paid_at`.

## Reverse-order proof

Repeat with a second controlled payment, but delay the mobile callback:

1. Complete Checkout and allow `payment.captured` to reach staging first.
2. Confirm the webhook marks the one local row paid.
3. Submit the saved mobile callback fields.
4. Confirm the callback returns HTTP 200, stores the checkout signature if
   absent, and does not create or recount a payment.

## Evidence to retain

- Date/time and tester.
- Staging release commit.
- Local payment ID, test order ID, and test payment ID.
- Expected rupees and observed paise.
- Callback-first and webhook-first HTTP results.
- Ledger row count/status before and after duplicate delivery.
- Razorpay Dashboard screenshot with secrets and customer data redacted.

Live-mode activation still requires Finance Owner, Product Owner, and Tech Lead
approval in the production-hardening tracker.
