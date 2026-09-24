"""Pre-execution checks for shell invocations (measured error classes).

p1 of the hand-discipline program (2026-09-24). Two mechanisms, each closing
a LIVE class measured from the raw 72h tool trace (``data/logs/tools.jsonl``,
see artifact ``p1_baseline_report.md``):

- **M1 argv audit** — lost-flag argv such as ``["sh","c","true"]`` passes
  every existing guard and dies only at exec with the cryptic
  ``sh: cannot open c`` (incident 2026-09-23T05:49). A deterministic
  adjacency check refuses pre-exec naming the exact fix.
- **M2 -c body parse** — a malformed compound ``sh -c 'a; b; …'`` body
  (unescaped parens, bash-only ``<(cmd)`` under sh) executes every command
  BEFORE the syntax error (incident 2026-09-24T08:04; 2026-09-21T15:53
  was a multi-command body). A no-exec ``{sh|bash} -n -c`` pre-parse
  catches it before any side effect, with the interpreter's own diagnostic.

Deliberately NOT implemented (probe-style scope narrowing):
- a py_compile preflight for run_script — CPython parses the whole file
  before executing any of it; a pre-parse saves neither a round nor a dollar.
- a staged-script import audit (ImportError class) — exec's own ImportError
  already names the missing symbol in one actionable round, while any
  audit-time symbol check carries irreducible false-positive surface
  (sys.path staging, dynamic exports, stale sys.modules post-commit).

Both mechanisms are conservative: a missing or slow checker passes through
(``_noexec_parse`` returns success on OSError/timeout), and healthy commands
are never touched.
"""
from __future__ import annotations

import subprocess

# Adjacent argv pairs → the dash the pair almost certainly lost. The dict
# key is argv[0]; the inner key is the bare flag seen next to it.
_SUSPECT_FLAG_ADJACENCIES = {
    "sh": {"c": "-c", "lc": "-lc"},
    "bash": {"c": "-c", "lc": "-lc"},
    "zsh": {"c": "-c"},
    "dash": {"c": "-c"},
    "python": {"c": "-c", "m": "-m"},
    "python3": {"c": "-c", "m": "-m"},
    "node": {"e": "-e"},
}

# Interpreters whose ``-c``/``-lc`` body M2 pre-parses no-exec.
_SHELL_INTERPRETERS = ("sh", "bash", "zsh", "dash")


def _suspect_argv_findings(cmd: list[str]) -> list[str]:
    """Lost-flag audit: interpreter immediately followed by its bare flag
    (``["sh","c","true"]`` → intended ``["sh","-c","true"]``)."""
    findings = []
    for i, tok in enumerate(cmd[:4]):
        flags = _SUSPECT_FLAG_ADJACENCIES.get(str(tok))
        if not flags:
            continue
        nxt = str(cmd[i + 1]) if i + 1 < len(cmd) else ""
        if nxt in flags:
            findings.append(
                f"'{tok}' is followed by bare '{nxt}' ('{tok} {nxt} …'), which the OS "
                f"parses as a FILE PATH — the flag lost its dash. Correct: "
                f'["{tok}", "-{nxt}", "…"] as in ["{tok}", "-c", "command"].'
            )
    return findings


def _should_parse_body(cmd: list[str]) -> str | None:
    """Return the interpreter program if cmd is a shell ``-c``/``-lc`` body call."""
    if len(cmd) >= 3 and str(cmd[0]) in _SHELL_INTERPRETERS and str(cmd[1]) in ("-c", "-lc"):
        return str(cmd[0])
    return None


def _noexec_parse(interp: str, body: str) -> tuple[int, str]:
    """Run ``{interp} -n -c body`` side-effect-free; timeouts pass through."""
    try:
        proc = subprocess.run(
            [interp, "-n", "-c", body],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        return proc.returncode, (proc.stderr or "").strip()
    except (OSError, subprocess.TimeoutExpired):
        return 0, ""


def preflight_argv(cmd: list[str]) -> tuple[bool, str]:
    """M1+M2 pre-exec audit for run_command argv. Returns (healthy, message)."""
    argv = [str(t) for t in cmd]
    findings = _suspect_argv_findings(argv)
    interp = _should_parse_body(argv)
    if interp is not None:
        parse_rc, diag = _noexec_parse(interp, argv[2])
        if parse_rc != 0 and diag:
            findings.append(
                f"the {interp} -c body fails the no-exec pre-parse (nothing ran): "
                f"{diag.strip()}. Fix the quoting before rerunning — common causes: "
                "unescaped parentheses, bash-only syntax like <(cmd) under sh, "
                "an unterminated quote."
            )
    if findings:
        return False, "\n".join(findings)
    return True, ""
