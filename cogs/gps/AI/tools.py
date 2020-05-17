def flatten(data, depth=None):
    if depth is None:
        depth = 0
    ret = []
    for i, item in enumerate(data):
        if type(item) is list:
            d = flatten(item, depth=depth+1)
            for thing in d:
                ret.append(thing)
        else:
            ret.append(item)
    return(ret)
