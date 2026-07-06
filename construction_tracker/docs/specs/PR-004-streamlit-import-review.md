# PR-004 Streamlit Import Review

## Goal

Make the app usable for the first HDFC import workflow.

## Scope

- Upload an HDFC Text statement.
- Parse transactions using the backend HDFC parser.
- Classify rows with the rule engine.
- Review and edit suggested fields in Streamlit.
- Download a reviewed CSV and a Ready-only ledger CSV.

## Status

Implemented in `frontend/streamlit/app.py`.
