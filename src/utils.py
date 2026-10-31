def dedupe_preserve_order(items):
    """Remove duplicates while keeping first-seen order (unlike set())."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
