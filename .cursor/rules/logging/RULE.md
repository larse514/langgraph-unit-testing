---
description: "Logging standards and log level guidelines"
alwaysApply: true
---

## Logging

1. All code changes must include any necessary production logging. Use the following to determine when and what level of logs to use:
TRACE: Low Level system metrics
DEBUG: Diagnostic info (before after method calls, parameter values, etc)
INFO: Domain level info (order was placed, order was canceled)
WARN: Non-critical error that needs attention soon
ERROR: Something went wrong that needs to be fixed immediately (think "is this something I should be woken up for?")
