"""List structure checker — WCAG SC 1.3.1."""

from __future__ import annotations

import re

import panflute as pf

from altscribe.checks.base import BaseCheck, CheckResult, Severity

_BULLET_PATTERN = re.compile(r"^[\u2022\u2023\u25e6\u2043\u2219\u25cf\u25cb]\s+")
_ORDERED_PATTERN = re.compile(r"^(\d+)[.)]\s+")


class ListStructureCheck(BaseCheck):
    check_id = "list-structure"
    check_name = "List Structure"
    wcag_sc = "1.3.1"
    element_types = (pf.Para,)

    def __init__(self) -> None:
        super().__init__()
        self._candidates: list[tuple[pf.Para, str, str]] = []

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        assert isinstance(elem, pf.Para)
        text = pf.stringify(elem).strip()

        bullet_match = _BULLET_PATTERN.match(text)
        ordered_match = _ORDERED_PATTERN.match(text)

        if bullet_match:
            self._candidates.append((elem, "bullet", text[bullet_match.end() :]))
        elif ordered_match:
            self._candidates.append((elem, "ordered", text[ordered_match.end() :]))

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        groups = self._find_consecutive_groups()

        for group in groups:
            list_type = group[0][1]
            count = len(group)
            first_text = group[0][2][:40]
            kind = "bulleted" if list_type == "bullet" else "numbered"
            issue = self._add_issue(
                message=(
                    f"{count} consecutive paragraphs look like a "
                    f"{kind} list (starting with '{first_text}...')"
                ),
                location="Para sequence",
                severity=Severity.WARNING,
            )
            if fix:
                self._convert_to_list(group, issue)

        return self._make_result()

    def _find_consecutive_groups(
        self,
    ) -> list[list[tuple[pf.Para, str, str]]]:
        """Find runs of 2+ consecutive same-type fake list items."""
        if not self._candidates:
            return []

        groups: list[list[tuple[pf.Para, str, str]]] = []
        current_group: list[tuple[pf.Para, str, str]] = [self._candidates[0]]

        for i in range(1, len(self._candidates)):
            prev_para = self._candidates[i - 1][0]
            curr = self._candidates[i]
            curr_para, curr_type = curr[0], curr[1]
            prev_type = self._candidates[i - 1][1]

            if (
                curr_type == prev_type
                and prev_para.parent is curr_para.parent
                and self._are_adjacent(prev_para, curr_para)
            ):
                current_group.append(curr)
            else:
                if len(current_group) >= 2:
                    groups.append(current_group)
                current_group = [curr]

        if len(current_group) >= 2:
            groups.append(current_group)

        return groups

    @staticmethod
    def _are_adjacent(a: pf.Para, b: pf.Para) -> bool:
        """Check if two paragraphs are adjacent siblings."""
        parent = a.parent
        if parent is None or not hasattr(parent, "content"):
            return False
        found_a = False
        for child in parent.content:
            if child is a:
                found_a = True
                continue
            if found_a:
                return child is b
        return False

    @staticmethod
    def _convert_to_list(
        group: list[tuple[pf.Para, str, str]],
        issue,
    ) -> None:
        """Replace consecutive paragraphs with a proper List element."""
        list_type = group[0][1]
        items = []
        for _, _, clean_text in group:
            items.append(pf.ListItem(pf.Plain(pf.Str(clean_text))))

        if list_type == "bullet":
            new_list = pf.BulletList(*items)
        else:
            new_list = pf.OrderedList(*items)

        parent = group[0][0].parent
        if parent is None or not hasattr(parent, "content"):
            return

        first_idx = None
        indices_to_remove = []
        for i, child in enumerate(parent.content):
            for j, (para, _, _) in enumerate(group):
                if child is para:
                    if j == 0:
                        first_idx = i
                    else:
                        indices_to_remove.append(i)

        if first_idx is not None:
            parent.content[first_idx] = new_list
            for idx in sorted(indices_to_remove, reverse=True):
                del parent.content[idx]

        issue.fixed = True
        issue.fix_description = (
            f"Converted {len(group)} paragraphs to "
            f"{'BulletList' if list_type == 'bullet' else 'OrderedList'}"
        )
