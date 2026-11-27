# SECURITY_KNOWLEDGE.md - the security knowledge base (PORTABLE, part of the future-project kit)

PURPOSE: The security knowledge base: one growing, numbered list of
  security practices learned by building real programs, each with its
  rule, its why, how it is built and how it is checked, carried from
  project to project so a new program starts with every wall the last
  one had to learn.
INTENT: Mazhron 2026-11-26, the day a scanner's visit showed two gaps in a
  live sign-in page: "please begin keeping a specific knowledge base for
  security. I want to have a list of security things that I can take from
  project to project as I go".

SECURITY_METHOD.md is the GATE: a mirror held up to a deployment before it
goes public (what a visitor's browser can already see). This file is the
WALLS: what is built into the program itself, and why. The audit asks "is
anything showing"; the knowledge base answers "what should have been built
so that nothing is". A project reads this file when it designs sign-in,
sessions, rights, uploads or its deploy, and writes to it the day it
learns something.

Search keys: security knowledge, knowledge base, security list, sign-in,
login, password, argon2, session, cookie, two-factor, verification code,
rate limit, wrong password, block an address, probing, scanner, safe
list, real client address, proxy, permissions, rights, audit trail,
secrets, env file, headers, CSP, HSTS, uploads, npm audit, backup,
restore, known gaps.
See also: SECURITY_METHOD.md (the pre-production audit, the gate this file
is the walls for), WIKI_METHOD.md (the entry and heading rules),
WORKFLOW_METHOD.md (the registry entry at the bottom of this file),
UPGRADES.md (how a new entry travels to an installed project).

## THE KNOWLEDGE RULE
Tags: process, security, law | A security thing learned is written here the day it is learned; an entry says how it is checked or it is not an entry

1. THE DAY IT IS LEARNED: a security finding, a security ruling by the
   owner, a fix for a security bug, or a scanner's visit that taught
   something lands here as an entry in the same batch as the fix or the
   ruling, never "later". The project's own lesson book keeps the story
   of the mistake; this file keeps the rule that outlives the project.
2. ONE ENTRY, FIVE LINES: RULE (one sentence, true for any project), WHY
   (what went wrong, or what it prevents), HOW (the way it was built),
   CHECK (the test or the read that proves it is still true), GROWN (the
   month and the kind of project, never its name).
3. THE STATUS IS HONEST: PROVEN means built and running in a real
   program, read in its code the day the entry was written. RULED means
   the owner decided it and the build is pending. OPEN means a known gap
   with nothing decided. An entry is never written as PROVEN from a
   plan, and a RULED entry is raised to PROVEN the day it is built and
   its check first passes. An entry built in part keeps the lower
   status, and its HOW says which part stands today.
   A CHECK line says how to prove the entry in
   any project; it is not a claim that the test exists in the project
   the entry grew in.
4. WHAT STAYS HOME: no real address, host name, person, client, key,
   password or log line enters this file. An example address comes from
   the documentation ranges (203.0.113.0/24, 198.51.100.0/24) and an
   example host is example.com. This file is published with the kit.
5. THE NUMBER IS THE NAME: entries are numbered K-1, K-2 and on, never
   renumbered and never removed. A rule that turned out wrong is marked
   SUPERSEDED with the number of the entry that replaced it.
6. BEFORE A DESIGN: a contract for sign-in, sessions, rights, uploads,
   a public page or a deploy names the K entries it follows and any it
   departs from, with the reason. An OPEN entry the design touches is
   put to the owner as a question.
7. UP TO THE KIT: an entry that is true beyond its project goes up to
   Rootstock by a release (CONTRIBUTING.md says how one is made). An
   installed project receives new entries as a graft: the new numbers
   are added to its copy, its own entries are kept.

See also: "How an entry is added" at the bottom of this file;
SECURITY_METHOD.md "THE SECURITY AUDIT RULE".

## Sign-in and passwords
Tags: security, sign-in, password | How a password is kept and how a sign-in page answers a guess

### K-1 A password is stored only as an argon2id hash [PROVEN]
- RULE: the database holds an argon2id hash of a password and nothing
  else; the password is never stored, logged or shown again.
- WHY: a copied table must not hand out passwords, and people reuse them.
- HOW: argon2id at 64 MiB, 3 passes, 1 lane, which is above the
  minimums OWASP publishes (19 MiB and 2 passes); read the current
  minimums the day you build, they rise. A
  hash made with older parameters still verifies, so the cost is raised
  later without a reset. A floor of 12 characters before hashing.
- CHECK: a test hashes, verifies, rejects a wrong password and reads the
  stored value's prefix; grep the schema for any second password column.
- GROWN: 2026-11, a multi-company business web program.

### K-2 A one-time code is short-lived, counted and stored as a hash [PROVEN]
- RULE: a verification or two-factor code has six digits, ten minutes
  and five tries, and only its hash is stored.
- WHY: a code with no limit of tries is a six-digit password anyone can
  walk through.
- HOW: the tries are counted with the code, and past the limit the
  answer is a refusal whatever was typed. In production, with no
  provider set to send the code, the request is refused; it never
  pretends it sent.
  The hash is a keyed one (an HMAC with a server secret) where it can
  be: a plain hash of six digits is walked in a million tries by
  anyone holding the table. The program this grew in stores a plain
  one, so there the short life and the count of tries are what
  protect it.
- CHECK: a test spends five wrong tries and then offers the right code.
- GROWN: 2026-11, a multi-company business web program.

### K-3 Wrong passwords are counted per address as well as per account [PROVEN]
- RULE: a wrong e-mail or password is counted against the address
  that sent it, beside the count against the account; the fourth
  wrong try from one address blocks that address for one hour.
- WHY: a count per account alone lets a guesser spread tries over many
  accounts unseen. The map of counts also grows by one key for every
  made-up e-mail unless it is capped.
- HOW: two counters, each map capped in size. The count by address
  has a window (four wrong tries inside fifteen minutes), a wrong
  e-mail counts the same as a wrong password, and a right password
  clears it. The block is K-9's timed block, not K-7's standing one.
  A wrong second-factor code is counted against the account only in
  the program this grew in; counting it by address too is a known
  next step there.
  The count per account stays beside the new one, and it has a cost
  to keep in view: anyone who knows a person's e-mail can lock that
  person out for the length of the account's lock by typing it
  wrong, so that lock is short and the count by address does the
  real work.
- CHECK: a test sends four wrong passwords for four different accounts
  from one address and reads the block; a fifth from a second address
  still gets a plain "wrong password".
- GROWN: 2026-11, ruled the day a scanner's visit was read and built
  that night.

### K-4 A sign-in page says the same thing for a wrong e-mail and a wrong password [OPEN]
- RULE: the answer to a failed sign-in does not tell a stranger whether
  the account exists.
- WHY: a different answer turns the sign-in page into a list of who has
  an account.
- HOW: not on record yet in any project; write the HOW when it is read
  against a real sign-in route.
- CHECK: none yet.
- GROWN: 2026-11, noted the day this file was founded.

See also: "Limits, blocks and probing" below; SECURITY_METHOD.md checklist
class 6 (auth on every route).

## Sessions and cookies
Tags: security, session, cookie | What a signed-in browser holds and what the database keeps

### K-5 The browser holds a random token; the database holds only its hash [PROVEN]
- RULE: a session is a random token in an HttpOnly cookie, and the
  session table stores the token's sha256, never the token.
- WHY: a copy of the table (a backup, a dump, a leak) signs nobody in,
  and a script in the page cannot read the cookie.
- HOW: the cookie is HttpOnly, SameSite=Lax, and Secure in production
  (off only for a local http server). A session idles out after a set
  number of hours without a request and ends for good after a set
  number of days. A password change revokes the user's other sessions.
- CHECK: a test signs in, reads the table and fails to sign in with the
  stored value; the browser's cookie list shows HttpOnly and Secure on
  the live address.
- GROWN: 2026-11, a multi-company business web program.

### K-6 A long-lived connection refuses another site's page [PROVEN]
- RULE: a route that holds a connection open (live updates, a stream)
  refuses a request whose Sec-Fetch-Site says it came from another site.
- WHY: SameSite=Lax still sends the cookie to a sibling subdomain's
  page, which could hold lines open in a visitor's browser.
- HOW: after the sign-in check, refuse 403 unless Sec-Fetch-Site is
  absent, "same-origin" or "none".
- CHECK: a test sends the request with Sec-Fetch-Site: same-site and
  cross-site and reads 403.
- GROWN: 2026-11, a multi-company business web program.

See also: K-28 (no token against cross-site writes is on record yet).

## Limits, blocks and probing
Tags: security, rate limit, block, probing, scanner | What a stranger's address may ask for, how often, and what is written down about it

### K-7 A blocked address is refused before anything reads a cookie [PROVEN]
- RULE: the block check is the first thing a request meets, ahead of
  sessions, routes and static files.
- WHY: a blocked address should cost the server nothing and learn
  nothing, and a block that runs after the session code can be dodged
  by whatever that code does first.
- HOW: the standing blocks are a set in memory, reloaded after every
  block and every lift; an API path answers 403 as JSON, any other path
  403 as plain text.
- CHECK: a test blocks an address and asks for a page, an API route and
  a static file from it.
- GROWN: 2026-11, a multi-company business web program.

### K-8 An address the program does not have answers Not Found [PROVEN]
- RULE: a path that is not a real route or a real built file answers
  404, never the start page or the sign-in page with 200.
- WHY: a single-page client is often served by "any other GET answers
  index.html". A scanner asking for /admin.php or /wp-login.php then
  reads 200 and keeps digging; the logs fill and the scanner believes
  the file is there. A client that routes by hash needs only "/" and its
  built files to answer.
- HOW: list what may answer 200 (the start page, the built files, the
  API) and send everything else to 404: JSON under the API's prefix,
  plain text elsewhere, never the start page. Paths with a part that
  starts with a dot (/.env, /.git/config, also "%2e") were the first
  case built. A test or a smoke check that asked for a client route
  by its path and read the page is turned round in the same batch:
  one of ours printed a pass over a wrong reading until its lines
  were read.
  What a browser asks for by itself (the list in K-9) answers 404 too
  and is never counted against the visitor.
- CHECK: a test asks for a made-up path, a dotfile path and an encoded
  dotfile path and reads 404 on each.
- GROWN: 2026-11, found by reading a scanner's requests.

### K-9 Probing earns a one-hour block, never a permanent one by itself [PROVEN]
- RULE: an address that is not signed in and not on the safe list, and
  that asks five times in ten minutes for things the program does not
  have (or sends wrong passwords, or too many account requests), is
  flagged and blocked for one hour. A permanent block is a person's
  decision.
- WHY: one mistyped address is not an attack, an automatic permanent
  block locks out the next person to get that address, and no block at
  all lets a scanner run all night.
- HOW: a counter per address with a window. The timed block is a
  check of its own with an end time, kept on the address's record
  (K-11) so a restart keeps it, and it runs AFTER the session is
  read: that is what lets a person already signed in keep working,
  and why it is not K-7's block, which runs first. It lifts by
  itself when the hour has passed. Wrong passwords have their own
  window (K-3) and are not counted here a second time.
  Paths a browser or a phone asks for by itself
  never count: /favicon.ico, /robots.txt, the apple-touch-icon names,
  /.well-known/ and the like; without that list an ordinary
  visitor's first page load is most of the way to a block. Sign-in from the address stops for the hour; a
  person already signed in from it keeps working; a super user can
  lift it early.
- CHECK: a test sends five made-up paths in the window and reads the
  block, then moves the clock one hour and reads the page again.
- GROWN: 2026-11, the owner's ruling after a scanner's visit.

### K-10 A safe address is never limited [PROVEN]
- RULE: an address on the owner's safe list is exempt from every
  automatic limit and block that is counted by address.
- WHY: an office shares one address, so four people mistyping a
  password must not lock the whole office out; and the owner must not
  be blocked from the program by its own guard.
- HOW: the safe list is read before every counter by address; the
  owner's own address and the office's go on it before the limits
  ship. The count per account (K-3) still stands for a safe address,
  so a guest on the office network cannot guess one account's
  password without limit. The list is only as true as K-12: where a
  forwarded header can be forged, anyone can claim a safe address.
  An address made safe while its hour runs is let in at once. In the
  program this grew in the limits shipped before the owner's address
  was listed, and the scan from outside then had to wait: its own
  asks would have blocked the owner for an hour.
- CHECK: a test sends ten wrong passwords for ten different accounts
  from a safe address and reads no block on the address.
- GROWN: 2026-11, the owner's ruling.

### K-11 The odd addresses are written down where a restart cannot lose them [PROVEN]
- RULE: every address that was flagged has a record: what it asked
  for, how many requests, how many one-hour blocks; and the record is
  on a screen the owner can read.
- WHY: a scanner's visit was found only by chance in the server's own
  log, and a count held in memory is gone at the next deploy.
- HOW: a table, not a map in memory; one row per address with its
  counts, the end of its block and the last fifty different paths it
  asked for, each cut to a fixed length. An ask refused during a
  block is counted in memory and added to the row at the next
  refused ask once ten seconds have passed, and at shutdown, so a
  blocked scanner does not cost one write an ask. A read-only
  command prints the same rows for the day the
  screen cannot be reached.
- CHECK: a test flags an address, restarts the app and reads the row.
- GROWN: 2026-11, the owner's ruling.

### K-12 Every limit by address depends on the real address [PROVEN]
- RULE: behind a proxy or a front door, the program must read the
  visitor's real address before any rule by address means anything.
- WHY: with the proxy setting wrong, every sign-in showed the front
  door's own address: one block would have blocked everyone, and the
  log named no one.
- HOW: the framework's trust-proxy setting is tried on a bare instance
  of the INSTALLED version, and its source read, before the code names
  a value: one framework version turned a bare hop count into "trust
  nobody". The proxy is named by where it calls from (the private
  range its network sits on), never "trust everything".
- CHECK: three test lines, never one: the trusted proxy's forwarded
  header is read; with no setting nothing is read; a caller from
  outside the trusted range is not believed. Then sign in from outside
  and read the recorded address: it is yours, not the proxy's.
- GROWN: 2026-11, a multi-company business web program.

### K-13 An open form is limited per address [PROVEN]
- RULE: a form that needs no sign-in (ask for an account, forgot my
  password, contact) is limited per address, three an hour.
- WHY: an open form is a free way to fill a table or send mail.
- HOW: a counter per address on the route; K-10's safe list is exempt.
  A request is counted after the form's own checks pass and before
  the e-mail is looked up, so a mistyped form does not use up the
  three and a refusal says nothing about who has an account. The
  program this grew in has one open form, the request for an
  account; a forgot-my-password or a contact form takes the same
  counter the day it is added.
- CHECK: a test sends four requests in the hour and reads the refusal.
- GROWN: 2026-11, the owner's ruling.

### K-14 A report endpoint is limited and never explains itself [PROVEN]
- RULE: an endpoint that takes reports from browsers with no sign-in
  (CSP reports) has a small body limit, a limit per address per
  minute, and one answer for everything.
- WHY: it is an open door for anyone to write to your log.
- HOW: over the limit the report is dropped and the file it writes is
  capped in size; the answer is 204 either way, so a sender learns
  nothing.
- CHECK: a test floods it and counts what was kept.
- GROWN: 2026-11, a multi-company business web program.

### K-15 The list of routes that answer with no session is short and written down [OPEN]
- RULE: the routes a stranger can reach are a named list, read at
  every audit, and each one says as little as it can.
- WHY: an audit was the first time anyone listed the open routes of a
  live program, and it found the health route telling a stranger the
  version and the database kind.
- HOW: not built yet. The shape: the list lives beside the sign-in
  code and a new open route is added to it in the same change.
- CHECK: a test asks every route with no cookie and compares the ones
  that answer with the list.
- GROWN: 2026-11, a systems audit of a multi-company business web
  program.

See also: K-3 (the count of wrong passwords); SECURITY_METHOD.md checklist
(rate limits).

## Rights and who may do what
Tags: security, permissions, rights | The server decides; the screen only shows

### K-16 The server decides every right, on every write [PROVEN]
- RULE: every route that writes asks the server-side rights function
  first; a hidden button is a courtesy, never the lock.
- WHY: anyone can send a request the screen never offered.
- HOW: one function returns the set of permission codes for a user in
  a company: empty for a user who is not active or not a member,
  everything for a super user, else the group's bundle plus grants.
- CHECK: a test per route calls it as a user without the right and
  reads 403; a lint or a review counts write routes with no check.
- GROWN: 2026-11, a multi-company business web program.

### K-17 Approving your own request is its own question with its own answer [PROVEN]
- RULE: whether a person may approve their own hours, time off or
  refund is asked separately from whether they may approve at all, and
  the answer can be set per person.
- WHY: the approval exists to be a second pair of eyes; the right to
  approve other people's requests says nothing about your own.
- HOW: one function answers it: the owner always; else an explicit
  row for that person decides either way; with no row, a top-level
  account may and everyone else may not.
- CHECK: a test approves its own request as each of the four cases.
- GROWN: 2026-11, a multi-company business web program.

### K-18 Locking out a top-level account takes two people, and deletes nothing [PROVEN]
- RULE: an emergency lock on a super user is proposed by one super
  user and seconded by another; the locked account cannot release
  itself; a lock that was withdrawn or released stays as history.
- WHY: one stolen top-level account must not be able to lock the
  others out, and one angry person must not either.
- HOW: a lock row with a proposer and a seconder; while it stands the
  account's rights are empty and its sign-in is refused.
- CHECK: tests for one person trying both steps and for the locked
  account trying to release.
- GROWN: 2026-11, a multi-company business web program.

See also: K-19 (the audit trail that records these).

## Logs and the audit trail
Tags: security, audit trail, logs | What is recorded, who may read it, what it never shows

### K-19 Every write is recorded with its actor, and the trail hides secrets [PROVEN]
- RULE: every change carries who made it; the audit view is read-only,
  sits under its own right, and never shows a password hash, a
  two-factor secret or recovery codes, whatever the record holds.
- WHY: a trail is how a break-in is read afterwards, and a trail that
  prints secrets is itself the leak.
- HOW: all writes pass through one apply function that records the
  actor; the view masks a fixed set of column names in either spelling
  as a second guard beside the writer's own skip list.
- CHECK: a test changes a password and reads the audit view for it.
- GROWN: 2026-11, a multi-company business web program.

See also: K-11 (the record of odd addresses).

## Secrets and config
Tags: security, secrets, env | Where a secret lives and how it is read

### K-20 An env file is data, never run as shell [PROVEN]
- RULE: a script reads a key from the env file by name; it never
  sources the file.
- WHY: a space after an equals sign ran a password as a command on a
  server.
- HOW: parse the one line wanted, taking everything after the FIRST
  equals sign (a value may hold one), or use the language's own env
  reader; quote every value in the file.
- CHECK: grep the deploy scripts for "source" and ". ./" on an env
  file.
- GROWN: 2026-11, a deploy to a rented server.

### K-21 A missing secret fails out loud [PROVEN]
- RULE: a part of the program that falls back to a local stand-in when
  its secret is blank says which one it chose, in the deploy's output
  and in the health check.
- WHY: blank storage keys made a file index read zero files and a
  nightly backup skip its off-machine copy, both in silence.
- HOW: the choice is printed where a person looks (the deploy's last
  line, the health route, a settings screen), and a production copy on
  a stand-in prints a warning in the deploy output. A setup step that
  leaves a secret for the owner to fill names it, with a check that
  proves it was filled by its length, never its value.
- CHECK: start the program with the key blanked and read the output.
- GROWN: 2026-11, a multi-company business web program.

### K-22 Secrets never enter git, and an automatic commit stages tracked files only [PROVEN]
- RULE: credentials, connection strings and client data live in the
  env family or outside the repo; any commit a script makes by itself
  stages tracked changes only, never "add everything".
- WHY: a safety-net hook with add-all pushed an owner's private
  picture to the remote; the same sweep would have pushed a key.
- HOW: a shell guard refuses a git add of a secret-shaped name;
  automatic commits use `git add -u`; new files are added by name from
  a read of the status.
- CHECK: the guard's own selftest; grep the hooks for "add -A" and
  "add ." .
- GROWN: 2026-11, the kit's own hooks.

See also: SECURITY_METHOD.md rule 3 (THE ROTATION LAW) and rule 4 (THE
PREFIX LAW), checklist class 1 (secrets in the client).

## Browser headers
Tags: security, headers, CSP, HSTS | What every answer carries

### K-23 Every answer carries the safety headers [PROVEN]
- RULE: every response, the API's and the client's files alike,
  carries X-Content-Type-Options: nosniff, a frame rule,
  Referrer-Policy, a Permissions-Policy that turns off what the
  program never asks for, and in production Strict-Transport-Security
  for a year.
- WHY: they are free, and their absence was the most common finding in
  the survey SECURITY_METHOD.md was founded on.
- HOW: one function returns the set and one hook adds it to every
  answer. The frame rule is SAMEORIGIN only when the program frames its
  own pages (a PDF viewer), DENY otherwise. HSTS is never sent by a
  local http server.
- CHECK: the audit script's header class against the live address.
- GROWN: 2026-11, a multi-company business web program.

### K-24 A script rule ships report-only first [PROVEN]
- RULE: a Content-Security-Policy ships first as Report-Only with a
  report endpoint (K-14); enforcing it is a second step (K-32), taken
  after the reports have been read and are empty for real use.
- WHY: a wrong script rule breaks a screen for every user at once.
- HOW: the same header text under the Report-Only name; a workflow to
  read what it would have refused.
- CHECK: the header's name on the live address, and the reports
  ledger.
- GROWN: 2026-11, a multi-company business web program.

See also: SECURITY_METHOD.md checklist class 2 (headers) and class 4
(CORS).

## Dependencies
Tags: security, dependencies, npm audit | Other people's code is your code once it runs on your server

### K-25 The advisory check runs in the everyday loop, and a high one fails it [PROVEN]
- RULE: the package manager's audit runs with the lints, not once
  before launch; a high or critical advisory in a package the server
  runs is a failed check.
- WHY: two packages took high advisories within weeks of install.
- HOW: a script in the check loop reads the audit, appends a ledger
  line, and fails on high or critical in a package the server runs.
- CHECK: the ledger's last line.
- GROWN: 2026-11, a multi-company business web program.

See also: SECURITY_METHOD.md checklist (the dependency audit).

## Backups and recovery
Tags: security, backup, restore | A backup that was never restored is a hope

### K-26 A backup is proven by a restore [PROVEN]
- RULE: the backup routine ends by restoring what it just made into a
  scratch database and comparing counts.
- WHY: a "newest file" pattern once picked a sibling file with the
  same prefix, and the restore held the wrong data; only the compare
  caught it.
- HOW: the pattern that picks the file is narrowed the day a second
  file shares its prefix; the compare prints restored against live.
- CHECK: the backup ledger's last line reads the two counts.
- GROWN: 2026-11, a multi-company business web program.

### K-27 One copy leaves the machine, and its absence is loud [PROVEN]
- RULE: every backup has a copy off the server, and a run that could
  not make it says so (K-21).
- WHY: a server that is lost takes its own backups with it.
- HOW: object storage or a second drive. The off-machine step was once
  skipped in silence because its keys were blank, which is why K-21
  exists.
- CHECK: list the off-machine store after a run.
- GROWN: 2026-11, a multi-company business web program.

See also: K-21 (a missing secret fails out loud).

## Known gaps (OPEN, nothing proven yet)
Tags: security, gaps, open | Looked for and not found in any project so far; each becomes an entry the day a project settles it

### K-28 A token against cross-site writes [OPEN]
- RULE: not settled. SameSite=Lax and K-6 are what stands today.
- WHY: a write a browser can be tricked into sending from another site
  is the classic gap a cookie session leaves.
- HOW: none on record; whether each write route needs its own token is
  the question.
- CHECK: none yet.
- GROWN: 2026-11, noted the day this file was founded.

### K-29 Upload checks [OPEN]
- RULE: not settled. The shape: a size limit, the type read from the
  bytes and not the name, and a user's file served from a separate
  origin so it can never run as the program's own page.
- WHY: an upload is a stranger's bytes kept on your server and sent to
  your users.
- HOW: partly built in one project and not yet read closely enough to
  write down.
- CHECK: none yet.
- GROWN: 2026-11, noted the day this file was founded.

### K-30 A rotation calendar for secrets [OPEN]
- RULE: not settled. The rotation LAW is in SECURITY_METHOD.md (a
  secret that was ever public is rotated at once).
- WHY: a secret that was never public still ages: people leave and
  laptops are lost.
- HOW: none on record.
- CHECK: none yet.
- GROWN: 2026-11, noted the day this file was founded.

### K-31 The server's CORS policy written down [OPEN]
- RULE: not settled. The shape: which origins may call, and why none is
  a wildcard.
- WHY: the survey SECURITY_METHOD.md was founded on met a wildcard in
  43 of 100 apps.
- HOW: none on record.
- CHECK: SECURITY_METHOD.md's checklist reads it from outside.
- GROWN: 2026-11, noted the day this file was founded.

### K-32 The script rule enforced [OPEN]
- RULE: not settled: when K-24's report-only rule is switched to
  enforcing, and who reads the reports first.
- WHY: a report-only rule refuses nothing.
- HOW: none on record.
- CHECK: none yet.
- GROWN: 2026-11, a multi-company business web program.

See also: THE KNOWLEDGE RULE point 6 (an OPEN entry a design touches is a
question for the owner).

## How an entry is added (paste into WORKFLOWS.md, adapt the paths)
Tags: process, workflow | The registry entry that keeps this file alive

```
## Add to the security knowledge base

WHEN: a security finding, a security ruling, a security fix, a scanner's
visit that taught something, or an audit line that names a gap; also the
day a RULED entry's check first passes.
EFFORT: low
STEPS:
1. `Grep "^### K-" SECURITY_KNOWLEDGE.md`: is it already there? Then the
   entry is updated (its status, its HOW), never doubled.
2. Else the next K number under the section it belongs to: RULE, WHY,
   HOW, CHECK, GROWN, and the honest status (PROVEN, RULED or OPEN).
3. Read it once as a stranger would: no real address, host, person,
   client or key (THE KNOWLEDGE RULE point 4).
4. If it is true beyond this project, note it for the kit: it goes up
   at the next release.
VERIFY: the wiki link check passes; the entry's CHECK line names
something that can be run or read.
```

See also: WORKFLOW_METHOD.md (the entry template); THE KNOWLEDGE RULE
above.

## BOOTSTRAP (new project)

1. Copy this file to the project root whole; the entries are the
   starting list, not a history to trim.
2. Paste the entry above into WORKFLOWS.md and add one line to the
   master index.
3. At the first design of sign-in, sessions, rights or a deploy, read
   the sections that match and name the K numbers in the contract.
4. The project's own findings take the next free numbers. At a kit
   update, new kit entries are added to this copy by graft; if a number
   is taken here by a project entry, the kit's entry takes the next
   free one and says which kit number it came from.

See also: SECURITY_METHOD.md "BOOTSTRAP (new project)"; UPGRADES.md "THE
GRAFT PROTOCOL".
