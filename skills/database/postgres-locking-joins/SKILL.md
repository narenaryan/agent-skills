---
name: postgres-locking-joins
description: Use when PostgreSQL SELECT FOR UPDATE or FOR NO KEY UPDATE joins return missing rows or NULL related fields after lock waits, especially when concurrent transactions change a joined foreign key under Read Committed.
---

# PostgreSQL Locking Joins

Row locking does not refresh the statement snapshot or restart the statement from scratch. Under Read Committed, rechecking an updated base row against previously fetched join data can discard a match despite a valid foreign key.

## Diagnose before changing isolation

Capture SQL, isolation, server version, and `EXPLAIN`. Look for `LockRows` above a join and concurrent join-key updates. [Reproduction harness](scripts/reproduce.py): A updates; B starts its locking join; verify B is blocked before committing A. Use only an explicitly selected disposable database.

| Choice | Boundary |
|---|---|
| Split base-row lock and related read | Second statement gets a fresh Read Committed snapshot |
| Lock inside a CTE/subquery | Inspect the plan; still one statement snapshot |
| Repeatable Read / Serializable | Both can raise `40001`; only Serializable prevents serialization anomalies |

## Lock first, then read

For `work_item(id PRIMARY KEY, queue_id NOT NULL REFERENCES queue(id))`, run as a non-interactive psql script:

```sql
\set ON_ERROR_STOP on
\unset locked_queue_id
BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT queue_id AS locked_queue_id
FROM work_item WHERE id = 42
FOR NO KEY UPDATE
\gset
SELECT * FROM queue WHERE id = :'locked_queue_id';
-- Validate and perform dependent writes here.
ROLLBACK; -- Demonstration only.
```

Bind the returned key into the second statement. Abort/rollback on missing rows, including concurrent deletions. Keep dependent writes inside this transaction.

Sources: [Haki Benita, 2026-02-24](https://hakibenita.com/postgres-row-lock-with-join); PostgreSQL 18 [isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [locking](https://www.postgresql.org/docs/18/explicit-locking.html), [SELECT](https://www.postgresql.org/docs/18/sql-select.html), [retries](https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html), [psql](https://www.postgresql.org/docs/18/app-psql.html). Reviewed 2026-10-07; PostgreSQL 17.11 startup blocked by Unix-socket permissions; examples unexecuted. Recheck on the deployed version.

## Pitfalls

- Locking the old related row as well does not repair the join; a left join can merely expose NULLs.
- A locking CTE cannot see a related row inserted after its statement snapshot; prefer separate statements when that race matters.
- Autocommit releases the first lock before the second read. `SKIP LOCKED` intentionally omits rows; it is not a correctness repair.
- Base locks neither freeze related attributes nor protect absent rows. Broader invariants need a locking protocol followed by every relevant writer; acquire locks consistently.
- For `40001` serialization failures or `40P01` deadlocks, retry the whole transaction, including decisions; avoid duplicating external side effects.
