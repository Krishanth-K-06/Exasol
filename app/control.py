from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ControlDecision:
    allowed: bool
    reason: str
    risk: str


class SQLValidator:
    forbidden = re.compile(r"\b(drop|truncate|alter|grant|revoke|create|comment)\b", re.I)
    mutation = re.compile(r"\b(insert|update|delete|merge)\b", re.I)
    dangerous_comment = re.compile(r"(--|/\*|\*/)")

    def validate(self, sql: str, allowed_tables: set[str], sandbox: bool = True) -> ControlDecision:
        normalized = sql.strip()
        if not normalized or normalized.count(";") > 1:
            return ControlDecision(False, "Empty or multiple SQL statements are forbidden", "HIGH")
        if self.dangerous_comment.search(normalized) or self.forbidden.search(normalized):
            return ControlDecision(False, "DDL, privilege changes, and SQL comments are forbidden", "CRITICAL")
        tables = {match.lower() for match in re.findall(r"\b(?:from|join|update|into)\s+([a-zA-Z_][\w.]*)", normalized, re.I)}
        allowed = {item.lower() for item in allowed_tables}
        if any(
            table.split(".")[-1] not in allowed
            and not any(table.split(".")[-1].startswith(f"{item}_") for item in allowed)
            for table in tables
        ):
            return ControlDecision(False, "Statement references a table outside the allowlist", "HIGH")
        if self.mutation.search(normalized) and not sandbox:
            return ControlDecision(False, "Production mutations require verified sandbox output and approval", "HIGH")
        if re.search(r"\b(update|delete)\b", normalized, re.I) and not re.search(r"\bwhere\b", normalized, re.I):
            return ControlDecision(False, "UPDATE and DELETE require a WHERE clause", "CRITICAL")
        return ControlDecision(True, "SQL passed deterministic policy checks", "LOW")


class PolicyEngine:
    def authorize(self, *, risk_level: str, sandbox_passed: bool, human_approved: bool = False) -> ControlDecision:
        if not sandbox_passed:
            return ControlDecision(False, "Sandbox verification must pass before deployment", "HIGH")
        if risk_level in {"HIGH", "CRITICAL"} and not human_approved:
            return ControlDecision(False, "Human approval is required for high-risk deployment", risk_level)
        return ControlDecision(True, "Deployment authorized by policy", risk_level)
