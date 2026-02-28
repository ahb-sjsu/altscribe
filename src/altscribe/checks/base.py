"""Foundation types for the altscribe checker system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

import panflute as pf


class Severity(Enum):
    """Issue severity for reporting."""

    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    """A single accessibility issue found in the document."""

    check_id: str
    wcag_sc: str
    severity: Severity
    message: str
    location: str
    fixed: bool = False
    fix_description: str = ""


@dataclass
class CheckResult:
    """Aggregated result from a single checker."""

    check_id: str
    check_name: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def fixed_count(self) -> int:
        return sum(1 for i in self.issues if i.fixed)


@runtime_checkable
class Check(Protocol):
    """Protocol that all accessibility checkers implement."""

    check_id: str
    check_name: str
    wcag_sc: str
    element_types: tuple[type[pf.Element], ...]

    def check(self, elem: pf.Element, doc: pf.Doc) -> None: ...

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult: ...


class BaseCheck:
    """Base class providing common boilerplate for checkers."""

    check_id: str = ""
    check_name: str = ""
    wcag_sc: str = ""
    element_types: tuple[type[pf.Element], ...] = ()

    def __init__(self) -> None:
        self._issues: list[Issue] = []

    def _add_issue(
        self,
        message: str,
        location: str,
        severity: Severity = Severity.ERROR,
    ) -> Issue:
        issue = Issue(
            check_id=self.check_id,
            wcag_sc=self.wcag_sc,
            severity=severity,
            message=message,
            location=location,
        )
        self._issues.append(issue)
        return issue

    def _make_result(self) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            check_name=self.check_name,
            issues=self._issues,
        )

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        raise NotImplementedError

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        raise NotImplementedError
