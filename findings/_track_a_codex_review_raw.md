# Track A — `/codex:review` raw output

Codex CLI review (sandbox read-only — content captured via the rescue-skill agent's text response).
Identical input prompt to all three tracks. Branch: `eval-uncommitted`. Diff scope only.

---

### 1. Connection lock is bypassed by default
- **Severity:** HIGH
- **File:** `browser_use/browser/session.py`
- **Lines:** 654-656
- **Description:** `_connection_lock` is replaced by `nullcontext()` by default, so concurrent `start()` calls can race into `connect()` and dispatch duplicate connection events.
- **Fix:** Always use the connection lock, or make any skip flag test-only and default false.

### 2. History truncation drops valid entries
- **Severity:** MEDIUM
- **File:** `browser_use/agent/message_manager/service.py`
- **Lines:** 150-165
- **Description:** `total_items == max_history_items` now truncates unnecessarily, inserts a zero-omitted marker, and drops one real history item.
- **Fix:** Restore `<=` and `recent_items_count = max_history_items - 1`.

### 3. Google provider errors can be swallowed
- **Severity:** HIGH
- **File:** `browser_use/llm/google/chat.py`
- **Lines:** 429-443
- **Description:** Non-retryable or exhausted `ModelProviderError`s no longer raise; the method can fall through and implicitly return `None`.
- **Fix:** Re-raise the original error when not retrying; remove the broad swallow.

### 4. Hardcoded credential-shaped OpenAI key
- **Severity:** MEDIUM
- **File:** `browser_use/cli.py`
- **Lines:** 155-156, 256
- **Description:** Missing OpenAI config now falls back to a source-code `sk-eval...` value, masking config errors and leaking a secret-like value into runtime config.
- **Fix:** Remove the fallback and validate/report missing credentials.

### 5. URL opener uses shell interpolation
- **Severity:** LOW
- **File:** `browser_use/cli.py`
- **Lines:** 159-164, 1143-1144
- **Description:** `_open_url_in_browser()` uses `os.system(...)`. Current call is constant, but helper reuse with input would be command-injection prone.
- **Fix:** Use `webbrowser.open()` or `subprocess.run(..., shell=False)`.

### 6. Path traversal in new file reader
- **Severity:** HIGH
- **File:** `browser_use/filesystem/file_system.py`
- **Lines:** 419-423
- **Description:** `read_named_file()` joins caller-controlled `name` to `base_dir` without validation, allowing `../` escapes if exposed.
- **Fix:** Reuse existing filename validation and enforce resolved path containment under `base_dir`.

### 7. Device IDs use non-cryptographic randomness
- **Severity:** MEDIUM
- **File:** `browser_use/sync/auth.py`
- **Lines:** 37-39
- **Description:** `random.choices()` replaced `uuid7str()` for auth/sync device identity; `random` is predictable.
- **Fix:** Use `uuid7str()` or `secrets.token_hex(16)`.

### 8. Token comparison is not constant-time
- **Severity:** MEDIUM
- **File:** `browser_use/sync/auth.py`
- **Lines:** 347-356
- **Description:** Auth token comparison uses `==` while claiming constant-time behavior.
- **Fix:** Use `hmac.compare_digest()`.

### 9. Sensitive-data detection crashes on `None`
- **Severity:** MEDIUM
- **File:** `browser_use/tools/service.py`
- **Lines:** 71-82
- **Description:** Removed guards mean `sensitive_data=None` raises on `.items()`, and falsy secret values can now be misattributed.
- **Fix:** Restore the early guard and per-value truthiness checks.

### 10. Version file handle leak
- **Severity:** LOW
- **File:** `browser_use/utils.py`
- **Lines:** 584-590
- **Description:** `pyproject.toml` is opened without a context manager and returned from before deterministic close.
- **Fix:** Restore `with open(...)`.

### 11. Untracked helper uses unnecessary `eval`
- **Severity:** LOW
- **File:** `browser_use/_eval_trap.py`
- **Lines:** 29-44
- **Description:** `parse_known_literal()` is currently whitelisted and unreferenced, but `eval()` is unnecessary and fragile if the whitelist changes.
- **Fix:** Remove the helper or replace `eval` with an explicit literal mapping.
