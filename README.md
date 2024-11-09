# File System Watcher

A small file system monitoring app which shows files that have been modified, created or deleted

Will build this to make it a cli tool rather than be in dev mode

## Needed

- Poetry
- Python3.10>

### Install dep

```python
poetry install .
```

## How to use

```bash
poetry run file_watcher/main.py . '\.py$'
```

Arguments

- Directory: Mandatory
- Pattern: Optional

## Pattern matching

Regex will have to match python regex for e.g.

```python
poetry run file_watcher/main.py . '\.py$'
```

This will look for only files with the extension `.py`.

### To look for multiple patterns

Just extend the command for e.g.

```bash
poetry run file_watcher/main.py . '\.py$' '\.yml$' 'blah'
```

## How to extend

- [x] Add a file content checksumming
- [x] Impl file filtering (should be done via the patterns already, just need to impl)
- [ ] Add a REST API to query file changes (might be interesting)
- [ ] Impl a TUI for an interface
