---
description: "Standards for code comments and documentation"
alwaysApply: true
---

## Comments

1. Comments should only be used to describe situations in code where we have to use a workaround, or something is not obvious why we are doing something. 

2. Comments should never be used to describe what is happening

### Good examples
```python

# Some legacy records were created without a timezone.
# We default to UTC to avoid breaking historical reports.
timestamp = record.created_at or assume_utc(record.raw_timestamp)

```
```python
# This query intentionally avoids an index scan.
# In production, forcing the planner here reduced p99 latency by ~40%.
result = await db.execute(text(slow_but_predictable_query))
```

### Bad Example
```python
# Create a new user in the database
user = await session.execute(insert(User).values(**data))
```
