# Claim Denial and Correction Policy

Policy ID: POL-CLAIM-001
Policy Version: 1.0
Effective Date: 2026-01-01

## Procedure Code and Authorization Matching

A claim requiring prior authorization must contain a procedure code
that matches the procedure code approved on the authorization.

If the billed procedure code does not match the authorized procedure
code, the claim may be denied with denial code AUTH_CODE_MISMATCH.

Before correcting or resubmitting the claim, the reviewer must verify:

1. The billed procedure code.
2. The authorized procedure code.
3. The member identifier.
4. The provider identifier.
5. The diagnosis code.
6. The date of service.
7. The authorization effective date range.

## Resolution Guidance

When the denial is caused by a data-entry or coding error:

- Correct the claim procedure code.
- Preserve the original claim reference.
- Attach the authorization identifier.
- Submit the corrected claim through the approved workflow.

When the service performed differs from the authorized service:

- Do not automatically change the claim.
- Request clinical or coding review.
- Determine whether retrospective authorization is permitted.
- Escalate the case for human review.

## Approval Requirement

Correcting or resubmitting a claim is a write action and requires
authorized human approval.

An AI agent may investigate the denial and recommend an action, but
it must not modify or resubmit the claim without approval.