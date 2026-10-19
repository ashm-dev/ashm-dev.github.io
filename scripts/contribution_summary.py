"""Format contribution counts for the PDF without assuming a fixed section count."""


def summary(project, text):
    parts = []
    for section in project["sections"]:
        if not section["items"]:
            continue
        counts = []
        for state in ("done", "open"):
            count = sum(item["state"] == state for item in section["items"])
            if count:
                counts.append(f"{count} {text['states'][section['title']][state]}")
        parts.append(f"{text['sections'][section['title']]}: {', '.join(counts)}")
    return " · ".join(parts)
