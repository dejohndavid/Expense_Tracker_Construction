# PR-002 - HDFC Text Parser

## Goal

Parse HDFC text statement exports into structured transaction records.

## Scope

- Read HDFC text exports with columns:
  - Date
  - Narration
  - Value Date
  - Debit Amount
  - Credit Amount
  - Chq/Ref Number
  - Closing Balance
- Normalize dates and amounts.
- Preserve original narration and reference number.
- Extract candidate transaction metadata:
  - transfer channel
  - payee name
  - UPI ID when present
  - purpose text when present

## Out Of Scope

- Vendor matching
- Rule scoring
- Database persistence
- UI upload workflow

## Acceptance Criteria

- Parser accepts the provided HDFC text sample.
- Parser returns typed records.
- Parser preserves source text for auditing.
- Tests cover UPI, NEFT, ACH, debit, and credit examples.
