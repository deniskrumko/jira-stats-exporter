import re
from html import escape

import nh3
from jira2markdown import convert
from linkify_it import LinkifyIt
from linkify_it.main import Match
from markdown_it import MarkdownIt

ATTACHMENT_PATTERN = re.compile(r"\[\^([^\]\r\n]+)\]|!([^!\r\n|]+)(?:\|[^!\r\n]*)?!")
BRACED_MONOSPACE_PATTERN = re.compile(r"\{\{\{\}(.+?)\{\}\}\}")
LIST_ITEM_PATTERN = re.compile(r"([#*]+)\s")
ATTACHMENT_TOKEN = "JIRAREPORTATTACHMENTTOKEN{}END"


class HTTPSLinkifyIt(LinkifyIt):
    """Detect implicit links with HTTPS as the default web scheme."""

    def normalize(self, match: Match) -> None:
        """Normalize implicit web links to HTTPS and email links to mailto URLs."""
        if not match.schema:
            match.url = f"https://{match.url}"
        elif match.schema == "mailto:" and not match.url.lower().startswith("mailto:"):
            match.url = f"mailto:{match.url}"


MARKDOWN_RENDERER = MarkdownIt("gfm-like", {"html": True, "linkify": True})
MARKDOWN_RENDERER.linkify = HTTPSLinkifyIt()
HTML_CLEANER = nh3.Cleaner(
    tags={
        "a",
        "blockquote",
        "br",
        "code",
        "del",
        "em",
        "font",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "li",
        "ol",
        "p",
        "pre",
        "q",
        "s",
        "span",
        "strong",
        "sub",
        "sup",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
    },
    clean_content_tags={"embed", "iframe", "math", "object", "script", "style", "svg", "template"},
    attributes={
        "a": {"href", "title"},
        "code": {"class"},
        "font": {"color"},
    },
    allowed_classes={
        "a": {"attachment"},
        "span": {"attachment"},
    },
    set_tag_attribute_values={"a": {"target": "_blank"}},
    url_schemes={"http", "https", "mailto"},
    url_relative="deny",
)


def render_jira_markup(description: str | None, issue_url: str | None = None) -> str:
    """Render Jira wiki markup as sanitized HTML."""
    if not description:
        return "—"

    normalized = _normalize_markup(description)
    markup, attachments = _extract_attachments(normalized)
    rendered = MARKDOWN_RENDERER.render(convert(markup))
    rendered = _restore_attachments(rendered, attachments, issue_url)
    return HTML_CLEANER.clean(rendered)


def _normalize_markup(markup: str) -> str:
    """Normalize Jira markup variants emitted by the configured instance."""
    normalized = markup.replace("{*}", "*")
    normalized = BRACED_MONOSPACE_PATTERN.sub(r"{{\1}}", normalized)

    lines = []
    in_ordered_list = False
    for line in normalized.splitlines():
        stripped = line.lstrip()
        item_match = LIST_ITEM_PATTERN.match(stripped)
        if item_match is None:
            in_ordered_list = False
        else:
            markers = item_match.group(1)
            if markers.startswith("#"):
                in_ordered_list = True
            elif in_ordered_list and markers == "**":
                indentation = line[: len(line) - len(stripped)]
                line = f"{indentation}#*{stripped[2:]}"
        lines.append(line)
    return "\n".join(lines)


def _extract_attachments(markup: str) -> tuple[str, list[str]]:
    """Replace attachment markup with stable renderer placeholders."""
    attachments: list[str] = []

    def replace_attachment(match: re.Match[str]) -> str:
        """Record an attachment name and return its placeholder."""
        filename = match.group(1) or match.group(2)
        attachments.append(filename.strip())
        return ATTACHMENT_TOKEN.format(len(attachments) - 1)

    return ATTACHMENT_PATTERN.sub(replace_attachment, markup), attachments


def _restore_attachments(
    rendered: str,
    attachments: list[str],
    issue_url: str | None,
) -> str:
    """Restore attachment placeholders as safe issue links or labels."""
    for index, filename in enumerate(attachments):
        label = f"📎 {escape(filename)}"
        if issue_url:
            attachment = f'<a class="attachment" href="{escape(issue_url, quote=True)}">{label}</a>'
        else:
            attachment = f'<span class="attachment">{label}</span>'
        rendered = rendered.replace(ATTACHMENT_TOKEN.format(index), attachment)
    return rendered
