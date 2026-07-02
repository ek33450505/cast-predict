#!/usr/bin/env python3
"""cast-predict.py — telemetry-driven dispatch prediction over cast.db (read-only).

Reads cast.db to predict a task's likely cost, suggest agents, and surface related
incidents from prior sessions. Strictly read-only — never writes.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.parse
from pathlib import Path
from statistics import mean, median


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cast-predict",
        description="Predict a task's likely cost, agents, and related incidents from cast.db.",
    )
    parser.add_argument("task", help="Task description to predict")
    parser.add_argument("--limit", type=int, default=5, help="Max agents / incidents to show (default 5)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--db", metavar="PATH", default=None, help="Override cast.db path")
    args = parser.parse_args()

    db_path = args.db or os.environ.get("CAST_DB_PATH", str(Path.home() / ".claude" / "cast.db"))
    if not os.path.exists(db_path):
        print(f"cast-predict: cast.db not found at {db_path}", file=sys.stderr)
        return 1

    task = args.task
    limit_n = max(1, args.limit)  # clamp: LIMIT -1 means "no limit" in sqlite; keep the cap meaningful
    json_out = args.as_json

    try:
        # Quote the path so a filename containing URI-special chars (?, #) cannot
        # inject query params and subvert the read-only mode=ro guarantee.
        ro_uri = "file://" + urllib.parse.quote(os.path.abspath(db_path)) + "?mode=ro"
        conn = sqlite3.connect(ro_uri, uri=True, timeout=5)
    except sqlite3.OperationalError as e:
        print(f"cast-predict: cannot open cast.db: {e}", file=sys.stderr)
        return 1
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ─────────────────────────────────────────────────────────────────────────
    # ENGINE BODY — extracted verbatim from the flagship cast binary heredoc.
    # Starts at STOP = {...} (original line 1807). Header lines dropped (replaced
    # by argparse scaffold above). sys.exit(0) → return 0 in both output blocks.
    # Re-indented +4 spaces to live inside main().
    # ─────────────────────────────────────────────────────────────────────────

    STOP = {"the","and","for","with","this","that","from","into","you","your","are","was","its","but","not"}
    keywords = [w for w in re.findall(r'[a-z0-9]+', task.lower()) if len(w) >= 3 and w not in STOP]

    # ── Section 1: Cost prediction via routing_events keyword scoring ─────────────
    try:
        cur.execute("SELECT session_id, prompt_preview FROM routing_events WHERE prompt_preview IS NOT NULL AND prompt_preview != ''")
        re_rows = cur.fetchall()
    except sqlite3.Error:
        re_rows = []  # fake-success-ok: table may be absent in fresh installs — graceful degradation

    total_sessions_searched = 0
    session_scores = {}
    if keywords and re_rows:
        session_previews = {}
        for row in re_rows:
            sid = row["session_id"]
            if sid:
                session_previews.setdefault(sid, []).append((row["prompt_preview"] or "").lower())
        total_sessions_searched = len(session_previews)
        for sid, previews in session_previews.items():
            combined = " ".join(previews)
            score = sum(1 for kw in set(keywords) if kw in combined)
            if score > 0:
                session_scores[sid] = score

    matched_sids = list(session_scores.keys())

    cost_data = {"median": None, "mean": None, "min": None, "max": None, "count": 0}
    session_costs = []
    if matched_sids:
        placeholders = ",".join("?" * len(matched_sids))
        cur.execute(f"""
            SELECT ar.session_id, COALESCE(SUM(ar.cost_usd), 0) AS total_cost
            FROM agent_runs ar
            WHERE ar.session_id IN ({placeholders})
            GROUP BY ar.session_id
        """, matched_sids)
        for r in cur.fetchall():
            session_costs.append(r["total_cost"])
        if session_costs:
            cost_data["median"] = median(session_costs)
            cost_data["mean"]   = mean(session_costs)
            cost_data["min"]    = min(session_costs)
            cost_data["max"]    = max(session_costs)
            cost_data["count"]  = len(session_costs)

    # ── Section 2: Suggested agents ──────────────────────────────────────────────
    agent_rows = []
    if matched_sids:
        placeholders = ",".join("?" * len(matched_sids))
        cur.execute(f"""
            SELECT ar.agent,
                   COUNT(*) AS runs,
                   COALESCE(AVG(ar.cost_usd), 0) AS avg_cost,
                   SUM(CASE WHEN ar.status='DONE' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS success_rate
            FROM agent_runs ar
            WHERE ar.session_id IN ({placeholders})
              AND ar.agent IS NOT NULL
            GROUP BY ar.agent
            ORDER BY runs DESC
            LIMIT ?
        """, matched_sids + [limit_n])
        agent_rows = [{"agent": r["agent"], "runs": r["runs"], "avg_cost": r["avg_cost"], "success_rate": r["success_rate"]} for r in cur.fetchall()]

    # dispatch_decisions signal (may be absent/empty — PRAGMA-guard)
    dd_rows = []
    try:
        cur.execute("PRAGMA table_info(dispatch_decisions)")
        dd_cols = {row["name"] for row in cur.fetchall()}
        if dd_cols and keywords:
            conditions = " OR ".join(["prompt_snippet LIKE ?" for _ in keywords])
            params = [f"%{kw}%" for kw in keywords]
            cur.execute(f"""
                SELECT chosen_agent, outcome, COUNT(*) AS cnt
                FROM dispatch_decisions
                WHERE {conditions}
                GROUP BY chosen_agent, outcome
                ORDER BY cnt DESC
                LIMIT ?
            """, params + [limit_n])
            dd_rows = [{"chosen_agent": r["chosen_agent"], "outcome": r["outcome"], "cnt": r["cnt"]} for r in cur.fetchall()]
    except sqlite3.Error:
        dd_rows = []  # fake-success-ok: dispatch_decisions table may be absent — graceful degradation

    # ── Section 3: Related incidents ──────────────────────────────────────────────
    incident_rows = []
    try:
        cur.execute("PRAGMA table_info(incidents)")
        inc_cols = {row["name"] for row in cur.fetchall()}
        if inc_cols and keywords:
            conditions = " OR ".join(
                ["(problem_summary LIKE ? OR COALESCE(fix_summary,'') LIKE ?)" for _ in keywords]
            )
            params = []
            for kw in keywords:
                params += [f"%{kw}%", f"%{kw}%"]
            cur.execute(f"""
                SELECT problem_summary, fix_summary, related_commit
                FROM incidents
                WHERE {conditions}
                LIMIT ?
            """, params + [limit_n])
            incident_rows = [
                {"problem_summary": r["problem_summary"], "fix_summary": r["fix_summary"], "related_commit": r["related_commit"]}
                for r in cur.fetchall()
            ]
    except sqlite3.Error:
        incident_rows = []  # fake-success-ok: incidents table may be absent — graceful degradation

    conn.close()

    # ── JSON output ───────────────────────────────────────────────────────────────
    if json_out:
        out = {
            "task": task,
            "keywords": keywords,
            "sessions_searched": total_sessions_searched,
            "matched_sessions": len(matched_sids),
            "cost_prediction": {
                "median_usd":   round(cost_data["median"], 4) if cost_data["median"] is not None else None,
                "mean_usd":     round(cost_data["mean"],   4) if cost_data["mean"]   is not None else None,
                "min_usd":      round(cost_data["min"],    4) if cost_data["min"]    is not None else None,
                "max_usd":      round(cost_data["max"],    4) if cost_data["max"]    is not None else None,
                "sample_count": cost_data["count"],
            },
            "suggested_agents": agent_rows,
            "dispatch_decision_signal": dd_rows,
            "related_incidents": incident_rows,
        }
        print(json.dumps(out, indent=2))
        return 0

    # ── Formatted output ──────────────────────────────────────────────────────────
    print(f"predict: {task!r}")
    print(f"Keywords: {', '.join(keywords) if keywords else '(none extracted)'}")
    print()

    print("── Cost Prediction ──────────────────────────────────────────────────────")
    if not keywords:
        print("No usable keywords extracted from task description — cannot predict.")
    elif cost_data["count"] == 0:
        print(f"No similar tasks found in the record ({total_sessions_searched} sessions searched) — cannot predict.")
    else:
        conf = " (low confidence — only {k} matched session{s})".format(
            k=cost_data["count"], s="" if cost_data["count"]==1 else "s"
        ) if cost_data["count"] < 3 else ""
        med = cost_data["median"]
        avg = cost_data["mean"]
        lo  = cost_data["min"]
        hi  = cost_data["max"]
        k   = cost_data["count"]
        print(f"Tasks like this: ≈ ${med:.4f} median  (mean ${avg:.4f}, range ${lo:.4f}–${hi:.4f}) over {k} similar session{'s' if k!=1 else ''}{conf}")
    print()

    print("── Suggested Agents ─────────────────────────────────────────────────────")
    if not agent_rows:
        if not matched_sids:
            print("  No similar sessions found — no agent suggestions.")
        else:
            print("  No agent run data for matched sessions.")
    else:
        for a in agent_rows:
            pct = round((a["success_rate"] or 0) * 100)
            print(f"  Suggested: {a['agent']:<22} ({a['runs']} run{'s' if a['runs']!=1 else ''} on similar tasks, {pct}% DONE, ≈${a['avg_cost']:.4f} avg)")
    if dd_rows:
        print()
        print("  Dispatch-decision signal:")
        for d in dd_rows:
            print(f"    {d['chosen_agent']} · outcome={d['outcome']} · {d['cnt']} match{'es' if d['cnt']!=1 else ''}")
    else:
        print("  (no dispatch-decision history yet)")
    print()

    print("── Related Incidents ────────────────────────────────────────────────────")
    if not incident_rows:
        print("  (no incident history yet)")
    else:
        for inc in incident_rows:
            prob   = (inc["problem_summary"] or "")[:80]
            fix    = (inc["fix_summary"] or "")[:80]
            commit = inc["related_commit"]
            commit_str = f"  [{commit[:8]}]" if commit else ""
            print(f"  {prob}{commit_str}")
            if fix:
                print(f"    → {fix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
