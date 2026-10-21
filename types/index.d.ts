// neuroflow mod — the $.state contract. `claude plugin validate` holds every $.state key the
// module names to this file. Truth lives in the .neuroflow/ files; everything here is a mirror
// of them or per-session UI state, never a second source of truth.

export type NfRuntime = 'off' | 'observe' | 'on'

/** Whether the mod acts in this session, and where. */
export type NfScope = {
  /** True when a neuroflow project was found and nothing rules the mod out here. */
  isActive: boolean
  /** Why the mod is inactive ('active' when it is). */
  reason: string
  /** Absolute project root (the folder holding .neuroflow/), or null. */
  root: string | null
  /** No person at the prompt (-p, SDK): no UI, no questions; guards still deny. */
  isHeadless: boolean
}

/** Frontmatter of a .neuroflow/<phase>/status.md integrity file. */
export type NfStatusFile = {
  status: string
  setBy: string | null
  setAt: string | null
}

export type NfEthics = NfStatusFile & {
  approvalId: string | null
  expires: string | null
  aiProcessing: string | null
}

export type NfPrereg = NfStatusFile & {
  frozenAt: string | null
  /** project-relative path → sha256 recorded at freeze time */
  files: Record<string, string>
  plannedN: number | null
}

/** A dated row of timeline.md; `gates` is the phase it gates, when the row names one. */
export type NfDeadline = { date: string; what: string; gates: string | null; daysLeft: number }

/** A meeting file (.neuroflow/meetings/ or the flowie meetings folder), as the band needs it. */
export type NfMeeting = {
  level: 'project' | 'flowie'
  slug: string
  title: string
  /** Local date-time as written (YYYY-MM-DDTHH:MM:SS, no timezone). */
  date: string
  /** Minutes from the snapshot's load time until it starts (negative once started). */
  startsIn: number
  closed: boolean
  /** Unchecked `- [ ]` action items in the file. */
  openActions: number
}

/** One row of a phase's autoresearch pointer registry. */
export type NfLoop = { phase: string; name: string; location: string; iterations: string; best: string; status: string }

/** A typed mirror of the project's .neuroflow/ files, reloaded when they change. */
export type NfSnapshot = {
  root: string
  nfSchema: number | null
  /** 'frontmatter' for the current contract, 'legacy' for older config dialects */
  dialect: 'frontmatter' | 'legacy'
  /** The neuroflow version the project was last brought up to date to (`plugin_version`), null when it names none. */
  pluginVersion: string | null
  /** The running plugin's version (.claude-plugin/plugin.json in the plugin's folder), null when unreadable. */
  runningVersion: string | null
  projectName: string | null
  phase: string | null
  mode: string | null
  recommendedPhases: string[]
  rawRoots: string[]
  paperAuto: boolean
  ethics: NfEthics | null
  prereg: NfPrereg | null
  deadlines: NfDeadline[]
  /** Phases that have a .neuroflow/<phase>/ folder. */
  phasesVisited: string[]
  /** Autoresearch loops listed in the phases' pointer registries. */
  loops: NfLoop[]
  /** Meetings from 2 days ago to 2 days ahead, soonest first. */
  meetings: NfMeeting[]
  /** Self-reported wellbeing is switched on in flowie and today's entry is missing (no scores are ever kept here). */
  wellbeingDue: boolean
  /** `ethics: not-applicable` in the config: no participants needing a tracked approval. */
  ethicsNotApplicable: boolean
  /** Flowie profiles this project is linked to (`flowie_profiles`); empty when not linked. */
  flowieProfiles: string[]
  /** The project's wiki capture policy (`wiki_capture: allow | forbid`), null when unset (allow). */
  wikiCapture: string | null
  /** Auto-capture cards waiting in .neuroflow/wiki/.pending/ for the person's review. */
  wikiPending: number
  /** Things the loader could not read or understand, in plain words. */
  problems: string[]
  loadedAt: number
  /** Changes on the person's claude.ai workbench waiting for /neuroflow:tasks --apply-web (pending.json); null when none. */
  workbench?: NfWebPending | null
}

/**
 * ~/.neuroflow/workbench/pending.json as workbench.py last wrote it (neuroflow-core → Workbench snapshot): how many
 * workbench changes wait for Claude Code, since when (`oldest`), and per level the board and the slugs they touch. As of
 * `checkedAt` only.
 */
export type NfWebPending = {
  checkedAt: string | null
  oldest: string | null
  count: number
  levels: { level: string; kind: string | null; board: string | null; root: string | null; slugs: string[]; count: number }[]
}

/** One row of a wiki's index.md: which wiki, the page title, its file and one-line summary. */
export type NfWikiPage = { level: string; title: string; path: string; summary: string }

/** One auto-wiki card waiting for review (wiki-protocol skill → Auto capture). */
export type NfWikiCard = { file: string; title: string; type: string; evidence: string; body: string; by: string }

/** The living paper pane (phase-paper → Living paper skeleton). */
export type NfPaperView = {
  status: string
  gaps: { gap: string; item: string; fill: string }[]
  /** Results slots (H1, H2…) the skeleton still shows without a final result. */
  slots: string[]
  /** Allow-listed source files changed since skeleton.md was written. */
  stale: string[]
  /** A submission or revision exists: sync rewrites nothing. */
  frozen: boolean
}

/** One X-ray finding (phase-paper → X-ray files). */
export type NfXrayFinding = {
  id: string
  scope: string
  sentence?: string
  line?: number
  severity: string
  area?: number
  basis?: string
  finding: string
  fix?: string
  status: string
  reason?: string
}

/** The X-ray pane: which files, and their findings. */
export type NfXrayView = { jsonl: string; md: string | null; title: string; findings: NfXrayFinding[] }

/** What the dashboard's loop tab shows for one autoresearch loop. */
export type NfLoopView = {
  name: string
  phase: string
  status: string
  iterations: string
  best: string
  /** The results.md "Running" column, oldest first. */
  running: number[]
  /** Open questions from the top of report.md. */
  questions: string[]
}

/** The dashboard's tabs, in their digit order (1–6); `now` lists every band item with its action. */
export type NfDashboardTab = 'now' | 'phase' | 'deadlines' | 'integrity' | 'tasks' | 'loop'

export type NfCard = {
  slug: string
  title: string
  owner: string | null
  due: string | null
  overdue: boolean
  /** The task's `project:` (flowie and hive levels), null when it names none. */
  project: string | null
  /** The task belongs to this project: every task at project level, a matching `project:` elsewhere. */
  isMine: boolean
  /** A change from the claude.ai workbench waits for this card (pending.json). */
  web?: boolean
}

/** One level's task board as the board pane draws it (commands/tasks.md format). */
export type NfBoard = {
  /** The drawn columns, each with every open card in board order (the pane shows five at a time and pages on). */
  columns: { id: string; label: string; cards: NfCard[]; total: number }[]
  /** Every open column of the board's config in board order, drawn or not (an empty one is not): where a card can move. */
  openColumns: string[]
  done: number
  archived: number
}

/** One task board level (commands/tasks.md → Levels), read from the local files as they are. */
export type NfTaskLevel = {
  /** `project`, `flowie`, `hive:{folder}` or `remote:{host/owner/repo}`: what the board pane switches by. */
  id: string
  /**
   * `remote`: the board of another repository of this project's card, read from the machine-local cache
   * projects.py keeps in ~/.neuroflow/boards/ (neuroflow-core → Project registry) — read-only here.
   */
  kind: 'project' | 'flowie' | 'hive' | 'remote'
  /** What the views call it: `project`, `flowie`, the hive's folder under ~/.neuroflow/hives/, or `owner/repo`. */
  name: string
  /** For a remote board: when its cache was last fetched (ISO time), null when unknown. */
  fetched?: string | null
  /**
   * This project's name at this level, the `project:` its tasks carry (commands/tasks.md → Levels): the flowie
   * project this repo is linked to, or the lab project of the hive's own registry; null at project level or unlinked.
   */
  project: string | null
  /** Open tasks: every column but done and the archive ones. */
  open: number
  /** Open tasks that belong to this project (all of them at project level). */
  mine: number
  board: NfBoard
  /** The level's first open cards: this project's first, overdue first, then by due date. */
  top: NfCard[]
}

/** The task boards of every level, for the dashboard's tasks tab and the board pane. */
export type NfTaskView = {
  /** Project first, then flowie, then the hives (those user.yaml lists first, the rest alphabetically), then remote boards. */
  levels: NfTaskLevel[]
  /** The id of this project's card (neuroflow-core → Project registry), null when this repo is linked to none. */
  card?: string | null
  /** Whether the card lists other repositories, whose boards the cache can hold. */
  hasRemote?: boolean
  /** Workbench changes waiting for Claude Code (pending.json): when it was written, since when the oldest waits, how many. */
  web?: { checkedAt: string | null; oldest?: string | null; count: number } | null
}

/** A flowie sync the mod queued (in $.store): the files it wrote there and the commit message. */
export type NfFlowieSyncEntry = {
  /** Paths inside the flowie repository, forward slashes. */
  paths: string[]
  message: string
  /** When it was last queued; a sync that ran from an older copy of the queue leaves it queued. */
  at: number
}

/** What the band shows about the mod's flowie syncs. */
export type NfFlowieSync = {
  /** Commit messages of the syncs still waiting, oldest first. */
  pending: string[]
  /** The last attempt's outcome when it did not go through (`push failed — …`); null after a clean sync. */
  failure: string | null
  /**
   * After a failure no new attempt runs until something new is queued or the next session; meanwhile each flush
   * point only checks, locally, whether a sync elsewhere (/neuroflow:flowie --sync) settled it.
   */
  isHeld: boolean
}

/**
 * The band's check of the flowie remote before it asks for today's wellbeing entry (#253): `pending` while it runs,
 * `present` when the entry is already on the remote (made on another machine), `absent`, or `unknown` when it could
 * not tell (offline, no upstream) — then the band asks as it always did.
 */
export type NfWellbeingCheck = {
  /** The day checked, YYYY-MM-DD (local time). */
  date: string
  state: 'pending' | 'present' | 'absent' | 'unknown'
}

export type NfReasoningBaseline = { path: string; lines: number }

export type NfDraftedDecision = {
  /** The reasoning log the entry goes to, absolute. */
  path: string
  phase: string
  command: string
  statement: string
  reasoning: string
  at: number
}

export type NfDrive = {
  name: string
  phase: string
  /** The loop folder, absolute. */
  folder: string
  /** Its location as the registry writes it (project-relative). */
  location: string
  startedAt: number
  /** Turns this drive submitted. */
  turns: number
  /** Turns in a row that ended in an error. */
  errors: number
  maxErrors: number
  /** The run's cost cap in USD, when program.md sets one this session can measure. */
  maxCostUsd: number | null
  costAtStart: number | null
}

/** The neuroflow command running in this turn, if any. */
export type NfActiveCommand = { name: string; phase: string; lifecycle: string; startedAt: number }

declare module 'claude-code' {
  interface PluginState {
    neuroflow: {
      scope: NfScope | null
      snapshot: NfSnapshot | null
      activeCommand: NfActiveCommand | null
      /** Files the model wrote through Write/Edit in the current turn. */
      turnWrites: string[]
      /** Features that could not do their job this session, for the status line and doctor. */
      degraded: string[]
      /** Short alerts features raise for the status line (a frozen file changed, a DOI does not resolve…). */
      statusAlerts: string[]
      /** Since when a quiet command (`lifecycle: quiet`, e.g. /idk) holds the mod's own UI silent; null when not. */
      quietSince: number | null
      /** The mod's own flowie syncs: queued by the wellbeing band (views) and the idea capture, run by capture. */
      flowieSync: NfFlowieSync
      /**
       * When each pane (by id) last opened asking for the keyboard, in `$.clock` time: keys typed within
       * TYPE_THROUGH_MS after it (lib/keys.ts) are dropped as typed through (views and user panes).
       */
      openedAt: Record<string, number>
      /**
       * When each pane (by id) last saw one of its keys pressed, or its ring moved by the mod, in `$.clock` time: an
       * Enter on an action (a row, a card, a move target, accept, sync) within TYPE_THROUGH_MS after it is dropped as
       * typed through, so a word typed for the prompt never presses what its `j` or `k` moved the ring onto.
       */
      keyAt: Record<string, number>
      // Feature slices: each feature file owns the keys between its markers.
      // <feature:context>
      /** Page titles and one-line summaries of the initialized wikis (index.md rows), for prompt-time lookups. */
      wikiIndex: NfWikiPage[]
      /** The flowie profile digest for the system prompt (identity and wellbeing left out), or null. */
      profileDigest: string | null
      // </feature:context>
      // <feature:bookkeeping>
      /** Lines in the command's reasoning log when it started (to see whether a decision was logged). */
      reasoningBaseline: NfReasoningBaseline | null
      /** A decision the mod drafted after a command turn that logged none; kept only if a person presses keep. */
      draftedDecision: NfDraftedDecision | null
      // </feature:bookkeeping>
      // <feature:status>
      // </feature:status>
      // <feature:guards>
      /** Whether this machine is an HPC login node (null until the first shell call checks). */
      loginNode: boolean | null
      /** The /git alias running in this turn (a, c, ac, acp, p, pl, ps, b, pr), for GIT-ALIAS-SCOPE. */
      gitAlias: string | null
      /** The documented .neuroflow/ structure from nf_check.py --structure (null until read). */
      memoryStructure: { rootFiles: string[]; rootFolders: string[] } | null
      // </feature:guards>
      // <feature:views>
      dashboardTab: NfDashboardTab
      /** The band is hidden for the rest of the day (the preference is kept in $.store). */
      bandHidden: boolean
      loopView: NfLoopView | null
      /** A line the phase picker shows (e.g. why it could not switch). */
      pickerNote: string | null
      /** Every level's task board, read when the dashboard's tasks tab or the board pane opens (null until then). */
      taskView: NfTaskView | null
      /** The level the board pane shows (an NfTaskLevel id); null picks one as the pane opens. */
      boardLevel: string | null
      /** Whether today's wellbeing entry is already on the flowie remote (#253); null before a check started. */
      wellbeingCheck: NfWellbeingCheck | null
      /** The task card picked on the board, to move it. */
      boardPick: string | null
      /**
       * How often the band took the keys (^X Tab or a click): a mirror of the `$.store` key `keys.learned`,
       * which stays the truth across sessions; null until the session read it. The band teaches the chord
       * until it reaches three.
       */
      keysLearned: number | null
      /**
       * Per pane id, the element the focus ring was last moved onto (a card, a move target, a now-tab action, a
       * key). Absent while the ring is on none of the pane's elements: since the pane opened, its tab changed or
       * the ring went to one of the engine's own stops.
       */
      paneRing: Record<string, string>
      // </feature:views>
      // <feature:loop>
      /** The autoresearch loop the mod is driving, one iteration per turn (null when none). */
      drive: NfDrive | null
      // </feature:loop>
      // <feature:capture>
      /** Live note capture in progress (the flag .neuroflow/notes/.capturing names the target). */
      capture: { target: string; count: number } | null
      // </feature:capture>
      // <feature:checks>
      /** Citable files written in this turn (any agent), checked by cite_check.py when the turn ends. */
      citeQueue: string[]
      // </feature:checks>
      // <feature:user>
      /** The living paper pane: the status line, gaps, open Results slots and changed sources (U1). */
      paperView: NfPaperView | null
      /** The X-ray pane: the newest X-ray's findings (U3). */
      xrayView: NfXrayView | null
      /** The X-ray finding picked in the pane. */
      xrayPick: string | null
      /** The auto-wiki cards waiting for review, as the review pane shows them (U2). */
      wikiCards: NfWikiCard[]
      /** The card picked in the review pane (its file name). */
      wikiPick: string | null
      // </feature:user>
    }
  }
}
