/* ── Neuroflow Mind — concept map visualization ────────────────────────────── */
/* Activated only on the /mind page. Uses D3 v7 (loaded dynamically).         */

(function () {
  "use strict";

  /* ── Graph data ──────────────────────────────────────────────────────────── */

  var NODES = [
    /* ── Personal Profile ── */
    {
      id: "c-profile",  label: "Research Profile",     category: "personal-profile",
      desc: "Your identity as a researcher — stances, writing voice, methodological preferences. Read silently by every phase to shape assistance.",
      commands: ["/flowie --init", "/flowie --view", "/flowie --identify"],
      url: "commands/flowie/"
    },
    {
      id: "c-wiki",     label: "Personal Wiki",         category: "personal-profile",
      desc: "Karpathy-style second brain — ingest sources, synthesize knowledge across sessions, query your accumulated understanding, lint for orphans and contradictions.",
      commands: ["/flowie --wiki-ingest", "/flowie --wiki-query", "/flowie --wiki-lint", "/flowie --wiki-add"],
      url: "skills/wiki/SKILL/"
    },
    {
      id: "c-tasks",    label: "Task Board",            category: "personal-profile",
      desc: "Cross-project Kanban board — inbox / active / review / done. One markdown file per task, linked to a flowie project entry.",
      commands: ["/flowie --tasks", "/flowie --tasks --add", "/flowie --tasks --move"],
      url: "commands/flowie/"
    },
    {
      id: "c-wellbeing",label: "Wellbeing",             category: "personal-profile",
      desc: "Opt-in daily self-assessment — anxiety, energy, and happiness on a 1–10 scale (5 = neutral). Prompted automatically on sync if enabled.",
      commands: ["/flowie --assess"],
      url: "commands/flowie/"
    },
    {
      id: "c-registry", label: "Project Registry",     category: "personal-profile",
      desc: "Phase timelines across all your research projects. Links repos to flowie project entries and auto-updates when you change phase.",
      commands: ["/flowie --projects", "/flowie --link"],
      url: "commands/flowie/"
    },
    {
      id: "c-ideas",    label: "Cross-project Ideas",  category: "personal-profile",
      desc: "Hypotheses and insights that span multiple projects. Feeds into the personal wiki and can evolve into new research directions.",
      commands: ["/flowie --wiki-ingest", "/flowie --view"],
      url: "commands/flowie/"
    },

    /* ── Project Memory ── */
    {
      id: "c-memory",   label: "Project Memory",       category: "project",
      desc: "Per-project knowledge store at .neuroflow/ — sessions, reasoning logs, flow index, phase subfolders, objectives. The persistent brain every command reads and writes.",
      commands: ["/neuroflow", "/setup", "/phase"],
      url: "concepts/project-memory/"
    },

    /* ── Research Pipeline ── */
    {
      id: "c-discovery",     label: "Discovery",       category: "pipeline",
      desc: "Ideation, literature search, brainstorming. The scholar agent runs sequential searches across bioRxiv and runs a 12-lens analytical review of downloaded papers.",
      commands: ["/ideation", "/search"],
      url: "commands/ideation/"
    },
    {
      id: "c-formalization", label: "Formalization",   category: "pipeline",
      desc: "Preregistration, hypothesis formalization, open science. Generates OSF-compatible documents. Constrains what data collection and analysis can do.",
      commands: ["/preregistration"],
      url: "commands/preregistration/"
    },
    {
      id: "c-funding",       label: "Funding",         category: "pipeline",
      desc: "Grant writing (NIH R01/R21, ERC, Wellcome, DFG) and budget tracking. Runs in parallel with hypothesis formalization.",
      commands: ["/grant-proposal", "/finance"],
      url: "commands/grant-proposal/"
    },
    {
      id: "c-experiment",    label: "Experiment",      category: "pipeline",
      desc: "Paradigm design in PsychoPy, LSL hardware integration, BIDS recording parameters, eye-tracking setup. Shaped by the preregistration.",
      commands: ["/experiment", "/tool-build", "/tool-validate"],
      url: "commands/experiment/"
    },
    {
      id: "c-data",          label: "Data",            category: "pipeline",
      desc: "BIDS structure validation, data ingestion, format conversion (EDF, BrainVision, NWB), preprocessing pipeline — filtering, ICA, epoching, QC reports.",
      commands: ["/data", "/data-preprocess"],
      url: "commands/data/"
    },
    {
      id: "c-analysis",      label: "Analysis",        category: "pipeline",
      desc: "ERPs, time-frequency, connectivity, decoding, GLM, brain simulation (NEURON, Brian2, NetPyNE, NEST). Results with built-in reproducibility auditing.",
      commands: ["/data-analyze", "/brain-build", "/brain-optimize", "/brain-run"],
      url: "commands/data-analyze/"
    },
    {
      id: "c-writing",       label: "Writing",         category: "pipeline",
      desc: "Manuscripts and peer review. Every section goes through a write→critique loop (paper-writer + paper-critic agents) before anything is saved.",
      commands: ["/paper", "/review"],
      url: "commands/paper/"
    },
    {
      id: "c-communication", label: "Communication",   category: "pipeline",
      desc: "Posters (LaTeX, 5 templates), slide decks, phase reports, and project output archives. Final outputs from the research pipeline.",
      commands: ["/poster", "/slideshow", "/write-report", "/output"],
      url: "commands/poster/"
    },

    /* ── Team Integration ── */
    {
      id: "c-team",     label: "Team Integration",     category: "team",
      desc: "Hive — shared GitHub org repo for team-level knowledge. Coordinates research directions and surfaces cross-project findings. Meetings with calendar integration and 3-tier task model (flowie/project/hive). All sharing is explicit, never automatic.",
      commands: ["/hive", "/meeting"],
      url: "commands/hive/"
    },

    /* ── Utilities & Quality ── */
    {
      id: "c-quality",    label: "Quality & Audit",   category: "utilities",
      desc: "Sentinel (11 consistency checks on .neuroflow/ structure, preregistration drift, sensitive data), fails log (structured failure reports), and tool validation.",
      commands: ["/sentinel", "/fails", "/tool-validate"],
      url: "commands/sentinel/"
    },
    {
      id: "c-automation", label: "Automation",        category: "utilities",
      desc: "Autoresearch infinite worker-evaluator loop (any artifact, any phase, live dashboard), multi-step pipeline orchestration, and hook triggers on tool events.",
      commands: ["/autoresearch", "/pipeline"],
      url: "commands/autoresearch/"
    },
    {
      id: "c-utilities",  label: "Utilities",         category: "utilities",
      desc: "Git version control, scoped search, phase tracking, notes capture, quiz, interview, and idk — the everyday tools that keep a project running.",
      commands: ["/git", "/search", "/notes", "/quiz", "/interview", "/phase", "/idk"],
      url: "commands/git/"
    }
  ];

  var LINKS = [
    /* Personal Profile internal */
    { source: "c-profile",  target: "c-wiki",          type: "knowledge" },
    { source: "c-wiki",     target: "c-ideas",         type: "knowledge" },
    { source: "c-tasks",    target: "c-registry",      type: "coordination" },

    /* Profile → Pipeline */
    { source: "c-profile",  target: "c-writing",       type: "knowledge" },
    { source: "c-profile",  target: "c-discovery",     type: "knowledge" },

    /* Wiki → Pipeline */
    { source: "c-wiki",     target: "c-discovery",     type: "knowledge" },

    /* Ideas → Discovery */
    { source: "c-ideas",    target: "c-discovery",     type: "knowledge" },

    /* Registry → Memory */
    { source: "c-registry", target: "c-memory",        type: "storage" },

    /* Memory ↔ Pipeline (stores) */
    { source: "c-memory",   target: "c-discovery",     type: "storage" },
    { source: "c-memory",   target: "c-analysis",      type: "storage" },
    { source: "c-memory",   target: "c-writing",       type: "storage" },

    /* Memory ↔ Quality */
    { source: "c-quality",  target: "c-memory",        type: "storage" },

    /* Research pipeline flow */
    { source: "c-discovery",     target: "c-formalization", type: "pipeline" },
    { source: "c-formalization", target: "c-funding",       type: "pipeline" },
    { source: "c-formalization", target: "c-experiment",    type: "pipeline" },
    { source: "c-experiment",    target: "c-data",          type: "pipeline" },
    { source: "c-data",          target: "c-analysis",      type: "pipeline" },
    { source: "c-analysis",      target: "c-writing",       type: "pipeline" },
    { source: "c-writing",       target: "c-communication", type: "pipeline" },

    /* Automation → Pipeline */
    { source: "c-automation", target: "c-analysis",    type: "improvement" },
    { source: "c-automation", target: "c-writing",     type: "improvement" },
    { source: "c-automation", target: "c-memory",      type: "improvement" },

    /* Team */
    { source: "c-team",     target: "c-memory",        type: "coordination" },
    { source: "c-team",     target: "c-discovery",     type: "coordination" },

    /* Utilities → Memory */
    { source: "c-utilities", target: "c-memory",       type: "storage" }
  ];

  /* ── Visual config ───────────────────────────────────────────────────────── */
  var CATEGORY_CONFIG = {
    "personal-profile": { color: "#ce93d8", glow: "#9c27b0", radius: 13 },
    "project":          { color: "#ffd54f", glow: "#f9a825", radius: 17 },
    "pipeline":         { color: "#7c4dff", glow: "#651fff", radius: 13 },
    "team":             { color: "#66bb6a", glow: "#43a047", radius: 13 },
    "utilities":        { color: "#26c6da", glow: "#00acc1", radius: 13 }
  };

  var CATEGORY_LABELS = {
    "personal-profile": "PERSONAL PROFILE",
    "project":          "PROJECT MEMORY",
    "pipeline":         "RESEARCH PIPELINE",
    "team":             "TEAM INTEGRATION",
    "utilities":        "UTILITIES & QUALITY"
  };

  /* ── Link type colors ────────────────────────────────────────────────────── */
  var LINK_COLORS = {
    "pipeline":     "rgba(124,77,255,0.45)",
    "knowledge":    "rgba(206,147,216,0.50)",
    "storage":      "rgba(38,198,218,0.40)",
    "coordination": "rgba(102,187,106,0.40)",
    "improvement":  "rgba(255,183,77,0.50)"
  };

  var LINK_LABELS = {
    "pipeline":     "research flow",
    "knowledge":    "knowledge flow",
    "storage":      "stores / audits",
    "coordination": "coordination",
    "improvement":  "improves"
  };

  /* ── Category cluster angles (clockwise degrees from 12 o'clock) ─────────── */
  var CATEGORY_ANGLES = {
    "personal-profile": 350,
    "project":           45,
    "pipeline":         180,
    "team":             270,
    "utilities":        310
  };

  /* ── State ───────────────────────────────────────────────────────────────── */
  var simulation = null;
  var selectedId = null;

  /* ── Main init (called after D3 loaded) ─────────────────────────────────── */
  function initMindGraph() {
    var root = document.getElementById("nf-mind-root");
    if (!root) return;

    root.querySelectorAll("svg, #nf-mind-panel").forEach(function(el) { el.remove(); });

    var W = root.clientWidth  || window.innerWidth;
    var H = root.clientHeight || window.innerHeight - 60;

    /* ── SVG setup ── */
    var svg = d3.select(root).append("svg")
      .attr("width",  "100%")
      .attr("height", "100%")
      .attr("viewBox", "0 0 " + W + " " + H)
      .style("display", "block");

    /* ── Defs: glow filters ── */
    var defs = svg.append("defs");

    function addGlow(id, color, blur, strength) {
      var f = defs.append("filter").attr("id", id).attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
      f.append("feGaussianBlur").attr("in", "SourceGraphic").attr("stdDeviation", blur).attr("result", "blur");
      var feMerge = f.append("feMerge");
      for (var i = 0; i < strength; i++) feMerge.append("feMergeNode").attr("in", "blur");
      feMerge.append("feMergeNode").attr("in", "SourceGraphic");
    }

    Object.keys(CATEGORY_CONFIG).forEach(function(cat) {
      addGlow("glow-" + cat, CATEGORY_CONFIG[cat].glow, 6, 2);
    });
    addGlow("glow-select", "#ffffff", 8, 4);

    /* ── Starfield background ── */
    var bg = svg.append("g").attr("class", "nf-stars");
    var rng = mulberry32(42);
    for (var s = 0; s < 220; s++) {
      bg.append("circle")
        .attr("cx", rng() * W)
        .attr("cy", rng() * H)
        .attr("r",  rng() * 1.4 + 0.2)
        .attr("fill", "rgba(255,255,255," + (rng() * 0.35 + 0.05) + ")");
    }

    /* ── Category legend (top-left) ── */
    var legend = svg.append("g").attr("transform", "translate(20,20)");
    var legendItems = Object.keys(CATEGORY_CONFIG).map(function(cat) {
      return { cat: cat, label: CATEGORY_LABELS[cat] };
    });
    legendItems.forEach(function(item, i) {
      var g = legend.append("g").attr("transform", "translate(0," + (i * 22) + ")");
      g.append("circle").attr("r", 6).attr("cx", 7).attr("cy", 7)
        .attr("fill", CATEGORY_CONFIG[item.cat].color)
        .attr("filter", "url(#glow-" + item.cat + ")");
      g.append("text").attr("x", 18).attr("y", 11)
        .attr("fill", "rgba(255,255,255,0.65)")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")
        .text(item.label.toLowerCase());
    });

    /* ── Link type legend (bottom-left) ── */
    var hint = svg.append("g").attr("transform", "translate(20," + (H - 80) + ")");
    Object.keys(LINK_LABELS).forEach(function(type, i) {
      var g = hint.append("g").attr("transform", "translate(0," + (i * 18) + ")");
      g.append("line").attr("x1", 0).attr("y1", 7).attr("x2", 22).attr("y2", 7)
        .attr("stroke", LINK_COLORS[type]).attr("stroke-width", 2)
        .attr("stroke-dasharray", type === "coordination" ? "4,3" : null);
      g.append("text").attr("x", 28).attr("y", 11)
        .attr("fill", "rgba(255,255,255,0.5)")
        .attr("font-size", "10px")
        .attr("font-family", "Inter, sans-serif")
        .text(LINK_LABELS[type]);
    });

    /* ── Build graph data ── */
    var nodeMap = {};
    var nodes = NODES.map(function(n) {
      var nd = Object.assign({}, n);
      nodeMap[n.id] = nd;
      return nd;
    });

    var links = LINKS.map(function(l) {
      return { source: l.source, target: l.target, type: l.type };
    });

    /* ── Cluster layout helpers ── */
    var viewportR = Math.min(W, H) / 2;

    function clusterAngleRad(d) {
      var deg = CATEGORY_ANGLES[d.category] !== undefined ? CATEGORY_ANGLES[d.category] : 0;
      return (deg - 90) * Math.PI / 180;
    }

    function clusterRadius(d) {
      /* Project Memory sits closer to center — it connects to everything */
      if (d.id === "c-memory") return viewportR * 0.30;
      return viewportR * 0.60;
    }

    function clusterX(d) {
      return W / 2 + clusterRadius(d) * Math.cos(clusterAngleRad(d));
    }

    function clusterY(d) {
      return H / 2 + clusterRadius(d) * Math.sin(clusterAngleRad(d));
    }

    /* Pre-position nodes near their cluster target */
    var rng2 = mulberry32(99);
    nodes.forEach(function(d) {
      d.x = clusterX(d) + (rng2() - 0.5) * 20;
      d.y = clusterY(d) + (rng2() - 0.5) * 20;
    });

    /* ── Force simulation ── */
    simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(function(d) { return d.id; }).distance(function(d) {
        if (d.type === "pipeline")     return 85;
        if (d.type === "knowledge")    return 80;
        if (d.type === "storage")      return 75;
        if (d.type === "coordination") return 90;
        return 80;
      }).strength(0.6))
      .force("charge", d3.forceManyBody().strength(function(d) {
        return d.id === "c-memory" ? -300 : -80;
      }))
      .force("x", d3.forceX(function(d) { return clusterX(d); }).strength(0.20))
      .force("y", d3.forceY(function(d) { return clusterY(d); }).strength(0.20))
      .force("collision", d3.forceCollide().radius(function(d) {
        return CATEGORY_CONFIG[d.category].radius + 10;
      }))
      .alphaDecay(0.018)
      .velocityDecay(0.38);

    /* ── Draw links ── */
    var linkG = svg.append("g").attr("class", "nf-links");
    var linkSel = linkG.selectAll("line")
      .data(links)
      .enter().append("line")
      .attr("stroke", function(d) { return LINK_COLORS[d.type] || "rgba(255,255,255,0.2)"; })
      .attr("stroke-width", function(d) {
        return d.type === "pipeline" || d.type === "improvement" ? 1.5 : 1;
      })
      .attr("stroke-dasharray", function(d) {
        return d.type === "coordination" ? "4,3" : null;
      })
      .attr("class", "nf-link");

    /* ── Draw nodes ── */
    var nodeG = svg.append("g").attr("class", "nf-nodes");
    var nodeSel = nodeG.selectAll("g.nf-node")
      .data(nodes)
      .enter().append("g")
      .attr("class", "nf-node")
      .style("cursor", "pointer")
      .call(d3.drag()
        .on("start", dragStarted)
        .on("drag",  dragged)
        .on("end",   dragEnded))
      .on("click",     onNodeClick)
      .on("mouseover", onNodeOver)
      .on("mouseout",  onNodeOut);

    /* Outer glow ring */
    nodeSel.append("circle")
      .attr("class", "nf-node-ring")
      .attr("r", function(d) { return CATEGORY_CONFIG[d.category].radius + 6; })
      .attr("fill", "none")
      .attr("stroke", function(d) { return CATEGORY_CONFIG[d.category].color; })
      .attr("stroke-width", 1.5)
      .attr("opacity", 0);

    /* Main circle */
    nodeSel.append("circle")
      .attr("class", "nf-node-circle")
      .attr("r", function(d) { return CATEGORY_CONFIG[d.category].radius; })
      .attr("fill", function(d) { return CATEGORY_CONFIG[d.category].color; })
      .attr("filter", function(d) { return "url(#glow-" + d.category + ")"; })
      .attr("opacity", 0.92);

    /* Project Memory pulse ring */
    nodeSel.filter(function(d) { return d.id === "c-memory"; })
      .append("circle")
      .attr("class", "nf-core-pulse")
      .attr("r", 22)
      .attr("fill", "none")
      .attr("stroke", "#ffd54f")
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.5);

    /* Labels */
    nodeSel.append("text")
      .attr("class", "nf-node-label")
      .attr("dy", function(d) { return CATEGORY_CONFIG[d.category].radius + 12; })
      .attr("text-anchor", "middle")
      .attr("font-size", function(d) { return d.id === "c-memory" ? "12px" : "10px"; })
      .attr("font-weight", function(d) { return d.id === "c-memory" ? "700" : "500"; })
      .attr("font-family", "Inter, JetBrains Mono, monospace")
      .attr("fill", function(d) { return d.id === "c-memory" ? "#fff8e1" : "rgba(255,255,255,0.72)"; })
      .attr("pointer-events", "none")
      .text(function(d) { return d.label; });

    /* ── Info panel ── */
    var panel = document.createElement("div");
    panel.id = "nf-mind-panel";
    panel.className = "nf-mind-panel";
    panel.innerHTML = '<div class="nf-mind-panel-inner">' +
      '<button class="nf-mind-close" aria-label="Close panel">✕</button>' +
      '<span class="nf-mind-panel-type"></span>' +
      '<h3 class="nf-mind-panel-title"></h3>' +
      '<p class="nf-mind-panel-desc"></p>' +
      '<div class="nf-mind-panel-tags"></div>' +
      '<div class="nf-mind-panel-connections"></div>' +
      '<a class="nf-mind-panel-link md-button md-button--primary" href="#" target="_self">View docs →</a>' +
      '</div>';
    root.appendChild(panel);

    panel.querySelector(".nf-mind-close").addEventListener("click", function() {
      closePanel();
    });

    /* ── Zoom & pan ── */
    var zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on("zoom", function(event) {
        linkG.attr("transform", event.transform);
        nodeG.attr("transform", event.transform);
      });
    svg.call(zoom);

    /* ── Tick ── */
    simulation.on("tick", function() {
      linkSel
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

      nodeSel.attr("transform", function(d) {
        return "translate(" + d.x + "," + d.y + ")";
      });
    });

    /* ── Pulse animation ── */
    animatePulse();

    /* ── Helpers ── */

    function onNodeClick(event, d) {
      event.stopPropagation();
      if (selectedId === d.id) { closePanel(); return; }
      selectedId = d.id;
      showPanel(d);
      highlightConnected(d.id);
    }

    function onNodeOver(event, d) {
      if (selectedId) return;
      d3.select(this).select(".nf-node-ring").attr("opacity", 0.6);
      d3.select(this).select(".nf-node-circle").attr("opacity", 1);
      highlightConnected(d.id);
    }

    function onNodeOut(event, d) {
      if (selectedId) return;
      d3.select(this).select(".nf-node-ring").attr("opacity", 0);
      resetHighlight();
    }

    function highlightConnected(nodeId) {
      var connectedIds = new Set([nodeId]);

      links.forEach(function(l) {
        var srcId = l.source.id || l.source;
        var tgtId = l.target.id || l.target;
        if (srcId === nodeId || tgtId === nodeId) {
          connectedIds.add(srcId);
          connectedIds.add(tgtId);
        }
      });

      nodeSel.each(function(d) {
        var connected = connectedIds.has(d.id);
        d3.select(this).select(".nf-node-circle").transition().duration(200).attr("opacity", connected ? 1 : 0.12);
        d3.select(this).select(".nf-node-label").transition().duration(200).attr("opacity", connected ? 1 : 0.12);
        d3.select(this).select(".nf-node-ring").attr("opacity", d.id === nodeId ? 0.7 : (connected ? 0.35 : 0));
      });

      linkSel.transition().duration(200)
        .attr("opacity", function(l) {
          var srcId = l.source.id || l.source;
          var tgtId = l.target.id || l.target;
          return (srcId === nodeId || tgtId === nodeId) ? 1 : 0.05;
        })
        .attr("stroke-width", function(l) {
          var srcId = l.source.id || l.source;
          var tgtId = l.target.id || l.target;
          return (srcId === nodeId || tgtId === nodeId) ? 2.5 : 1;
        });
    }

    function resetHighlight() {
      nodeSel.each(function(d) {
        d3.select(this).select(".nf-node-circle").transition().duration(200).attr("opacity", 0.92);
        d3.select(this).select(".nf-node-label").transition().duration(200).attr("opacity", 1);
        d3.select(this).select(".nf-node-ring").attr("opacity", 0);
      });
      linkSel.transition().duration(200).attr("opacity", 1).attr("stroke-width", function(d) {
        return d.type === "pipeline" || d.type === "improvement" ? 1.5 : 1;
      });
    }

    function showPanel(d) {
      var cfg = CATEGORY_CONFIG[d.category];

      panel.querySelector(".nf-mind-panel-type").textContent = CATEGORY_LABELS[d.category] || d.category.toUpperCase();
      panel.querySelector(".nf-mind-panel-type").style.color = cfg.color;
      panel.querySelector(".nf-mind-panel-title").textContent = d.label;
      panel.querySelector(".nf-mind-panel-desc").textContent = d.desc;

      /* Commands list (replaces tags) */
      var tagsDiv = panel.querySelector(".nf-mind-panel-tags");
      var cmds = d.commands || [];
      if (cmds.length) {
        var html = '<p class="nf-conn-heading">Commands</p><div class="nf-tag-pills">';
        cmds.forEach(function(cmd) {
          html += '<span class="nf-tag-pill" style="border-color:' + cfg.color + ';color:' + cfg.color + '">' + cmd + '</span>';
        });
        html += '</div>';
        tagsDiv.innerHTML = html;
      } else {
        tagsDiv.innerHTML = "";
      }

      /* Connections list */
      var connDiv = panel.querySelector(".nf-mind-panel-connections");
      var connectedNodes = [];
      links.forEach(function(l) {
        var srcId = l.source.id || l.source;
        var tgtId = l.target.id || l.target;
        var other = null, rel = "";
        if (srcId === d.id) { other = nodeMap[tgtId]; rel = l.type + " →"; }
        else if (tgtId === d.id) { other = nodeMap[srcId]; rel = "← " + l.type; }
        if (other) connectedNodes.push({ node: other, rel: rel });
      });

      if (connectedNodes.length) {
        var connHtml = '<p class="nf-conn-heading">Connections (' + connectedNodes.length + ')</p><ul class="nf-conn-list">';
        connectedNodes.forEach(function(cn) {
          connHtml += '<li><span style="color:' + CATEGORY_CONFIG[cn.node.category].color + '">◆</span> ' +
            '<span class="nf-conn-rel">' + cn.rel + '</span> ' +
            '<strong>' + cn.node.label + '</strong></li>';
        });
        connHtml += '</ul>';
        connDiv.innerHTML = connHtml;
      } else {
        connDiv.innerHTML = "";
      }

      /* Doc link */
      var link = panel.querySelector(".nf-mind-panel-link");
      if (d.url) {
        var currentPath = window.location.pathname;
        var siteRoot = currentPath.replace(/\/mind\/?$/, "/");
        link.href = siteRoot + d.url;
        link.style.display = "";
      } else {
        link.style.display = "none";
      }

      panel.classList.add("nf-mind-panel--open");
    }

    function closePanel() {
      selectedId = null;
      panel.classList.remove("nf-mind-panel--open");
      resetHighlight();
    }

    svg.on("click", function() {
      if (selectedId) closePanel();
    });

    /* ── Drag ── */
    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    }
    function dragged(event, d) {
      d.fx = event.x; d.fy = event.y;
    }
    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null;
    }

    /* ── Pulse animation ── */
    function animatePulse() {
      svg.selectAll(".nf-core-pulse")
        .transition().duration(2000).ease(d3.easeSinInOut)
        .attr("r", 38).attr("opacity", 0)
        .transition().duration(0)
        .attr("r", 22).attr("opacity", 0.5)
        .on("end", animatePulse);
    }
  }

  /* ── Seeded PRNG for deterministic stars ─────────────────────────────────── */
  function mulberry32(seed) {
    return function() {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  /* ── D3 loader ───────────────────────────────────────────────────────────── */
  function loadD3AndInit() {
    if (!document.getElementById("nf-mind-root")) return;
    if (window.d3) { initMindGraph(); return; }

    var base = document.querySelector("base");
    var basePath = base ? base.href : "/";
    basePath = basePath.replace(/\/$/, "");

    var s = document.createElement("script");
    s.src = basePath + "/javascripts/d3.min.js";
    s.onload = initMindGraph;
    s.onerror = function() {
      var fallback = document.createElement("script");
      fallback.src = "https://d3js.org/d3.v7.min.js";
      fallback.onload = initMindGraph;
      fallback.onerror = function() {
        var root = document.getElementById("nf-mind-root");
        if (root) {
          root.innerHTML = '<p style="color:#ef9a9a;padding:2rem;font-family:Inter,sans-serif;">Failed to load the visualization library. Please reload while online.</p>';
        }
      };
      document.head.appendChild(fallback);
    };
    document.head.appendChild(s);
  }

  /* ── Hook into Material instant navigation ───────────────────────────────── */
  if (typeof document$ !== "undefined") {
    document$.subscribe(loadD3AndInit);
  } else {
    document.addEventListener("DOMContentLoaded", loadD3AndInit);
  }
})();
