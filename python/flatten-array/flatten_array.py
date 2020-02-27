def flatten(iterable):
    flat = []
    for item in iterable:
        if isinstance(item, list):
            flat.extend(flatten(item))
        elif item is not None:
            flat.append(item)
    return flat
