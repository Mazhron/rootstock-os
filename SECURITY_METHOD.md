# SECURITY_METHOD.md - the pre-production security audit (PORTABLE, part of the future-project kit)

PURPOSE: The pre-production security audit: one checklist, one read-only
  script and one ledger line that every app, SaaS or website with a backend,
  an API key, an env file or user data passes before it goes public, and
  again before every public release that touched secrets, auth, headers,
  config or the database rules.
INTENT: Mazhron 2026-09-29, on a survey of 100 AI-built apps: "I feel like
  this is important to note inside of Rootstock as part of the audit of an
  app, saas or website where applicable before it goes into production,
  goes out to the public, etc. We should create a file for this
  specifically ... to help keep users safe who are making them. Which could
  be me, and very will likely be me in the future when I get my
  programming job."

Founded 2026-09-29 on a Reddit survey (r/claude, u/Donchuan1998): 100
publicly launched apps built with Lovable, Bolt, Cursor and similar tools,
checked with passive, read-only requests only, what any visitor's browser
already downloads. 37 of 100 had at least one potentially exposed secret
in their frontend JavaScript (OpenAI, Stripe and Supabase credentials the
most common). 78 of 100 were missing at least one important security
header. 12 of 100 exposed a development or configuration file such as
/.git/ or .env.bak. 43 of 100 returned a wildcard CORS header. 9 of 100
had no findings. The cause the survey names: AI coding tools optimise for
"it works", not "it is safe"; the commonest pattern was an environment
variable renamed with a VITE_ or NEXT_PUBLIC_ prefix to make a build error
go away, which ships the server-side secret to every visitor. None of it
is sophisticated. It is default mistakes repeated at scale, and a
checklist catches default mistakes. Nothing in the rest of the kit looked
at this; the kit audits its own process and never the app it builds.

Search keys: security audit, secrets, API key, exposed secret, env file,
VITE_, NEXT_PUBLIC_, security headers, CSP, HSTS, CORS, .git exposed,
.env exposed, Supabase RLS, rotate a key, pre-production, go live,
production checklist, public release, source maps, rate limit.
See also: REPORTING_METHOD.md (the script and its ledger are a scripted
run), WORKFLOW_METHOD.md (the registry entry that runs the audit),
SUBAGENT_METHOD.md (the read-only employee that walks the checklist),
CONTRIBUTING.md (the purpose audit of the kit's own things, which this
is not), reference tools/security_audit.py.

## THE SECURITY AUDIT RULE
Tags: process, security, law | No app with a backend, a key, an env file or user data goes public before the audit passes; a key that was ever public is rotated, never merely removed

1. THE GATE: the audit runs, and its ledger line reads PASS or every
   FAIL is answered, BEFORE the first public release of anything that
   has a backend, an API key, an environment file, a database or user
   accounts. "Public" means a URL anyone can open, an app store listing,
   a Product Hunt or showcase post, a "look what I built" link. A
   static page with no keys and no backend is exempt and says so in
   its ledger line.
2. THE RE-RUN: the audit runs again before every public release whose
   diff touched secrets, environment files, auth, HTTP headers, CORS,
   hosting config, or database rules. The ship ritual asks; a release
   that skipped it is a ship-law breach, same as a missing changelog.
3. THE ROTATION LAW: a secret that was ever reachable by the public (in
   a bundle, a repo, a screenshot, a log, a chat) is compromised the
   moment it was reachable. The fix is to ROTATE it at the provider and
   then remove it; removing it from the code is not a fix, git history
   and every visitor's cache still hold it. Rewriting history is a
   separate decision (THE PRESERVATION LAW applies to the repo, the
   rotation does not wait for it).
4. THE PREFIX LAW: an environment variable whose name starts with
   VITE_, NEXT_PUBLIC_, REACT_APP_, PUBLIC_, EXPO_PUBLIC_, NUXT_PUBLIC_
   or GATSBY_ is bundled into the client and shipped to every visitor.
   Only a key the provider itself calls public, publishable or anon
   belongs there. A build error that a prefix would silence is a design
   error: the call belongs on the server (an API route, an edge
   function, a proxy), never in the browser.
5. THE SCRIPT AND THE LEDGER (REPORTING_METHOD): the checks a script can
   make are made by the script (reference tools/security_audit.py) and
   append to docs/history/security_audit_runs.txt; the checks a script
   cannot make (the database rules, the auth on every route, the
   dependency audit) are walked by a read-only employee from the
   checklist below and the manager writes the ledger line with the
   employee's findings. Trust the ledger: an unchanged release at a
   green line needs no re-run.
6. READ-ONLY: the audit touches only what a visitor's browser already
   downloads from YOUR OWN deployment. It never probes a site you do not
   own, never logs in, never sends a payload. It is a mirror, not a
   scanner.

## The checklist (one section per finding class; the survey's order)
Tags: security, checklist | What to check, how, and what passing looks like

### 1. Secrets in the client
- WHAT: any server-side credential in the built JavaScript, the HTML,
  the source maps or a public config file.
- HOW: build for production, then search the OUTPUT folder (dist/,
  build/, .next/static/, out/) and the live site's Sources tab for the
  patterns the script carries: `sk_live`, `sk_test`, `sk-` (OpenAI and
  Stripe secret keys), `AKIA` (AWS access key id), `service_role`
  (Supabase's admin key), `ghp_` / `github_pat_` (GitHub tokens), `AIza`
  (Google API keys, public by design but restricted by referrer or
  they bill you), `xox[bp]-` (Slack), `-----BEGIN` (a private key),
  `password=`, `secret=`, and every name from your own .env that is not
  meant to be public. Search the source maps too (`*.map`), a map ships
  the original source with its comments.
- PASS: only keys the provider calls publishable or anon appear, and
  each of those is restricted at the provider (allowed origins,
  referrers, scopes, row-level rules).
- FAIL: rotate first (rule 3), then move the call server-side.

### 2. Security headers
- WHAT: the response headers on the site's root and on one app route.
- HOW: `curl -sI https://yoursite/` (the script does this) and read:
  `Strict-Transport-Security` (HSTS: HTTPS is forced after the first
  visit); `Content-Security-Policy` (CSP: which scripts, frames and
  connections the page may load; the one header that blunts an injected
  script); `X-Frame-Options: DENY` or the CSP `frame-ancestors`
  directive (nobody can put your login page in an invisible frame);
  `X-Content-Type-Options: nosniff`; `Referrer-Policy`;
  `Permissions-Policy` (camera, microphone, geolocation off unless
  used).
- PASS: HSTS, a CSP, and a frame rule present. The others are warnings.
- FIX: hosting platforms set them in one file (vercel.json, netlify.toml,
  `_headers`, nginx.conf, a Next.js `headers()` export). A CSP is
  written strict and loosened only for the origins the console names.

### 3. Exposed files
- WHAT: files the deployment serves that were never meant to be served.
- HOW: request each path and expect 404 (or 403): `/.git/HEAD`,
  `/.git/config`, `/.env`, `/.env.local`, `/.env.production`,
  `/.env.bak`, `/.env.example` (harmless but shows your variable
  names), `/config.json`, `/config.yml`, `/backup.zip`, `/db.sqlite`,
  `/.DS_Store`, `/server.log`, `/phpinfo.php`, `/wp-config.php.bak`,
  `/.htpasswd`, `/docker-compose.yml`, `/package.json` (shows your
  dependency versions), and the `.map` next to each built script.
- PASS: every one returns 404 or 403, and a 200 on `/.git/HEAD` is a
  FAIL that outranks everything else (the whole repo, history included,
  is downloadable).
- FIX: a deny rule in the host or server config; source maps off in
  the production build, or uploaded to the error tracker only.

### 4. CORS
- WHAT: `Access-Control-Allow-Origin` on the API's responses.
- HOW: `curl -sI -H "Origin: https://evil.example" https://yourapi/route`.
- PASS: the header names your own origins, or is absent on routes that
  no browser calls. A wildcard `*` alone is a warning, not a finding;
  a wildcard together with `Access-Control-Allow-Credentials: true`,
  or an origin reflected back unchecked, is a FAIL (any site can call
  your API as the logged-in visitor).

### 5. Database rules
- WHAT: what the public key alone can read and write.
- HOW (Supabase): every table has Row Level Security ENABLED and at
  least one policy; the anon key is in the client, the service_role
  key is never. Test it: with only the anon key, `select * from` each
  table from a browser console; a table you did not mean to be public
  that returns rows is a FAIL. (Firebase): the rules are not the
  test-mode default (`allow read, write: if true`) and every collection
  has an auth check. (Any ORM with a direct connection string): the
  string is server-side only, check class 1.
- PASS: every table's public read and write matches the design, in
  writing, in the wiki.

### 6. Auth and rate limits on the server routes
- WHAT: which API routes run without a session, and what they cost.
- HOW: list every server route (API routes, edge functions, webhooks,
  cron endpoints); for each one, name who may call it and whether the
  code checks that before doing work. Call the ones that should need a
  session without one and expect 401. Any route that calls a paid
  provider (an LLM, email, SMS, a payments API) has a rate limit or a
  per-user cap, or one visitor's script runs up your bill overnight.
  Webhooks verify the provider's signature.
- PASS: every route has a named caller and a check; every paid route
  has a limit; every webhook verifies.

### 7. Dependencies and the build
- HOW: `npm audit` / `pip-audit` / `cargo audit` clean of critical and
  high; the lockfile is committed; the production build does not ship
  the dev server, the test fixtures, or a `debug=true`.

### 8. Logs, errors and telemetry
- HOW: an error page shows no stack trace to a visitor; logs sent to a
  third party carry no secrets, tokens or personal data; the analytics
  snippet is the one you chose and nothing else loads from an origin
  you cannot name.

### 9. The game and export note (Godot, Unity, web exports)
- A web export ships every script and resource in the PCK to every
  player; anything under res:// is public, an obfuscated string
  included. A leaderboard key, an itch or Steam API secret, a Discord
  webhook, an analytics write key belong in a server the game calls,
  never in a .gd, a .tres or an exported constant. A game with no
  server and no key is exempt from the gate and its ledger line says
  so ("static export, no backend, no keys").

## The ledger line
Tags: security, ledgers | One line per audit, read the tail

docs/history/security_audit_runs.txt, append-only, one line per audit:
`date time | ws | target | PASS/WARN/FAIL counts | note`. The script
writes the counts (`--record` after a run); the manager's note carries
the hand-walked verdict for classes 5-8 from the employee's report and
the count of keys rotated. A release ships against the newest line, and
the ship ritual quotes it.

## The workflow entry (paste into WORKFLOWS.md, adapt the paths)
Tags: security, workflows

```
## Audit the app for exposed secrets before a public release
WHEN: before the FIRST public URL, store listing or showcase post, and
before any release whose diff touched secrets, env files, auth, headers,
CORS, hosting config or database rules (SECURITY_METHOD.md rule 2).
STEPS:
1. `python tools/security_audit.py --dir <build output>` (class 1) and
   `python tools/security_audit.py --url https://<your site>` (classes
   2-4); read the FAIL lines.
2. One read-only employee (sonnet, /brief) walks classes 5-8 against the
   deployment's config and the route list; diff-only report.
3. Every FAIL: rotate first (rule 3), then fix, then re-run step 1.
4. `python tools/security_audit.py --record "<note>"` writes the ledger
   line from the last run's counts; quote it in the ship commit.
VERIFY: security_audit_runs.txt's tail is a PASS at this version.
See also: SECURITY_METHOD.md; the ship workflow.
```

## BOOTSTRAP (new project)
Tags: security, bootstrap

1. At STEP 0 the CEO answers: does this project have a backend, a key,
   an env file, a database or user accounts? NO: write the exemption in
   the wiki's systems index and stop here. YES: continue.
2. Copy reference tools/security_audit.py to tools/, run `--selftest`,
   add the workflow entry above to WORKFLOWS.md, and add the .env
   family to .gitignore before the first commit that could carry one.
3. Add the ship ritual's question: "did this diff touch secrets, env,
   auth, headers, CORS, hosting or database rules? then the audit runs
   first" (one line in the ship skill or WORKFLOWS "Ship a batch").
4. The first audit runs before the first public URL; its line is the
   first in security_audit_runs.txt.
