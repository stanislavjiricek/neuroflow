# Skill Creator Reference Schemas

JSON schemas for all files produced and consumed by the skill creator workflow.

---

## evals.json

Defines the evaluation suite for a skill. Create this before running evals.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "description", "prompt", "expectations"],
    "properties": {
      "id": {
        "type": "string",
        "description": "Unique identifier for this eval (e.g., 'basic_pdf', 'multi_page_doc')"
      },
      "description": {
        "type": "string",
        "description": "Human-readable description of what this eval tests"
      },
      "prompt": {
        "type": "string",
        "description": "The exact prompt to send to the agent"
      },
      "expectations": {
        "type": "array",
        "description": "List of assertions to check on the output",
        "items": {
          "type": "object",
          "required": ["id", "description", "assertion"],
          "properties": {
            "id": {
              "type": "string",
              "description": "Unique assertion identifier within this eval"
            },
            "description": {
              "type": "string",
              "description": "Human-readable description of what this assertion checks"
            },
            "assertion": {
              "type": "string",
              "description": "Grader instruction: what to look for in the output (checked by grader agent)"
            }
          }
        }
      },
      "setup": {
        "type": "object",
        "description": "Optional setup configuration for this eval",
        "properties": {
          "files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Paths to files needed for this eval"
          },
          "env": {
            "type": "object",
            "description": "Environment variables to set for this eval"
          }
        }
      }
    }
  }
}
```

### Example

```json
[
  {
    "id": "basic_conversion",
    "description": "Convert a simple PDF to markdown",
    "prompt": "Convert the file report.pdf to markdown format",
    "expectations": [
      {
        "id": "is_markdown",
        "description": "Output is valid markdown",
        "assertion": "The output contains markdown formatting elements like headers (#), lists (-), or bold (**text**)"
      },
      {
        "id": "preserves_content",
        "description": "Key content is preserved",
        "assertion": "The output preserves the main textual content from the source document"
      }
    ]
  }
]
```

---

## history.json

Tracks the improvement history across skill versions. Updated by `run_loop.py` at the end of each iteration.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["skill_name", "iterations"],
  "properties": {
    "skill_name": {
      "type": "string",
      "description": "Name of the skill being improved"
    },
    "iterations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["iteration", "timestamp", "pass_rate", "skill_snapshot_path"],
        "properties": {
          "iteration": {
            "type": "integer",
            "description": "Iteration number, starting at 1"
          },
          "timestamp": {
            "type": "string",
            "format": "date-time"
          },
          "pass_rate": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Fraction of assertions that passed (0.0 to 1.0)"
          },
          "skill_snapshot_path": {
            "type": "string",
            "description": "Path to archived copy of SKILL.md for this iteration"
          },
          "notes": {
            "type": "string",
            "description": "Optional free-form notes about changes made this iteration"
          }
        }
      }
    }
  }
}
```

---

## grading.json

Output from the Grader Agent. One entry per eval × run × assertion.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["eval_id", "run_id", "grades"],
  "properties": {
    "eval_id": {
      "type": "string",
      "description": "ID of the eval that was graded"
    },
    "run_id": {
      "type": "string",
      "description": "Unique identifier for this run (typically a timestamp or UUID)"
    },
    "grades": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["expectation_id", "pass", "reason"],
        "properties": {
          "expectation_id": {
            "type": "string",
            "description": "ID of the assertion being graded"
          },
          "pass": {
            "type": "boolean",
            "description": "Whether the assertion passed"
          },
          "reason": {
            "type": "string",
            "description": "Grader explanation of why this passed or failed"
          },
          "evidence": {
            "type": "string",
            "description": "Optional: specific text from the output that supports the grade"
          }
        }
      }
    },
    "overall_pass": {
      "type": "boolean",
      "description": "True only if all assertions passed"
    }
  }
}
```

---

## metrics.json

Execution metrics for a single eval run. Written by `run_eval.py`.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["eval_id", "run_id", "time_seconds", "tokens"],
  "properties": {
    "eval_id": {"type": "string"},
    "run_id": {"type": "string"},
    "time_seconds": {
      "type": "number",
      "description": "Wall-clock time from prompt send to output received"
    },
    "tokens": {
      "type": "object",
      "properties": {
        "input": {"type": "integer"},
        "output": {"type": "integer"},
        "total": {"type": "integer"}
      }
    },
    "tool_calls": {
      "type": "integer",
      "description": "Number of tool calls made during execution"
    },
    "error": {
      "type": ["string", "null"],
      "description": "Error message if the run failed, null otherwise"
    }
  }
}
```

---

## timing.json

Aggregated timing statistics across all runs. Written by `aggregate_benchmark.py`.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "description": "Timing aggregates keyed by eval_id",
  "additionalProperties": {
    "type": "object",
    "properties": {
      "mean_seconds": {"type": "number"},
      "std_seconds": {"type": "number"},
      "min_seconds": {"type": "number"},
      "max_seconds": {"type": "number"},
      "runs": {"type": "integer"}
    }
  }
}
```

---

## benchmark.json

Complete benchmark run data for a single benchmark or run_loop iteration. This is what `generate_review.py` reads to produce the HTML report.

> **Important field names**: The viewer expects `configuration` (not `config`), and pass rate is at `result.pass_rate` (not top-level).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["skill_name", "timestamp", "configurations", "runs", "run_summary"],
  "properties": {
    "skill_name": {
      "type": "string"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "configurations": {
      "type": "array",
      "description": "List of configurations tested (e.g., ['with_skill', 'without_skill'])",
      "items": {"type": "string"}
    },
    "runs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["eval_id", "configuration", "run_index", "result"],
        "properties": {
          "eval_id": {"type": "string"},
          "configuration": {
            "type": "string",
            "description": "Which configuration this run used (matches entry in configurations[])"
          },
          "run_index": {
            "type": "integer",
            "description": "0-based index for repeated runs of the same eval+configuration"
          },
          "result": {
            "type": "object",
            "required": ["pass_rate", "grades"],
            "properties": {
              "pass_rate": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
              },
              "grades": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "expectation_id": {"type": "string"},
                    "pass": {"type": "boolean"},
                    "reason": {"type": "string"}
                  }
                }
              }
            }
          },
          "metrics": {
            "type": "object",
            "properties": {
              "time_seconds": {"type": "number"},
              "tokens": {"type": "object"},
              "tool_calls": {"type": "integer"}
            }
          }
        }
      }
    },
    "run_summary": {
      "type": "object",
      "description": "Aggregated pass rates keyed by eval_id, then configuration",
      "additionalProperties": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "properties": {
            "pass_rate": {"type": "number"},
            "runs": {"type": "integer"},
            "std": {"type": "number"}
          }
        }
      }
    },
    "analyzer_notes": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Optional notes from the Analyzer Agent"
    }
  }
}
```

---

## comparison.json

Output from the Blind Comparator Agent.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["winner", "reasoning", "scores"],
  "properties": {
    "winner": {
      "type": "string",
      "enum": ["A", "B", "tie"],
      "description": "Which output was better, or tie if indistinguishable"
    },
    "reasoning": {
      "type": "string",
      "description": "Detailed explanation of why the winner was chosen"
    },
    "scores": {
      "type": "object",
      "description": "Scores on comparison rubric dimensions",
      "properties": {
        "content": {
          "type": "object",
          "properties": {
            "A": {"type": "number", "minimum": 1, "maximum": 5},
            "B": {"type": "number", "minimum": 1, "maximum": 5}
          }
        },
        "structure": {
          "type": "object",
          "properties": {
            "A": {"type": "number", "minimum": 1, "maximum": 5},
            "B": {"type": "number", "minimum": 1, "maximum": 5}
          }
        }
      }
    },
    "eval_id": {
      "type": "string",
      "description": "Which eval this comparison was for"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

---

## analysis.json

Output from the Post-hoc Analyzer Agent (see `agents/analyzer.md`).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["comparison_summary", "winner_strengths", "loser_weaknesses", "improvement_suggestions"],
  "properties": {
    "comparison_summary": {
      "type": "object",
      "properties": {
        "winner": {"type": "string", "enum": ["A", "B"]},
        "winner_skill": {"type": "string"},
        "loser_skill": {"type": "string"},
        "comparator_reasoning": {"type": "string"}
      }
    },
    "winner_strengths": {
      "type": "array",
      "items": {"type": "string"},
      "description": "What made the winner better"
    },
    "loser_weaknesses": {
      "type": "array",
      "items": {"type": "string"},
      "description": "What held the loser back"
    },
    "instruction_following": {
      "type": "object",
      "properties": {
        "winner": {
          "type": "object",
          "properties": {
            "score": {"type": "number", "minimum": 1, "maximum": 10},
            "issues": {"type": "array", "items": {"type": "string"}}
          }
        },
        "loser": {
          "type": "object",
          "properties": {
            "score": {"type": "number", "minimum": 1, "maximum": 10},
            "issues": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    },
    "improvement_suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["priority", "category", "suggestion"],
        "properties": {
          "priority": {
            "type": "string",
            "enum": ["high", "medium", "low"]
          },
          "category": {
            "type": "string",
            "enum": ["instructions", "tools", "examples", "error_handling", "structure", "references"]
          },
          "suggestion": {"type": "string"},
          "expected_impact": {"type": "string"}
        }
      }
    },
    "transcript_insights": {
      "type": "object",
      "properties": {
        "winner_execution_pattern": {"type": "string"},
        "loser_execution_pattern": {"type": "string"}
      }
    }
  }
}
```
