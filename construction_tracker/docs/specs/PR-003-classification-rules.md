# PR-003 Classification Rules

## Goal

Add a deterministic first-pass rule engine that marks parsed HDFC transactions as Ready, Review, or Ignore.

## Scope

- Ignore credit transactions.
- Match construction debits using token-aware keyword groups.
- Suggest vendor, category, subcategory, stage, and payment mode.
- Avoid unsafe substring matches, such as matching `SAND` inside `ANAND`.

## Status

Implemented in `backend/modules/vendors/rule_engine.py`.
