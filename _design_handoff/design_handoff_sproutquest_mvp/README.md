# Handoff: SproutQuest MVP

## Overview

SproutQuest is a kid-friendly multiplayer plant-hunting game. Players join timed hunts, scan plants in the real world (camera + ML, not yet wired up), earn points scaled by rarity, and compete on a live leaderboard. First-discoverers of a species in a session get a 2× points bonus.

This handoff covers a **focused 4-screen MVP** scoped down from a larger prototype. Removed surfaces (home, map, field guide, Sprout tip card, nearby-plants list) should **not** be reintroduced.

The 4 screens:
1. **Login** — password gate with the Sprout fox mascot
2. **Hunt Setup** — host or join, picks duration / enters code
3. **Hunt Mode** — locked-context game session with Scan / My Finds / Scores tabs
4. **End** — automatic celebration screen when the timer hits 0:00

## About the Design Files

The files in this bundle (`SproutQuest MVP.html`, `reference_sproutquest_v3.html`) are **design references created in HTML** — interactive prototypes showing intended look and behavior, not production code to copy directly.

Your task is to **recreate these designs in the target codebase's existing environment** (React Native / Flutter / SwiftUI / native iOS / Android — whatever the team is using) using its established patterns, navigation library, and component primitives. If no environment exists yet, choose the most appropriate framework for a mobile-first, real-time multiplayer game (React Native + a realtime backend like Supabase/Firebase, or native iOS with WebSocket transport, are reasonable starting points).

Do **not** ship the HTML as-is. Treat it as a visual + interaction spec.

## Fidelity

**High-fidelity.** The prototype reflects final intended colors, typography, spacing, animations, and interaction patterns. Recreate UI pixel-close using the codebase's existing libraries. The chunky-cartoon visual language (offset bottom shadows on buttons, big rounded everything, bouncy spring animations) is a load-bearing brand decision — preserve it.

The reference file `reference_sproutquest_v3.html` is the broader earlier prototype — useful for design DNA (color palette, type scale, plant data shapes) but **the MVP file is canonical** for scope and screen structure.

---

## Screens / Views

### 1. Login Screen (`#scr-login`)

**Purpose:** Gate the app behind a shared password (MVP-only; real auth comes later).

**Layout:**
- Full-bleed radial-gradient green background (`#86c34a` → `#5aaa1e` → `#3d7a10`)
- 4 decorative leaf emoji absolutely positioned at corners, gently swaying (`leafSway` animation, 4.5–6s loop)
- Centered card (`max-width: 340px`), vertically + horizontally centered:
  - Circular white logo badge, 170×170px, white background, `border-radius: 50%`, drop shadow stack `0 12px 0 rgba(0,0,0,.18), 0 18px 40px rgba(0,0,0,.3)`, bobbing animation (`foxBob` 3s, ±10px Y)
  - Inside: 140×140 SVG of "Sprout" the fox (orange head, white muzzle, black eyes with white catchlight, green leaf sprig on head, pink cheek blush)
  - `SproutQuest` wordmark — 54px / 900 / letter-spacing -1.5 / white / with text-shadow stack including a 4px offset solid drop
  - Tagline — 15px / 800 / "Hunt plants. Score points. Be a nature hero! 🌿"
  - Password input — full-width pill (`border-radius: 99px`), 18px padding, white, centered text, letter-spacing 1px, focus border `--amber`
  - Error pill (shown only on wrong password) — "Oops! Try again 🦊", red text on white, pops in with scale animation, input shakes (`shake` keyframes, 0.4s)
  - Submit button — full-width, "Let's Go! →", chunky green pill (gradient `#86c34a → #5aaa1e`), 22px / 900, 5px solid offset shadow + soft blur shadow, depresses 3px on press
  - Below: small hint text "Hint: password is **sprout**" (REMOVE for production)

**Behavior:**
- Submit checks `password.trim().toLowerCase() === 'sprout'` (replace with real auth)
- Wrong password: shake input, show error pill, refocus input
- Right password: navigate to Setup, clear field

---

### 2. Hunt Setup Screen (`#scr-setup`)

**Purpose:** Player decides whether to host a new hunt or join a friend's hunt with a code.

**Layout:**
- Top 30% of viewport: solid green band (`linear-gradient(180deg, #5aaa1e → #86c34a)`) with hero content; rest is `--green-xl` (`#f0f9e8`)
- Hero (centered, white text):
  - 100×100 white circular Sprout badge, rocking back and forth (`foxCheer` 2.4s, rotate -6 → 6 deg + Y bob)
  - "Ready to Hunt?" — 34px / 900 / -1px letter-spacing / white / 3px shadow
  - Subhead "Pick a mode and let's go find some plants!" — 14px / 700
- Mode stack: two cards, stacked vertically with 14px gap, pulled up 64px to overlap the hero band:
  - **Start Hunt** card — green diagonal gradient (`135deg, #86c34a → #5aaa1e → #3d7a10`)
  - **Join Hunt** card — orange diagonal gradient (`135deg, #fb923c → #f97316 → #c2410c`)
  - Each card has decorative translucent circles bottom-right (140px) and top-right (80px)
  - `border-radius: 24px`, `padding: 22px`, chunky offset shadow `0 6px 0 rgba(0,0,0,.22), 0 12px 28px rgba(0,0,0,.18)`

**Card header (always visible):**
- 64×64 emoji tile (translucent white bg, 18px radius) — 🌿 for Start, 🔍 for Join
- Title 26px / 900 / -.5px letter-spacing
- Subtitle 13px / 700 / 90% opacity
- Right-side `›` chevron, 24px, rotates 90° when expanded (CSS transition .25s)

**Behavior:**
- Only one card expanded at a time. Tapping the collapsed card expands it and collapses the other.
- Tapping inside an already-expanded card body does **not** collapse it (clicks inside don't trigger the card's onClick).

**Start Hunt — expanded body, Phase A (duration picker):**
- Section label "PICK A DURATION" — 11px / 900 / 1.5px tracking / 85% white
- 2×2 grid of duration buttons, 10px gap
- Each duration button: 16×12 padding, 14px radius, translucent white bg (`rgba(255,255,255,.18)`), white text
  - Big number (24px / 900) above small unit "MIN" (11px / 800 / 1px tracking)
  - Selected state: white background, dark green text (`--green-d`), 4px offset shadow, 3px border `rgba(255,255,255,.5)`
  - Default selection: 30 min
  - Options: 15, 30, 45, 60
- "Create Hunt! →" button — full-width white pill, dark green text, 4px solid offset shadow, depresses 2px

**Start Hunt — expanded body, Phase B (code share):**
- Code display box — white card, 18px radius, centered:
  - Label "YOUR HUNT CODE" (10px / 900 / 2px tracking / `--text3`)
  - Code value 46px / 900 / 6px tracking / `--green-d` with text-shadow drop, in Nunito (acceptable substitute: any rounded monospace)
  - Helper "📣 Share this code with friends!" (12px / 800 / `--text2`)
- Stats row — translucent dark bar with two columns: duration + live player count (player count animates `transform: scale(1.3) → 1` on each join)
- "Begin Hunt! →" button — same style as Create Hunt button

**Code generation:** pick one of `['SPROUT','OAK247','FERN88','MOSSY1','PETAL9','ACORN5','BLOOM3','LEAFY7']` randomly. Production: generate a 6-char alphanumeric code server-side and broadcast it to joiners.

**Join Hunt — expanded body, Phase A (PIN entry):**
- Section label "ENTER THE 6-LETTER CODE"
- PIN input — full-width, 18px padding, 4px border `rgba(255,255,255,.4)`, 34px / 900 / 8px tracking, uppercase, monospace feel, placeholder `••••••`
- Auto-uppercases input via JS, strips non-alphanumeric, max length 6
- "Join!" button — white pill, orange text on press
- Error: shake animation, yellow border, on codes < 4 chars (real validation: hit backend, accept only valid codes)

**Join Hunt — expanded body, Phase B (lobby):**
- Lobby box — white card with idle Sprout (rocking animation), "Joined! Waiting for host" with animated dots (`···` cycling 1.4s), "Hunt starts when host begins" subtitle
- 3 stat tiles in row: duration / players joined / code
- "Leave lobby" button — translucent white, returns to Phase A
- **Auto-advances to Hunt Mode after 4.5s** in the prototype (simulating host clicking Begin). In production this is triggered by a websocket/realtime event from the host.

---

### 3. Hunt Mode Screen (`#scr-hunt`)

**Purpose:** The actual game session. Locked context — no back navigation, only the small ✕ Exit button with confirmation modal.

**Layout:** Vertical stack:
1. Persistent topbar (always visible across all tabs)
2. Active tab content (flex: 1, scrolls internally)
3. Bottom 3-tab nav

**Topbar:**
- Background `linear-gradient(180deg, #3d7a10 → #2d5a08)`, 3px solid bottom shadow
- 4 stats arranged in a flex row, each `flex: 1`, with thin vertical dividers between (`1px × 36px`, `rgba(255,255,255,.15)`):
  - **SCORE** — 22px / 900 / white number, 9px / 900 / 1px tracking label (55% white)
  - **RANK** — same, but number in `--amber` (`#f59e0b`)
  - **FOUND** — number in `--green-m` (`#86c34a`)
  - **LEFT** (time) — white, `font-variant-numeric: tabular-nums`. When `≤ 30s`, turns `#fca5a5` and pulses (`urgent` animation, scale 1↔1.1, 1s loop)
- Followed by a small **✕ Exit** button inline at the right: `rgba(0,0,0,.3)` bg, 10px radius, 8×10 padding, 10px / 900, 6px left margin

**Bottom nav (3 tabs):**
- Position: left = My Finds, center = Scan (raised), right = Scores
- Background white, 8px top padding, 22px bottom padding (safe area on iPhone)
- Each item: stacked icon (24×24 stroke SVG) + 11px / 900 label, default color `--text3`, active color `--green-d` with 24px green underline pip below
- Active state on side tabs: icon scales 1.15
- **Center Scan button is raised:** 64×64 circle, gradient `#86c34a → #5aaa1e`, white 32×32 icon, `margin-top: -26px` so it pops up above the nav, with `0 5px 0 #3d7a10` solid shadow + `0 8px 18px` blur. Label hidden. Depresses 3px on press.

#### Tab: My Finds (`#hs-finds`)

- Header card at top (white, 18px radius, 14×18 padding, 2px border `--border`):
  - 🌿 emoji (32px)
  - "YOUR FINDS" label (10px / 900 / 1px tracking / `--text3`)
  - Running total: `{score} pts` — 28px / 900 / `--green-d`
  - "{count} plants discovered" — 11px / 800 / `--text2`
- Scrollable list below:
  - Empty state (no finds): bouncing 🌱, "No finds yet!", "Tap the Scan button below to discover your first plant."
  - With finds: section title "RECENT FIRST", then a card per find. Each card:
    - 48×48 emoji tile, rarity-tinted background
    - Plant name (15px / 900) with optional "FIRST!" amber pill
    - Rarity badge + relative time ("just now", "12s ago", "2m ago")
    - Points (18px / 900), color by rarity
    - Slides in with `rowIn` animation (8px translate Y + opacity)

#### Tab: Scan (`#hs-scan`) — default tab when entering hunt

- Full-bleed dark-green camera-style viewfinder
- Decorative big 🌿 emoji at 18% opacity as the "camera feed" placeholder
- Centered scan frame: 64% width, square, with 4 corner brackets (36×36, 4px stroke, `--green-m`, rounded inside corners) + a horizontal scan line that travels top → bottom every 2.2s with green box-shadow glow
- Hint banner at top: translucent black, backdrop blur, "📷 Point at a plant" / "Hold steady · Center leaves in the frame"
- **Demo buttons row at bottom** (4 buttons, one per rarity, label "DEMO · Tap a rarity to simulate a find"):
  - 🌼 Common (green gradient) → calls `triggerFind('dandelion')`
  - 🌸 Uncommon (blue gradient) → `triggerFind('phlox')`
  - 🌷 Rare (pink gradient) → `triggerFind('trillium')`
  - 🍄 Ultra Rare (purple gradient) → `triggerFind('morel')`
  - **Remove these in production** — they exist because the camera isn't wired up

When camera + ML are wired up:
- Real camera feed should fill the dark area
- ML inference happens on each frame; when a confident match is found, fire the same `triggerFind(plantKey)` flow

#### Tab: Scores (`#hs-scores`)

- Section title "🏆 LIVE LEADERBOARD"
- Leaderboard card (white, 18px radius, 2px border):
  - One row per player, sorted by score descending
  - Row contents: rank badge (gold/silver/bronze for top 3 — circles with white text and a 2px offset solid shadow) → 36×36 colored avatar circle with first initial → name (with "YOU" pill if current player) → score (16px / 900 / dark green) + finds count (10px / 700 / `--text3`) right-aligned
  - Current player row has a green gradient highlight background
  - Updates whenever a find happens or another player scores
- Section title "⭐ NOTABLE FINDS"
- Empty state until someone has a first-find
- Each first-discovery: emoji + plant name + "First found by **{Name}** · {time ago}" + amber `2× pts!` badge

---

### 4. End Screen (`#scr-end`)

**Purpose:** Celebration moment when timer hits 0 (or user confirms exit). Shows final tally + recap + Play Again.

**Layout:**
- Background: radial gradient amber → orange → brown (`#f59e0b → #d97706 → #92400e`)
- Recurring confetti layer (every 3.5s, ~80 pieces of color blocks + plant emoji, falling 1.5–4s each)
- Hero (centered):
  - 🏆 trophy at 120px, bounces in with spring (`trophyBounce`, `cubic-bezier(.34,1.56,.64,1)` over 1.2s, from `scale(0) rotate(-30deg)` → `scale(1.2) rotate(10deg)` → final)
  - "Hunt Complete!" — 36px / 900 / -1px tracking / white
  - Rank line: "🏆 You finished in 1st place!" or "You finished in 3rd place out of 5."
- Final score card (white, 24px radius, 8px solid shadow):
  - "FINAL SCORE" label
  - Score 64px / 900 / `--green-d` / tabular-nums
  - 3-stat row at bottom: plants found, first finds, rarest (emoji of highest-tier find or `—`)
- Recap section (95% white card with 24×24 top radius, flex-grow to fill):
  - Title "📜 RECAP — EVERY PLANT YOU FOUND"
  - Scrollable list of every find in reverse chronological order, same row component as My Finds
- Bottom action: "🌿 Play Again" button — full-width chunky green pill, 18px / 900, depresses 3px on press, returns to Setup

---

## Interactions & Behavior

### Navigation flow
- Login → Setup (on correct password)
- Setup → Hunt (on Begin Hunt by host, or auto-trigger for joiner after host's begin event)
- Hunt → End (automatic at timer 0, or via Exit modal confirmation)
- End → Setup (Play Again)
- No back navigation in Hunt mode — only the ✕ Exit button + confirmation modal

### Timer
- Counts down 1s/s starting at `state.duration * 60` seconds
- Display format `M:SS` (e.g. `29:05`). For ≥60min display, extend to `MM:SS`.
- Last 30s: time text turns light red `#fca5a5`, pulses (scale 1 ↔ 1.1, 1s loop)
- At 0: trigger End screen automatically

### Find / scan
1. Player taps demo button (production: ML identifies plant from camera frame)
2. Look up plant in DB → determine if first finder (no entry in `firstFinds[plantKey]` yet)
3. Compute points: `basePts * (isFirst ? 2 : 1)`
4. Append to `myFinds[]`, increment `score` + `plants`, set `firstFinds[plantKey] = { finder: 'You', t: Date.now() }` if first
5. Re-render topbar, my-finds list, leaderboard, notable finds
6. Fire celebration overlay (see below)
7. If first finder: 800ms later, fire toast notification

### Celebration overlay (fires on every find)
- Full-screen dim (rgba(0,0,0,.65) + 2px blur)
- Big plant emoji (120px) springs in: `scale(0) rotate(-180deg) → scale(1.3) rotate(15deg) → scale(1) rotate(0)` over 600ms with cubic-bezier(.34,1.56,.64,1)
- Title varies by rarity:
  - `c` (common) → "New find!"
  - `u` (uncommon) → "Nice find!"
  - `r` (rare) → "RARE FIND!"
  - `ul` (ultra rare) → "ULTRA RARE!" with animated gold gradient text-fill (32px instead of 28px)
- Plant name subtitle
- Big amber points readout (48px / 900)
- "⭐ FIRST FINDER · 2× BONUS!" amber pill if first finder
- Confetti scales with rarity:
  - common: 30 pieces, color blocks only
  - uncommon: 50 pieces, ~35% chance each is an emoji (🌿 🍃 🌱 ✨ ⭐ 💚)
  - rare: 80 pieces
  - ultra rare: 120 pieces
- Dismiss after 2000ms (3000ms for ultra rare)

### Toast notifications
- Position: absolute, top 80px, full width minus 14px margins, z-index 500
- Appearance: dark green gradient bg, 2px amber border, chunky shadow, 35ms spring-in
- Auto-dismiss after 3500ms with 400ms fade
- Used for: first-find announcements (yours and others')

### Exit modal
- Full-screen dim overlay, fades in 200ms
- Centered card (max 320px, 24px radius):
  - 🦊 emoji (54px)
  - "Leave the hunt?" title
  - Warning copy with current score interpolated
  - Two buttons side by side: "Keep hunting" (gray) and "Yes, exit" (red gradient)
- Closing: hide overlay; "Yes, exit" → kills timer, fires End screen

### Other player simulation (prototype only — replace with realtime)
- Every 4.5s: random other player has a chance to find a random plant
- If they're first finder: register them, broadcast toast + add notable finds row
- Always re-render leaderboard
- **Production:** replace with websocket/realtime channel; each player's client posts find events; all clients subscribe to a session-scoped channel; leaderboard + notable finds derive from that event log

### Animations (all are essential to the brand)
| Animation | Duration | Notes |
|---|---|---|
| `foxBob` | 3s loop | Logo badge Y-axis ±10px |
| `foxCheer` | 2.4s loop | Setup fox rocks -6° ↔ 6° + Y bob |
| `foxIdle` | 2s loop | Lobby fox subtle sway |
| `leafSway` | 4.5–6s loop | Decorative leaves on login |
| `shake` | 400ms once | Wrong password / wrong PIN |
| `popIn` | 300ms once | Error pill, modal entry |
| `urgent` | 1s loop | Last-30s timer pulse |
| `rowIn` | 300ms once | New find list rows |
| `celBounce` | 600ms once | Celebration plant emoji |
| `trophyBounce` | 1200ms once | End screen trophy |
| `scanLine` | 2.2s loop | Viewfinder scan sweep |
| `confettiFall` | 1.5–4s once | Per-confetti-piece fall + 720° rotation |
| `toastIn` | 350ms once | Toast entry |
| `dots` | 1.4s loop | "Waiting for host..." dots |
| `slideDown` | 300ms once | Mode card body expand |

All button presses depress 2–3px on `:active` (the offset shadow shrinks to match). This is load-bearing for the chunky/tactile feel.

### Press / hover states
- Mobile-first design — hover is not relied on
- `:active` state on every button: `transform: translateY(2-3px)` with shadow offset reduction to match
- Focus state on inputs: 3px amber border (`--amber`)

---

## State Management

### Session state (Hunt mode)
```ts
type HuntState = {
  duration: number;        // minutes, picked at setup
  joinCode: string;
  timerSec: number;        // counts down
  score: number;
  plants: number;
  rank: number;
  myFinds: Find[];
  firstFinds: Record<string, { finder: string; t: number }>;
  playerCount: number;
  others: Player[];        // simulated; replace with realtime roster
};

type Find = {
  key: string;             // plantDB key
  name: string;
  emoji: string;
  rarity: string;
  tier: 'c' | 'u' | 'r' | 'ul';
  pts: number;
  first: boolean;
  t: number;               // Date.now() at find
};

type Player = { name: string; color: string; score: number };
```

### State transitions
- Login submit → if valid, navigate to Setup
- Setup `expandCard(which)` → toggle which card is expanded; reset that card's internal phase
- Setup `selectDur(min)` → set `state.duration`
- Setup `createHunt()` → generate code, advance to code-share phase, start fake-join interval (production: open session on backend, subscribe to roster updates)
- Setup `joinHunt(code)` → advance to lobby; wait for host start event
- `beginHunt()` → reset all session state, navigate to Hunt, start timer, start realtime subscriptions
- `triggerFind(plantKey)` → see Find flow above
- Timer at 0 OR exit confirm → `endHunt()` → navigate to End
- `playAgain()` → reset card phases, navigate to Setup

### Data fetching / realtime needs (for production)
- Auth (replace password gate)
- Plant identification API (camera frame → species + confidence)
- Plant DB (catalog of all known species, with rarity tiers, base points, taxonomy, foraging notes, conservation notes — see reference file's `plantDB` shape for the richer version)
- Session creation + join code generation
- Realtime session events: roster changes, find events, host-began-hunt event, hunt-ended event
- Server-side timer authority (don't trust each client's clock for end-time)
- Persistence: save user's lifetime stats, finished hunt summaries

---

## Design Tokens

### Colors

```css
/* Greens (primary brand) */
--green:        #5aaa1e;   /* primary CTAs, points */
--green-d:      #3d7a10;   /* topbar dark, text on light */
--green-dd:     #1e3d08;   /* app shell backdrop */
--green-m:      #86c34a;   /* lighter accent, found-count */
--green-l:      #e8f5d0;   /* tinted backgrounds */
--green-xl:     #f0f9e8;   /* page background */

/* Orange (secondary — Sprout the fox, Join card) */
--orange:       #f97316;
--orange-d:     #c2410c;
--orange-l:     #fff0e6;

/* Accents */
--purple:       #8b5cf6;   /* ultra-rare rarity */
--amber:        #f59e0b;   /* rank, first-finder pills, end screen */
--amber-l:      #fffbeb;
--red:          #ef4444;   /* errors, exit confirm */
--pink:         #ec4899;
--gray:         #6b7280;
--gray-l:       #f3f4f6;

/* Neutrals */
--card:         #fff;
--text:         #1a2e0a;
--text2:        #4a6330;
--text3:        #7a9460;
--border:       #d4eab8;
```

### Rarity tier colors (text)
- Common (`c`): `--green` `#5aaa1e`
- Uncommon (`u`): `#2563eb`
- Rare (`r`): `#db2777`
- Ultra Rare (`ul`): `--purple` `#8b5cf6`

### Rarity tier colors (tinted bg)
- Common: `--green-l`
- Uncommon: `#eff6ff`
- Rare: `#fdf2f8`
- Ultra Rare: `#f3f0ff`

### Typography
- Family: **Nunito** (Google Fonts, weights 400/600/700/800/900). Falls back to `sans-serif`. Acceptable native substitutes: SF Rounded (iOS), `Sans Serif Rounded` (Android), or any rounded geometric sans.
- The design relies heavily on weight 900 — make sure that weight is included.
- Sizes used (px):
  - 9 (tiny tracked labels), 10 (micro), 11 (small captions), 12 (body small), 13 (default body), 14 (large body), 15 (list item titles), 16 (button text), 17 (modal titles), 18 (large buttons / running scores), 20 (medium hero text), 22 (topbar stats), 26 (mode card titles), 28 (running totals, celebration title), 32 (UR celebration title), 34 (setup hero), 36 (end hero), 46 (hunt code), 48 (celebration points), 54 (login logo), 64 (final score), 120 (celebration emoji / trophy)
- Letter-spacing: tight (-1px to -1.5px) on big display text, generous (0.5–2px tracking) on uppercase labels

### Spacing scale
- 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 32, 40, 64 px

### Border radius
- `--rs: 12px` — small (default buttons, demo tiles)
- `--r: 18px` — medium (cards, inputs)
- 14px — list rows
- 24px — mode cards, modals
- 99px — pills (most buttons)
- 50% — circles (avatars, logo badge, raised scan button)

### Shadows
The chunky offset shadow is foundational:
- **Button chunk** — `0 5px 0 rgba(0,0,0,.18), 0 8px 20px rgba(0,0,0,.15)`. On press: shadow shrinks to `0 2px 0 ...`, button translates 3px Y.
- **Mode card** — `0 6px 0 rgba(0,0,0,.22), 0 12px 28px rgba(0,0,0,.18)`
- **Card lift** (My Finds row, leaderboard card) — `0 3px 0 rgba(0,0,0,.06)` or `0 4px 0 rgba(0,0,0,.08), 0 6px 16px rgba(0,0,0,.06)`
- **Topbar bottom edge** — `0 3px 0 rgba(0,0,0,.25)`
- **Bottom nav top edge** — `0 -4px 16px rgba(0,0,0,.08)`
- **Raised scan button** — `0 5px 0 #3d7a10, 0 8px 18px rgba(0,0,0,.2)`
- **App shell** — `0 30px 80px rgba(0,0,0,.5)` (only when shown in a webview-style container)
- **Final score card** — `0 8px 0 rgba(0,0,0,.18), 0 12px 28px rgba(0,0,0,.25)`

Reproduce these as platform-native shadow stacks where possible (e.g. layered `box-shadow` on web, multiple `Shadow` views or `elevation` + custom drop shadow on native).

---

## Assets

### Sprout the fox (mascot)
The fox is drawn inline as SVG in the prototype — it appears at several sizes (170px on login, 100px on setup, 80px in lobby).

Spec for the production version:
- Round orange head, white muzzle wrapping around bottom + cheeks
- Two pointed orange triangle ears with lighter inner triangles
- Black ovate eyes with small white catchlight ovals
- Black oval nose, simple curved smile underneath
- Pink translucent cheek blush circles
- Single green leaf sprig on top of head (the "sprout")
- Final asset should be a single SVG file in the repo (`assets/sprout.svg`) that scales cleanly. Consider 2–3 variants (cheering, idle, surprised) for richer animation.

### Plant emojis
Used as placeholders. MVP uses native emoji rendering. Production should consider commissioning custom plant illustrations (or sourcing CC-licensed botanical art) for higher polish — but launching with emoji is acceptable.

### Plant catalog (starter set)
From the reference file's richer `plantDB`. For each plant, store:
```ts
{
  key: 'morel',
  emoji: '🍄',
  name: 'Yellow Morel',
  sciName: 'Morchella esculenta',
  rarity: 'Ultra Rare',
  tier: 'ul',
  basePoints: 100,
  about: '...',
  forage: '...',
  impact: '...'   // conservation / ecology note
}
```
The MVP only surfaces emoji + name + rarity + points, but the richer data is wanted for a future plant-detail view.

### Icons
- Bottom nav icons (My Finds book, Scan camera-target, Scores trophy) — currently inline `stroke="currentColor"` SVGs at 24×24. Replace with your icon library (Lucide, Phosphor, custom) but keep the chunky 2.2px stroke weight to match the visual language.

---

## Files

In this bundle:

- **`SproutQuest MVP.html`** — the canonical MVP prototype with all 4 screens, all interactions, all animations. **This is the source of truth.**
- **`reference_sproutquest_v3.html`** — the earlier, fuller prototype. Use for: extended plant DB shape, design DNA cross-reference, hunt-mode visual details. **Out of MVP scope; do not implement screens that exist only here.**

Open both files in a browser to interact with them.

---

## Notes for the implementing developer

- **The chunky offset shadows are the brand.** Don't replace them with subtle Material-style shadows or iOS-style soft drops. The 5px solid offset shadow + button-depresses-on-press is the entire tactile vocabulary.
- **Animations are not garnish.** Sprout's idle bob, the scan line, the confetti, the trophy spring — these are why a 10-year-old will play this twice. Don't strip them for "polish" later; build them in from day one.
- **The 3-tab bottom nav appears only in Hunt mode.** Login and Setup are full-bleed with no nav. Don't unify into a single 5-tab shell.
- **Demo buttons on Scan must go** before production. They exist purely so the prototype is testable without a camera.
- **Hunt mode is locked context.** No back gestures, no swipe-to-dismiss, no system back button. Only the ✕ Exit confirmation. On iOS, suppress the swipe-back gesture. On Android, intercept hardware back to show the exit modal.
- **Server-authoritative timer.** Each client should periodically reconcile against a server-issued `hunt_ends_at` timestamp. Local countdown is fine for display; rely on server for the actual end event.
- **Accessibility:** All buttons hit ≥ 44×44pt. Add proper accessible labels for the ✕ Exit button (currently has `aria-label="Exit hunt"` in the prototype), the rarity emoji tiles, and the scan button. The "demo" rarity buttons should be removed in production so screen reader users don't hear them.
