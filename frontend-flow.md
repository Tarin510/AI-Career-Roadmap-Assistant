# Frontend Flow

This app has no separate frontend build — it's a single-page **Streamlit** app. There are
no `.html`, `.css`, or `.js` files anywhere in the project. Everything the user sees is
rendered imperatively from Python in [`main.py`](main.py), which is the only "frontend"
file. `backend.py`, `job_api.py`, `auth.py`, `history.py`, and `database.py` are the
backend modules `main.py` calls into.

## How Streamlit rendering works here

Streamlit has no client-side routing or component state of its own — on every user
interaction (button click, text input, etc.) it **reruns `main.py` top to bottom** as a
plain Python script. Persistence across reruns only happens through `st.session_state`
(an in-memory dict scoped to the browser session) and the SQLite database. There is no
virtual DOM diffing you write yourself; Streamlit's own bundled frontend (compiled
React, shipped inside the `streamlit` package) handles turning each rerun's widget tree
into the displayed page.

This means: **reading `main.py` top to bottom *is* reading the render order.** Whatever
runs earlier in the file is drawn earlier, and it uses whatever state existed in the
database/session at the moment that line executed — see the "sidebar shows stale
history" bug in `issues.md` for a concrete consequence of this.

## Where things live

| Concern | Location |
|---|---|
| Page config (title, icon, layout) | `main.py:32-37` |
| All CSS | one `<style>` block, `main.py:42-363`, injected via `st.markdown(unsafe_allow_html=True)` |
| All HTML | inline f-strings scattered through `main.py`, also injected via `unsafe_allow_html=True` |
| Render helpers (chips, roadmap, score gauge, job cards) | `main.py:413-533` |
| Auth UI (login/register tabs) | `main.py:556-603` |
| Post-login sidebar | `main.py:614-677` |
| Post-login main content | `main.py:679-800` |

There is no JavaScript written anywhere in this project.

## Session state keys in play

| Key | Set by | Meaning |
|---|---|---|
| `logged_in` | login form / session restore | gates auth screen vs. app |
| `user` | login form / session restore | tuple `(id, full_name, email, password_hash)` |
| `selected_analysis` | clicking a history entry | id of the analysis currently shown; absence means "show homepage" |
| `skills_input`, `jd_input` | text areas / "Use example" buttons / New Chat | the two textarea widget values |

Login also writes a session token into the URL (`st.query_params["session"]`) so a page
reload can restore the session via `get_user_by_session` (`main.py:545-551`).

## Top-level flow

```
main.py runs top to bottom on every interaction
│
├─ create_tables()                         (idempotent schema setup, runs every rerun)
├─ st.set_page_config(...)
├─ inject global <style> block
├─ define render helper functions
├─ init st.session_state.logged_in / .user
├─ try to restore session from ?session= URL param
│
├─ IF NOT logged_in:
│    └─ render Login/Register tabs (main.py:556-603)
│         ├─ Login tab  → auth.login_user() → on success: set session_state, write
│         │                 ?session= token, st.rerun()
│         └─ Register tab → auth.register_user()
│
└─ IF logged_in:
     ├─ SIDEBAR (main.py:614-677)
     │    ├─ user card (avatar, name, email) + Logout icon button, side by side
     │    ├─ "+ New Chat" button
     │    │     → clears selected_analysis + skills_input/jd_input, st.rerun()
     │    └─ Analysis History list
     │          → history.get_user_history(user_id)
     │          → one button per row, title = history_title() derived from
     │            recommended_jobs (fallback: first skill, fallback: "Analysis")
     │          → click sets selected_analysis + st.rerun()
     │
     └─ MAIN CONTENT (main.py:679-800)
          ├─ IF selected_analysis is set AND the row still exists:
          │     show_homepage = False
          │     → render ONLY that saved report (history.get_analysis_by_id)
          │       via render_analysis_report() — no hero/examples/form underneath
          │
          └─ IF show_homepage:
               ├─ hero ("Hey {name}", "What role are you aiming for?")
               ├─ 4 example prompt cards
               │     → "Use example" sets skills_input/jd_input session_state
               │       *before* the text_area widgets below are instantiated
               │       (Streamlit's supported way to pre-fill a widget)
               ├─ input form (skills textarea, job description textarea)
               └─ "Analyze My Career" button
                     → backend.analyze_skills(skills, jd)      [Gemini call]
                     → job_api.fetch_linkedin_jobs(jobs[:3])   [Apify call]
                     → history.save_analysis(...)              [persists row]
                     → render_analysis_report() inline, same run
```

## Analysis report rendering

`render_analysis_report()` (`main.py:499-533`) is the single function that draws a report,
used in two places: right after a fresh analysis, and when loading a saved one from
history. It always renders, in order: score donut (`render_score_gauge`), a 3-line
summary, matched/missing skill chips (`render_chips`), the roadmap timeline
(`render_roadmap`), recommended job-title chips, and LinkedIn job cards
(`render_linkedin_jobs`).

All dynamic text passed into `unsafe_allow_html=True` blocks is escaped through the local
`esc()` helper (`main.py:413-414`, a thin wrapper over `html.escape`) — **except** the
`href` on LinkedIn job links, which is escaped but not scheme-validated (see `issues.md`).

## Known issues affecting this flow

See [`issues.md`](issues.md) for the full list — most relevant to this flow:
- The sidebar history list is stale for one rerun after a fresh analysis (render-order
  issue, see "Top-level flow" above).
- A whitespace-only `full_name` crashes the entire post-login render path at the hero
  section.
