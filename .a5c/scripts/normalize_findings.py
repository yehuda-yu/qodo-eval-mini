"""Normalize raw findings into findings/{A,B,C}_run1.json.

Run from c:/Users/yehud/projects/qodo-eval-mini.
"""
import json
import os
from pathlib import Path

os.chdir("c:/Users/yehud/projects/qodo-eval-mini")

# ----- Track A (merged: /code-review + /codex:review) -----
a_findings = [
    # /code-review skill (12)
    {"id":"A_run1_001","track":"A","run":1,"file":"browser_use/cli.py","line_start":155,"line_end":156,"severity":"CRITICAL","category":"security/hardcoded-secret","title":"Hardcoded credential-shaped default for OPENAI_API_KEY","description":"DEFAULT_OPENAI_API_KEY is a literal sk-eval-... string baked into source as the fallback for os.environ.get(OPENAI_API_KEY, DEFAULT_OPENAI_API_KEY) when building the default config. Constitutes a secret-pattern in source and silently masquerades as a configured key.","raw":"DEFAULT_OPENAI_API_KEY = sk-eval-...","tool_pipeline":"/code-review"},
    {"id":"A_run1_002","track":"A","run":1,"file":"browser_use/cli.py","line_start":159,"line_end":164,"severity":"CRITICAL","category":"security/command-injection","title":"Command injection via os.system on caller-controlled URL","description":"_open_url_in_browser(url) interpolates url directly into os.system with f-string. No quoting, no scheme allow-list. URL with shell metacharacters executes attacker-chosen commands.","raw":"os.system(f'start {url}')","tool_pipeline":"/code-review"},
    {"id":"A_run1_003","track":"A","run":1,"file":"browser_use/filesystem/file_system.py","line_start":419,"line_end":423,"severity":"CRITICAL","category":"security/path-traversal","title":"Path traversal in FileSystem.read_named_file","description":"read_named_file(name) builds path as self.base_dir / name and opens it with no normalization, no dotdot rejection. Attacker-controlled name like ../../etc/passwd reads arbitrary files.","raw":"path = self.base_dir / name; open(path)","tool_pipeline":"/code-review"},
    {"id":"A_run1_004","track":"A","run":1,"file":"browser_use/browser/session.py","line_start":652,"line_end":657,"severity":"HIGH","category":"concurrency/race","title":"Race condition / TOCTOU on CDP connection lock","description":"_skip_lock = getattr(self, '_skip_connection_lock', True) defaults to True, replacing self._connection_lock with contextlib.nullcontext. Two concurrent start() calls can both observe _cdp_client_root is None and both connect.","raw":"_skip_lock = getattr(self, '_skip_connection_lock', True)","tool_pipeline":"/code-review"},
    {"id":"A_run1_005","track":"A","run":1,"file":"browser_use/llm/google/chat.py","line_start":428,"line_end":443,"severity":"HIGH","category":"error-handling/swallowed-exception","title":"Silenced ModelProviderError after retry exhaustion","description":"Retry loop wraps decision in try/except-Exception/pass and removes the terminal raise. Non-retryable status codes silently dropped. Failed Gemini calls return None.","raw":"except ModelProviderError as e: try: ... except Exception: pass","tool_pipeline":"/code-review"},
    {"id":"A_run1_006","track":"A","run":1,"file":"browser_use/agent/message_manager/service.py","line_start":148,"line_end":160,"severity":"MEDIUM","category":"correctness/off-by-one","title":"Off-by-one in agent history window","description":"Two coupled regressions: (1) total_items <= max_history_items changed to <, falling through to omit branch at boundary. (2) recent_items_count = max_history_items - 2 (was -1), shrinking displayed window by one.","raw":"if total_items < self.max_history_items: ... recent_items_count = self.max_history_items - 2","tool_pipeline":"/code-review"},
    {"id":"A_run1_007","track":"A","run":1,"file":"browser_use/sync/auth.py","line_start":37,"line_end":39,"severity":"MEDIUM","category":"security/weak-randomness","title":"Predictable device ID via random.choices","description":"device_id changed from uuid7str (UUIDv7) to random.choices over hex alphabet. Python random is Mersenne Twister, not a CSPRNG; ~600 bytes of output recovers state. Used as identity binding in cloud-sync auth.","raw":"device_id = ''.join(random.choices('0123456789abcdef', k=32))","tool_pipeline":"/code-review"},
    {"id":"A_run1_008","track":"A","run":1,"file":"browser_use/sync/auth.py","line_start":347,"line_end":356,"severity":"MEDIUM","category":"security/timing-attack","title":"Timing-leaky token comparison","description":"_check_token compares bearer token with ==. Python string equality short-circuits on first mismatching byte. Remote caller of is_authorized_request can recover token byte-by-byte.","raw":"return provided == expected","tool_pipeline":"/code-review"},
    {"id":"A_run1_009","track":"A","run":1,"file":"browser_use/tools/service.py","line_start":71,"line_end":83,"severity":"MEDIUM","category":"correctness/input-validation","title":"Removed input validation in _detect_sensitive_key_name","description":"Two guards removed: early if-not-sensitive_data-or-not-text return None gone; per-value truthiness check reduced. None.items() now raises; falsy text matches falsy values.","raw":"removed: if not sensitive_data or not text: return None","tool_pipeline":"/code-review"},
    {"id":"A_run1_010","track":"A","run":1,"file":"browser_use/utils.py","line_start":583,"line_end":590,"severity":"LOW","category":"resource-leak","title":"File handle leak in get_browser_use_version","description":"with-open(pyproject_path) replaced with bare f = open(...); never closed.","raw":"f = open(pyproject_path, encoding='utf-8')","tool_pipeline":"/code-review"},
    {"id":"A_run1_011","track":"A","run":1,"file":"browser_use/_eval_trap.py","line_start":18,"line_end":44,"severity":"LOW","category":"security/eval-usage-defensively-gated","title":"Untracked module _eval_trap.py exposing eval behind a whitelist","description":"parse_known_literal(token) calls eval(token) gated by strict membership check against fixed _ALLOWED_LITERALS. As written technically safe; flagged LOW because eval for a fixed set is gratuitous and a future maintainer adding an evaluable entry converts to RCE.","raw":"if token not in _ALLOWED_LITERALS: raise; return eval(token)","tool_pipeline":"/code-review"},
    {"id":"A_run1_012","track":"A","run":1,"file":"browser_use/browser/session.py","line_start":652,"line_end":654,"severity":"LOW","category":"code-quality/anti-pattern","title":"Default-True getattr bypass is itself a footgun","description":"_skip_lock = getattr(self, '_skip_connection_lock', True) introduces stringly-typed feature flag on a Pydantic BaseModel without declaring it as a field.","raw":"getattr(self, '_skip_connection_lock', True)","tool_pipeline":"/code-review"},
    # /codex:review (11)
    {"id":"A_run1_013","track":"A","run":1,"file":"browser_use/browser/session.py","line_start":654,"line_end":656,"severity":"HIGH","category":"concurrency","title":"Connection lock is bypassed by default (codex)","description":"_connection_lock is replaced by nullcontext() by default; concurrent start() calls race into connect() and dispatch duplicate connection events.","raw":"default-True _skip_lock => nullcontext","tool_pipeline":"/codex:review"},
    {"id":"A_run1_014","track":"A","run":1,"file":"browser_use/agent/message_manager/service.py","line_start":150,"line_end":165,"severity":"MEDIUM","category":"logic","title":"History truncation drops valid entries (codex)","description":"total_items == max_history_items truncates unnecessarily, inserts zero-omitted marker, drops one real history item.","raw":"<= -> <; -1 -> -2","tool_pipeline":"/codex:review"},
    {"id":"A_run1_015","track":"A","run":1,"file":"browser_use/llm/google/chat.py","line_start":429,"line_end":443,"severity":"HIGH","category":"error-handling","title":"Google provider errors can be swallowed (codex)","description":"Non-retryable or exhausted ModelProviderErrors no longer raise; method falls through and implicitly returns None.","raw":"except ModelProviderError ... try/except Exception: pass","tool_pipeline":"/codex:review"},
    {"id":"A_run1_016","track":"A","run":1,"file":"browser_use/cli.py","line_start":155,"line_end":156,"severity":"MEDIUM","category":"security/secret","title":"Hardcoded credential-shaped OpenAI key (codex)","description":"Missing OpenAI config falls back to a source-code sk-eval... value, masking config errors.","raw":"DEFAULT_OPENAI_API_KEY","tool_pipeline":"/codex:review"},
    {"id":"A_run1_017","track":"A","run":1,"file":"browser_use/cli.py","line_start":159,"line_end":164,"severity":"LOW","category":"security/command-injection","title":"URL opener uses shell interpolation (codex, charitable)","description":"_open_url_in_browser uses os.system. Current call is constant, helper reuse with input would be command-injection prone.","raw":"os.system(f'start {url}')","tool_pipeline":"/codex:review"},
    {"id":"A_run1_018","track":"A","run":1,"file":"browser_use/filesystem/file_system.py","line_start":419,"line_end":423,"severity":"HIGH","category":"security/path-traversal","title":"Path traversal in new file reader (codex)","description":"read_named_file joins caller-controlled name to base_dir without validation; ../ escapes if exposed.","raw":"path = self.base_dir / name","tool_pipeline":"/codex:review"},
    {"id":"A_run1_019","track":"A","run":1,"file":"browser_use/sync/auth.py","line_start":37,"line_end":39,"severity":"MEDIUM","category":"security/randomness","title":"Device IDs use non-cryptographic randomness (codex)","description":"random.choices replaced uuid7str for auth/sync device identity; random is predictable.","raw":"random.choices('0123456789abcdef', k=32)","tool_pipeline":"/codex:review"},
    {"id":"A_run1_020","track":"A","run":1,"file":"browser_use/sync/auth.py","line_start":347,"line_end":356,"severity":"MEDIUM","category":"security/timing","title":"Token comparison is not constant-time (codex)","description":"Auth token comparison uses == while claiming constant-time behavior.","raw":"return provided == expected","tool_pipeline":"/codex:review"},
    {"id":"A_run1_021","track":"A","run":1,"file":"browser_use/tools/service.py","line_start":71,"line_end":82,"severity":"MEDIUM","category":"correctness/validation","title":"Sensitive-data detection crashes on None (codex)","description":"Removed guards mean sensitive_data=None raises on .items(); falsy secret values now misattributed.","raw":"for ... in sensitive_data.items()","tool_pipeline":"/codex:review"},
    {"id":"A_run1_022","track":"A","run":1,"file":"browser_use/utils.py","line_start":584,"line_end":590,"severity":"LOW","category":"resource-leak","title":"Version file handle leak (codex)","description":"pyproject.toml is opened without a context manager and returned from before deterministic close.","raw":"f = open(pyproject_path, encoding='utf-8')","tool_pipeline":"/codex:review"},
    {"id":"A_run1_023","track":"A","run":1,"file":"browser_use/_eval_trap.py","line_start":29,"line_end":44,"severity":"LOW","category":"code-quality","title":"Untracked helper uses unnecessary eval (codex, charitable)","description":"parse_known_literal is currently whitelisted and unreferenced; eval is unnecessary and fragile if whitelist changes.","raw":"return eval(token)","tool_pipeline":"/codex:review"},
]

a = {
    "track": "A",
    "run": 1,
    "tool_pipeline": "/code-review skill ⊕ /codex:review skill (codex CLI sandbox via codex:rescue agent)",
    "scope": "diff vs pinned SHA on branch eval-uncommitted",
    "scope_files": [
        "browser_use/_eval_trap.py",
        "browser_use/agent/message_manager/service.py",
        "browser_use/browser/session.py",
        "browser_use/cli.py",
        "browser_use/filesystem/file_system.py",
        "browser_use/llm/google/chat.py",
        "browser_use/sync/auth.py",
        "browser_use/tools/service.py",
        "browser_use/utils.py",
    ],
    "findings": a_findings,
}
Path("findings/A_run1.json").write_text(json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Track A: {len(a_findings)} findings -> findings/A_run1.json")

# ----- Track B (Qodo Gen, 10 findings) -----
b_findings = [
    {"id":"B_run1_001","track":"B","run":1,"file":"browser_use/cli.py","line_start":155,"line_end":256,"severity":"high","category":"Security vulnerability","title":"Hardcoded OPENAI_API_KEY default leaks credential-shaped secret and can be used unintentionally","description":"DEFAULT_OPENAI_API_KEY is a literal sk-... string and is used as a fallback when OPENAI_API_KEY is unset, which can accidentally route requests using a baked-in key-like value.","raw":"DEFAULT_OPENAI_API_KEY = 'sk-eval-...'","qodo_category_tag":"Security vulnerability"},
    {"id":"B_run1_002","track":"B","run":1,"file":"browser_use/cli.py","line_start":159,"line_end":164,"severity":"high","category":"Security vulnerability","title":"Command injection via os.system in _open_url_in_browser()","description":"_open_url_in_browser() interpolates url directly into os.system() without quoting/validation; shell metacharacters execute arbitrary commands.","raw":"os.system(f'start {url}')","qodo_category_tag":"Security vulnerability"},
    {"id":"B_run1_003","track":"B","run":1,"file":"browser_use/filesystem/file_system.py","line_start":419,"line_end":423,"severity":"high","category":"Security vulnerability","title":"Path traversal in FileSystem.read_named_file() allows sandbox escape","description":"read_named_file() joins self.base_dir / name and opens it directly; .. segments or absolute paths read arbitrary host files outside intended base directory.","raw":"path = self.base_dir / name; open(path)","qodo_category_tag":"Security vulnerability"},
    {"id":"B_run1_004","track":"B","run":1,"file":"browser_use/sync/auth.py","line_start":37,"line_end":39,"severity":"high","category":"Security vulnerability","title":"Predictable device_id generation weakens sync auth identity","description":"get_or_create_device_id() switches from uuid7str() to random.choices(...), not cryptographically secure; enables device-id spoofing.","raw":"device_id = ''.join(random.choices(...))","qodo_category_tag":"Security vulnerability"},
    {"id":"B_run1_005","track":"B","run":1,"file":"browser_use/sync/auth.py","line_start":347,"line_end":356,"severity":"medium","category":"Security vulnerability","title":"Non-constant-time token comparison enables timing attacks","description":"_check_token() uses == for secret comparison; short-circuits and leaks information via timing differences when used on auth/webhook paths.","raw":"return provided == expected","qodo_category_tag":"Security vulnerability"},
    {"id":"B_run1_006","track":"B","run":1,"file":"browser_use/agent/message_manager/service.py","line_start":148,"line_end":160,"severity":"high","category":"Potential bug","title":"Off-by-one history truncation drops valid items and shortens window","description":"Changing <= to < and reducing recent_items_count by an extra 1 causes the history view to omit an item when total_items == max_history_items and shows fewer recent items than intended.","raw":"if total_items < ...; -2","qodo_category_tag":"Potential bug"},
    {"id":"B_run1_007","track":"B","run":1,"file":"browser_use/llm/google/chat.py","line_start":428,"line_end":443,"severity":"high","category":"Potential bug","title":"ModelProviderError is silently swallowed when non-retryable or retries exhausted","description":"Retry logic now catches ModelProviderError but no longer re-raises when not retrying; callers may get None/unexpected behavior instead of an exception.","raw":"except ModelProviderError ... try/except Exception: pass","qodo_category_tag":"Potential bug"},
    {"id":"B_run1_008","track":"B","run":1,"file":"browser_use/tools/service.py","line_start":71,"line_end":83,"severity":"medium","category":"Potential bug","title":"_detect_sensitive_key_name can crash when sensitive_data is None and mis-attribute falsy values","description":"Removing the early guard means sensitive_data.items() raises AttributeError when sensitive_data is None; removed if value checks let empty/None values match unexpectedly.","raw":"removed early return; .items() on None","qodo_category_tag":"Potential bug"},
    {"id":"B_run1_009","track":"B","run":1,"file":"browser_use/utils.py","line_start":583,"line_end":590,"severity":"medium","category":"Potential bug","title":"File descriptor leak in get_browser_use_version() due to missing context manager","description":"Opening pyproject.toml without with leaks the file handle on success and failure paths.","raw":"f = open(pyproject_path, encoding='utf-8')","qodo_category_tag":"Potential bug"},
    {"id":"B_run1_010","track":"B","run":1,"file":"browser_use/browser/session.py","line_start":654,"line_end":656,"severity":"high","category":"Potential bug","title":"Connection lock is skipped by default, reintroducing concurrent connect race","description":"_skip_connection_lock defaults to True; real _connection_lock replaced with nullcontext(); concurrent start() calls race into _cdp_client_root is None and connect twice.","raw":"_skip_lock = getattr(self, '_skip_connection_lock', True)","qodo_category_tag":"Potential bug"},
]

b = {
    "track": "B",
    "run": 1,
    "tool": "Qodo Gen VS Code plugin -- Review uncommitted changes",
    "scope": "diff vs pinned SHA on branch eval-uncommitted",
    "scope_files": [
        "browser_use/agent/message_manager/service.py",
        "browser_use/browser/session.py",
        "browser_use/cli.py",
        "browser_use/filesystem/file_system.py",
        "browser_use/llm/google/chat.py",
        "browser_use/sync/auth.py",
        "browser_use/tools/service.py",
        "browser_use/utils.py",
        "browser_use/_eval_trap.py",
    ],
    "findings": b_findings,
}
Path("findings/B_run1.json").write_text(json.dumps(b, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Track B: {len(b_findings)} findings -> findings/B_run1.json")

# ----- Track C (community, 11 findings) -----
c_findings = [
    {"id":"C_run1_001","track":"C","run":1,"file":"browser_use/browser/session.py","line_start":649,"line_end":659,"severity":"blocking","category":"concurrency","title":"Race condition -- connection lock replaced with nullcontext by default","description":"_skip_connection_lock looked up with getattr(..., True) -- default True; every BrowserSession instance not explicitly setting attribute uses nullcontext() instead of self._connection_lock. Two concurrent callers race into connect().","raw":"_skip_lock = getattr(self, '_skip_connection_lock', True)"},
    {"id":"C_run1_002","track":"C","run":1,"file":"browser_use/agent/message_manager/service.py","line_start":150,"line_end":158,"severity":"blocking","category":"logic","title":"Off-by-one in history window -- items silently dropped","description":"Two coordinated errors: <= -> < at boundary; recent_items_count -1 -> -2. LLM sees fewer history items than configured; context silently lost.","raw":"if total_items < ...; recent_items_count = self.max_history_items - 2"},
    {"id":"C_run1_003","track":"C","run":1,"file":"browser_use/llm/google/chat.py","line_start":426,"line_end":447,"severity":"blocking","category":"error-handling","title":"Silent error swallow -- non-retryable ModelProviderErrors discarded","description":"Restructured handler wraps retry-decision in try/except Exception: pass. Non-retryable or exhausted-retry ModelProviderError no longer raises. Caller never receives an exception.","raw":"except ModelProviderError ... try/except Exception: pass"},
    {"id":"C_run1_004","track":"C","run":1,"file":"browser_use/cli.py","line_start":155,"line_end":256,"severity":"blocking","category":"security/secret","title":"Hardcoded API key default committed to source","description":"DEFAULT_OPENAI_API_KEY = 'sk-eval-...' baked into source. os.environ.get('OPENAI_API_KEY', DEFAULT_OPENAI_API_KEY) without env var passes literal downstream. Secret scanners flag it.","raw":"DEFAULT_OPENAI_API_KEY = 'sk-eval-DO-NOT-USE-...'"},
    {"id":"C_run1_005","track":"C","run":1,"file":"browser_use/cli.py","line_start":159,"line_end":165,"severity":"blocking","category":"security/command-injection","title":"Command injection via os.system with unsanitized URL","description":"os.system(f'start {url}') / os.system(f'xdg-open {url}') passes url directly to shell without quoting. URL like 'https://x.com && rm -rf ~' executes arbitrary commands.","raw":"os.system(f'start {url}')"},
    {"id":"C_run1_006","track":"C","run":1,"file":"browser_use/filesystem/file_system.py","line_start":417,"line_end":422,"severity":"blocking","category":"security/path-traversal","title":"Path traversal in read_named_file -- arbitrary host file read","description":"path = self.base_dir / name then open(path, 'r') with no further validation. name like '../../etc/passwd' resolves outside base_dir. No commonpath/resolve guard.","raw":"path = self.base_dir / name; open(path, 'r')"},
    {"id":"C_run1_007","track":"C","run":1,"file":"browser_use/utils.py","line_start":583,"line_end":590,"severity":"important","category":"resource-leak","title":"Resource leak -- file handle not closed on early return","description":"Refactored code opens pyproject_path with bare open() (no with, no try/finally). On return version path the file handle f is never closed.","raw":"f = open(pyproject_path, encoding='utf-8'); ... return version"},
    {"id":"C_run1_008","track":"C","run":1,"file":"browser_use/sync/auth.py","line_start":37,"line_end":38,"severity":"important","category":"security/randomness","title":"Weak PRNG for device identity -- predictable device IDs","description":"device_id generated with random.choices over hex alphabet of length 32. MT19937 not a CSPRNG; ~624 outputs reconstruct internal state. Used in cloud sync OAuth2 Device Authorization Grant.","raw":"''.join(random.choices('0123456789abcdef', k=32))"},
    {"id":"C_run1_009","track":"C","run":1,"file":"browser_use/tools/service.py","line_start":71,"line_end":85,"severity":"important","category":"correctness/validation","title":"Missing null guard -- AttributeError/TypeError when sensitive_data is None","description":"Early-exit guard removed. sensitive_data is None raises AttributeError on .items(). Falsy values now participate in equality comparisons, causing incorrect sensitive-key attribution.","raw":"removed early return; .items()"},
    {"id":"C_run1_010","track":"C","run":1,"file":"browser_use/sync/auth.py","line_start":347,"line_end":355,"severity":"important","category":"security/timing","title":"Timing side-channel in token comparison","description":"_check_token uses provided == expected; short-circuits on first mismatching byte. Remote attacker on sync webhook/auth endpoint can recover token byte-by-byte. Outer is_authorized_request docstring promises 'constant-time check'.","raw":"return provided == expected"},
    {"id":"C_run1_011","track":"C","run":1,"file":"browser_use/_eval_trap.py","line_start":37,"line_end":44,"severity":"blocking","category":"security/eval","title":"eval whitelist bypassable via str subclass with overridden __eq__","description":"Python 'in' operator for tuple calls __eq__ on the token (LHS), not on whitelist strings. A str subclass overriding __eq__ to always return True passes both isinstance and the membership check; eval(token) then receives arbitrary Python.","raw":"if token not in _ALLOWED_LITERALS: raise; return eval(token)"},
]

c = {
    "track": "C",
    "run": 1,
    "tool": "awesome-skills/code-review-skill (code-review-excellence)",
    "scope": "diff vs pinned SHA on branch eval-uncommitted",
    "scope_files": [
        "browser_use/_eval_trap.py",
        "browser_use/agent/message_manager/service.py",
        "browser_use/browser/session.py",
        "browser_use/cli.py",
        "browser_use/filesystem/file_system.py",
        "browser_use/llm/google/chat.py",
        "browser_use/sync/auth.py",
        "browser_use/tools/service.py",
        "browser_use/utils.py",
    ],
    "findings": c_findings,
}
Path("findings/C_run1.json").write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Track C: {len(c_findings)} findings -> findings/C_run1.json")

print(f"\nTotal: {len(a_findings) + len(b_findings) + len(c_findings)} findings across 3 tracks")
