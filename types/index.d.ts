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

/** One row of a phase's autoresearch pointer registry. */
export type NfLoop = { phase: string; name: string; location: string; iterations: string; best: string; status: string }

/** A typed mirror of the project's .neuroflow/ files, reloaded when they change. */
export type NfSnapshot = {
  root: string
  nfSchema: number | null
  /** 'frontmatter' for the current contract, 'legacy' for older config dialects */
  dialect: 'frontmatter' | 'legacy'
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
  /** Number of task files per board column (.neuroflow/tasks/<column>/), or null without a board. */
  taskCounts: Record<string, number> | null
  /** Autoresearch loops listed in the phases' pointer registries. */
  loops: NfLoop[]
  /** Things the loader could not read or understand, in plain words. */
  problems: string[]
  loadedAt: number
}

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

export type NfDashboardTab = 'phase' | 'deadlines' | 'integrity' | 'tasks' | 'loop'

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
      // Feature slices: each feature file owns the keys between its markers.
      // <feature:context>
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
      // </feature:guards>
      // <feature:views>
      dashboardTab: NfDashboardTab
      /** The band is hidden for the rest of the day (the preference is kept in $.store). */
      bandHidden: boolean
      loopView: NfLoopView | null
      /** A line the phase picker shows (e.g. why it could not switch). */
      pickerNote: string | null
      // </feature:views>
      // <feature:loop>
      /** The autoresearch loop the mod is driving, one iteration per turn (null when none). */
      drive: NfDrive | null
      // </feature:loop>
      // <feature:capture>
      // </feature:capture>
      // <feature:user>
      // </feature:user>
    }
  }
}
