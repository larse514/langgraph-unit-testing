---
description: "Testing requirements and TDD workflow standards"
alwaysApply: true
---

## Tests

1. All code changes must include any necessary unit tests, this includes new unit tests, removing no longer applicable tests, or updating tests
2. Any new features must include evaluations in the **evals** directory. These should only be written for new features
3. write code and run tests until they pass

## Process

1. All changes must require running tests via `make test`
