"""Source component boundary and source-first eligibility for a one-work panel."""


def components(posts):
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    for post in posts:
        works = post['works']
        if not works:
            raise ValueError('Every inventory post must retain its source nomination')
        for x in works:
            parent[find(x)] = find(works[0])
    groups = {}
    for x in sorted(parent):
        groups.setdefault(find(x), []).append(x)
    return sorted(groups.values())


def unused_components(posts, historical_groups, aliases):
    exposed = set(historical_groups)
    for group in historical_groups:
        exposed.update(aliases.get(group, []))
    return [g for g in components(posts) if not exposed.intersection(g)]


def eligibility(*, component_novel, source_prose, authority_verified,
                edition_verified, extraction_reviewed, source_scope_matches,
                fl_opening_available, correspondence_reviewed):
    values = locals()
    if not all(type(v) is bool for v in values.values()):
        raise ValueError('Require explicit evidence booleans')
    return {'eligible':all(values.values()), 'requirements':values,
            'unmet':[k for k,v in values.items() if not v]}
