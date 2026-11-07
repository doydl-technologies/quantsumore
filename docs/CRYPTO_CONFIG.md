# CryptoConfig transactional refresh and snapshots

CryptoConfig refreshes all metadata tables in one SQLite transaction. It does not delete or replace the database file. Validation happens before writes, and any database error rolls back the refresh and propagates to the caller. The previous committed data remains available.

SQLite BEGIN IMMEDIATE serializes competing writers, including writers in other processes. Connections wait up to 30 seconds for locks, then raise an error rather than publishing partial data. Readers use an explicit read transaction across all three tables, so they see a complete committed generation. During first initialization the prior generation is empty. Before any database exists, snapshot() returns empty collections.

## Cache contract

An instance uses a reentrant lock to protect its operations and staged input. Cache publication occurs once, after every table has been read successfully. A failed read leaves the prior internal cache intact and raises an error; it does not return a partial result. Successful writes reload the cache.

snapshot() reloads committed data on every call, including commits made by other instances or processes, and returns an isolated dictionary containing cryptos, exchanges and pairs. This favors correctness over avoiding local database reads.

Use snapshot() when reading multiple collections together. Separate accesses to cryptos, exchanges and pairs are each consistent, but a refresh may occur between accesses.

The properties and snapshot() return deep copies. Editing returned lists or dictionaries does not change the internal cache or database. saved_json_content is staged input, also copied on assignment and access. Assign a complete updated payload before calling to_sqlite(); mutating a returned input copy does not stage an update.

Existing Query.Currency / Query.Exchange objects built from previously returned lists are independent snapshots. Recreate those derived objects if they need newer metadata; CryptoConfig does not mutate objects held by callers.

## Scope and limits

Missing bundled ticker/crypto reference files are copied to temporary files in the destination directory before publication. Windows uses a rename that refuses an existing destination; other platforms use a hard link, because a POSIX rename could overwrite another process's file. Publication succeeds only when the destination is absent, so concurrent imports never observe a partial copy and existing user files are retained. Copy/publication errors propagate and temporary files are removed on handled failures. This initialization requires the local filesystem to support the corresponding atomic operation.

db_directory is a directory even when its name contains periods; missing directories are created when opening the database. Use db_filename for an explicit database-file path. The lower-level SQLiteDBHandler also retains its legacy handling of an already existing file passed as directory; nonexistent paths are treated as directories.

These guarantees apply to CryptoConfig operations on a local SQLite database with functioning file locks. External file deletion, manual schema changes, unsupported network filesystems and mutable public path configuration during an operation are outside this contract. An initialized database must have the expected schema.

A database commit and a Python cache assignment cannot form one cross-process transaction. Public reads obtain a fresh committed snapshot, and same-instance operations are serialized. A later writer may commit immediately after a read completes; returned snapshots represent the database at their read transaction, not a permanently live view.
