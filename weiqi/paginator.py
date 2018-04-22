import math


def paginate(query, limit, page=1):
    total_results = query.count()
    total_pages = max(1, math.ceil(total_results / limit))
    page = max(1, page)
    page = min(total_pages, page)

    return {
        'query': query.limit(limit).offset((page-1)*limit),
        'page': page,
        'total_pages': total_pages,
        'total_results': total_results
    }
