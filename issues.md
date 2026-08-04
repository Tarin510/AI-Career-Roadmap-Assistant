# Known Issues

Findings from a full code review + live reproduction of the app (Streamlit, `main.py` as
the entry point). Ordered by severity. File:line references point at the code as of this
review — re-check line numbers if the file has changed since.

## 🔴 Critical — crashes the whole app

### Whitespace-only name crashes on every login
**File:** `main.py:706`

```python
first_name = full_name.split()[0] if full_name else "there"
```

`if full_name` only checks the string is non-empty, not that it has real content.
Registration (`auth.py:9`, `register_user`) never trims or validates the name field, so a
user who types a single space `" "` as their full name passes the `if full_name and
reg_email and reg_password` check on the register form and gets stored as-is.

On every subsequent login, `full_name.split()` returns `[]` (splitting whitespace-only
text yields no tokens), so `[0]` raises `IndexError: list index out of range`. The app
crashes with a raw Python traceback instead of rendering the homepage — the account
becomes permanently unusable without a direct database edit.

**Reproduced live:** registered with full name `" "`, logged in, got:
```
IndexError: list index out of range
File "main.py", line 706, in <module>
    first_name = full_name.split()[0] if full_name else "there"
```

**Fix direction:** validate/strip `full_name` on registration (reject if `full_name.strip()`
is empty), and/or guard the split at line 706 with `full_name.split()[0] if full_name.strip()
else "there"`.

---

## 🟠 High

### LinkedIn job links aren't scheme-validated before rendering as `<a href>`
**File:** `main.py:487`, data sourced from `job_api.py:33`

```python
f'<a class="job-link" href="{esc(link)}" target="_blank" rel="noopener noreferrer">View Job →</a>'
```

`esc()` (`html.escape`) neutralizes `<`, `>`, `&`, and quotes, but it does **not**
neutralize a `javascript:` URI scheme. `link` comes straight from the Apify LinkedIn
scraper's raw output (`job_api.py:33`, `item.get("jobUrl", item.get("link", ""))`) with no
`http(s)://` check before it's rendered. If the scraper ever returns (or is fed) a
`javascript:` URL, it would render as a normal-looking clickable link that executes script
on click.

Likelihood is low given the data source is a specific scraping actor, but there is
currently no defense at all.

**Fix direction:** before rendering, only treat `link` as clickable if it starts with
`http://` or `https://`; otherwise omit the link.

### New analysis doesn't appear in the sidebar until another click
**File:** `main.py:659` (sidebar history fetch) vs `main.py:783` (`save_analysis` call)

Streamlit reruns the whole script top-to-bottom on every interaction. The sidebar's
`get_user_history(user_id)` call sits earlier in the file than the "Run Analysis" handler,
so on the same run where the user clicks **Analyze My Career**, the sidebar is drawn
*before* `save_analysis(...)` has inserted the new row. The report renders correctly in the
main panel, but the new entry is silently missing from "Analysis History" until the next
click/rerun — it looks like the save silently failed even though it didn't.

**Fix direction:** after `save_analysis`, either `st.rerun()` (and point
`selected_analysis` at the new row so the just-completed report reloads from history), or
refetch/append to the sidebar list before it renders.

---

## 🟡 Medium

### `rows` parameter is silently ignored
**File:** `job_api.py:12-20`

```python
def fetch_linkedin_jobs(search_query, location="Bangladesh", rows=10):
    run_input = {
        "searchKeywords": search_query,
        "location": location
    }
```

`rows` is accepted as a parameter but never added to `run_input`. The `rows=10` passed in
from `main.py:777` does nothing — the actor runs with whatever its own default result cap
is, not the one the caller asked for.

**Fix direction:** find the actor's actual input key for a result cap (commonly
`maxItems` or similar for Apify actors) and include it in `run_input`.

### Session tokens live in the URL and never expire
**File:** `main.py:580`, `auth.py:82-97`

```python
st.query_params["session"] = create_session(user[0])
```

The raw session token is placed directly in the browser's address bar, where it persists
in browser history and any synced-history feature. `sessions` rows in the database are
only ever deleted on explicit logout (`delete_session`) — there is no expiry column or
cleanup job. A leaked URL is effectively a permanent login for whoever has it.

**Fix direction:** add an expiry timestamp to `sessions` and check it in
`get_user_by_session`; consider periodic cleanup of stale rows.

### History timestamps are shown in UTC, not the user's local time
**File:** `database.py:48` (`CURRENT_TIMESTAMP`), `main.py:429` (`format_history_label`)

SQLite's `CURRENT_TIMESTAMP` default stores UTC. `format_history_label` displays
`created_at` as-is with no timezone conversion. Verified live on a UTC+6 machine: every
timestamp shown in the sidebar was 6 hours behind the actual wall-clock time the analysis
was run.

**Fix direction:** either store timezone-aware timestamps, or convert at display time using
a known/user-configured offset.

---

## ⚪ Low / hygiene

- **Email isn't normalized** — `register_user` (`auth.py:9`) doesn't lowercase or trim
  `email`/`full_name`, so `User@x.com` and `user@x.com` register as two different accounts.
- **`create_tables()` runs on every single interaction** (`main.py:27`) — opens/closes a
  fresh SQLite connection and re-checks the schema on every button click, not just app
  startup. Harmless but wasteful.
- **No `try/finally` around DB connections** (all of `history.py` / `auth.py`) — a
  mid-query exception would leak an unclosed `sqlite3` connection instead of closing it.
- **Unpinned dependencies** (`requirements.txt`) — no version pins at all. For example,
  `apify-client`'s `ActorClient.call()` return type has changed across major versions
  (plain `dict` in older releases vs. a typed `Run` model in the currently installed
  `3.0.6`); an unpinned upgrade/downgrade could silently break `job_api.py`'s
  `run.default_dataset_id` attribute access.
