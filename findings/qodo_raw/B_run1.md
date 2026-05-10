# Track B — Qodo Gen VS Code plugin "Review uncommitted changes" (raw paste)

Branch: `eval-uncommitted` on `corpus/browser-use`. 8 modified + 1 untracked file.
Tool: Qodo Gen IDE plugin, "Review uncommitted changes" workflow.

Top-line summary (Qodo's own header):
> "Changes introduce multiple correctness regressions (off-by-one history window, swallowed provider errors, leaked file descriptor, broken sensitive-data detection) and several high-impact security issues (hardcoded API-key default, shell command injection, path traversal, weak device-id randomness, timing-attack token compare), plus a reliability regression enabling concurrent CDP connection races."

---

## 5 Security Vulnerabilities

### 1. [high] Hardcoded OPENAI_API_KEY default leaks credential-shaped secret and can be used unintentionally
- **File:** `browser_use/cli.py`
- **Description:** `DEFAULT_OPENAI_API_KEY` is a literal `sk-...` string and is used as a fallback when `OPENAI_API_KEY` is unset, which can accidentally route requests using a baked-in key-like value and also constitutes a secret-pattern in source.
- **Evidence:** `get_default_config()` now prefers `os.environ.get("OPENAI_API_KEY", DEFAULT_OPENAI_API_KEY)` over `CONFIG.OPENAI_API_KEY`, so the hardcoded value becomes the effective key whenever env/config is missing.
- **Fix:** Remove the hardcoded default and fall back to None/empty (and error clearly) or to `CONFIG.OPENAI_API_KEY` only.

### 2. [high] Command injection via os.system in _open_url_in_browser()
- **File:** `browser_use/cli.py`
- **Description:** `_open_url_in_browser()` interpolates `url` directly into `os.system()` without quoting/validation, allowing shell metacharacters to execute arbitrary commands.
- **Evidence:** The function uses `os.system(f"start {url}")` / `os.system(f"xdg-open {url}")`, which executes through a shell and treats `url` as command text.
- **Fix:** Use `subprocess.run([...], shell=False)` (or `webbrowser.open`) and validate/escape URLs.

### 3. [high] Path traversal in FileSystem.read_named_file() allows sandbox escape
- **File:** `browser_use/filesystem/file_system.py`
- **Description:** `read_named_file()` joins `self.base_dir / name` and opens it directly, so `..` segments or absolute paths can read arbitrary host files outside the intended base directory.
- **Evidence:** Unlike existing async read paths that typically validate filenames (e.g., `write_file()` calls `_is_valid_filename()`), this new method performs no validation before `open()`.
- **Fix:** Reject absolute paths and `..`, and enforce `path.resolve()` stays within `base_dir` (e.g., `commonpath`/`is_relative_to`).

### 4. [high] Predictable device_id generation weakens sync auth identity
- **File:** `browser_use/sync/auth.py`
- **Description:** `get_or_create_device_id()` switches from `uuid7str()` to `random.choices(...)`, which is not cryptographically secure and can be predictable, enabling device-id spoofing.
- **Evidence:** The new code uses Python's `random` module (Mersenne Twister) rather than a CSPRNG; the previous implementation used `uuid7str()`.
- **Fix:** Use `secrets.token_hex(16)` or revert to `uuid7str()`/`uuid.uuid4().hex`.

### 5. [medium] Non-constant-time token comparison enables timing attacks
- **File:** `browser_use/sync/auth.py`
- **Description:** `_check_token()` uses `==` for secret comparison, which can short-circuit and leak information via timing differences when used on auth/webhook paths.
- **Evidence:** `is_authorized_request()` delegates to `_check_token()` for bearer-token matching, so this comparison is directly on the authorization decision path.
- **Fix:** Replace with `hmac.compare_digest(provided, expected)` (and normalize types/encoding).

## 5 Potential bugs

### 6. [high] Off-by-one history truncation drops valid items and shortens window
- **File:** `browser_use/agent/message_manager/service.py`
- **Description:** Changing `<=` to `<` and reducing `recent_items_count` by an extra 1 causes the history view to omit an item when `total_items == max_history_items` and generally show fewer recent items than intended.
- **Evidence:** The comment says "Show first item + omitted message + most recent (max_history_items - 1) items" but the code now uses `max_history_items - 2`.
- **Fix:** Restore `<=` and set `recent_items_count = self.max_history_items - 1`.

### 7. [high] ModelProviderError is silently swallowed when non-retryable or retries exhausted
- **File:** `browser_use/llm/google/chat.py`
- **Description:** The retry logic now catches `ModelProviderError` but no longer re-raises it when not retrying, so callers may get None/unexpected behavior instead of an exception.
- **Evidence:** The previous code had an explicit terminal `raise`, but the new code exits the `except ModelProviderError` block without raising in the non-retry path.
- **Fix:** Reintroduce `raise` when not retrying (and remove the broad `except Exception: pass`).

### 8. [medium] _detect_sensitive_key_name can crash when sensitive_data is None and mis-attribute falsy values
- **File:** `browser_use/tools/service.py`
- **Description:** Removing the early guard means `sensitive_data.items()` will raise `AttributeError` when `sensitive_data is None`, and removing `if value` checks can cause empty-string/None values to match unexpectedly.
- **Evidence:** In `input()` this helper is called only when `has_sensitive_data and sensitive_data`, but the helper itself is a general utility and can be called elsewhere; its signature explicitly allows `sensitive_data: ... | None`.
- **Fix:** Restore `if not sensitive_data or not text: return None` and keep truthiness guards.

### 9. [medium] File descriptor leak in get_browser_use_version() due to missing context manager
- **File:** `browser_use/utils.py`
- **Description:** Opening `pyproject.toml` without `with` leaks the file handle on both success and failure paths, which can exhaust file descriptors in long-running processes.
- **Evidence:** The new code assigns `f = open(...)` and returns without closing `f`, and there is no `finally`/`close()` call.
- **Fix:** Restore the `with open(...) as f:` block (or ensure `f.close()` in a `finally`).

### 10. [high] Connection lock is skipped by default, reintroducing concurrent connect race
- **File:** `browser_use/browser/session.py`
- **Description:** `_skip_connection_lock` defaults to True, so the real `_connection_lock` is replaced with `nullcontext()` and concurrent `start()` calls can race into `_cdp_client_root is None` and connect twice.
- **Evidence:** The comment says the lock is for "race condition protection" but the new default (`getattr(..., True)`) disables it unless explicitly overridden.
- **Fix:** Default `_skip_connection_lock` to False (or remove the bypass) and keep the lock enabled in production paths.

---

**Note on the trap:** Qodo did NOT flag `browser_use/_eval_trap.py` in this run. Zero false positives on the trap.
