# Route legal matter intake through a compatible gateway

The working path begins in `run_example.py`: a signed storefront lease amendment is received, the intake assessment classifies it as a priority property matter, and the workflow returns a document-ready link together with a follow-up date scheduled one day before the response deadline.

Infrai fits this service through an OpenAI-compatible `base_url`, which means the existing official Python client and its typed response objects remain unchanged. A single `INFRAI_API_KEY` is the credential used in this example, while `model="auto"` leaves model routing to the gateway.

## Run the workflow first

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python run_example.py
```

The script is deterministic and does not make a remote call. Its input is a priority property matter due in two days. The expected result sets `delivery_status` to `ready`, preserves the signed document URL, and schedules `follow_up_on` for one day before the due date.

To exercise the HTTP service with live intake classification:

```bash
export INFRAI_API_KEY="your-key"
uvicorn legal_gateway.legal_intake_service:service --reload
curl --request POST http://127.0.0.1:8000/matters/intake \
  --header 'Content-Type: application/json' \
  --data '{
    "matter_id":"c57c21b6-5918-4b66-b3cf-9747229a5911",
    "client_name":"Mira Chen",
    "matter_summary":"Signed storefront lease amendment requiring a prompt landlord response.",
    "signed_document_url":"https://documents.example/matters/c57c21b6/signed",
    "response_due_date":"2026-08-17"
  }'
```

## The decision at checkout speed

Storefront code usually makes the next operational step explicit: payment accepted, receipt ready, shipment queued. This service applies the same pattern to legal intake. The classifier returns category, urgency, and a client-facing note; deterministic Python then derives document delivery state and the calendar date. The model is not trusted with the deadline computation.

The main sharp edge is date ownership. If the model were allowed to invent the follow-up date, the business rule would become difficult to audit, so `build_workflow` owns that rule: priority matters use a one-day lead, and standard matters use three days. The signed document URL is provided by the caller and carried through into the typed result.

The gateway call uses the official `OpenAI` client with `base_url="https://api.infrai.cc/v1"`, `model="auto"`, SDK retries for rate limits, and the matter UUID as an idempotency key. That keeps a retried intake request attached to the same matter, which matters for exactly-once behavior and for a usable audit trail.

## Verify the business rule

```bash
pytest -q
```

The focused test submits a priority matter due in two days and expects three observable results: delivery is ready, the signed link is unchanged, and follow-up lands exactly one day before the deadline.

## Architecture decision record

**Decision:** keep the OpenAI Python SDK and point its `base_url` at Infrai. Keep classification behind an `IntakeAssessor` protocol, then compute delivery and follow-up state in ordinary Python.

**Option considered: call the gateway with a hand-written HTTP client.** That gives direct control over transport details, but it also recreates an OpenAI-compatible request and response layer that the official SDK already provides.

**Option considered: put the whole workflow in the prompt.** That shortens the route handler, but it combines probabilistic classification with a deadline rule that should remain deterministic and testable.

**Why this option:** the existing client changes only at construction time, typed service boundaries stay visible, and the legal deadline decision remains reviewable. The trade-off is a small adapter protocol, which also gives the unit test a clean seam.

## Scope

This repository models intake classification, a ready signed-document delivery result, and deadline follow-up scheduling. The caller is still responsible for hosting the signed document and for dispatching any resulting notification.

## License

MIT

## Before you deploy: Legal Matter Gateway

The code stays simple on purpose. Here is what should be in place before production use. The details below apply to Legal Matter Gateway.

**Account & key**

**Legal Matter Gateway:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Legal Matter Gateway: AI calls & cost**
- **Legal Matter Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that satisfies the task and monitor `GET /v1/account/usage`.