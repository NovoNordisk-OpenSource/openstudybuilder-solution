def path_join(*parts, separator="/"):
    if len(parts) == 0:
        result = ""
    else:
        result = parts[0]
        for p in parts[1:]:
            nbr_separators = int(result.endswith(separator)) + int(
                p.startswith(separator)
            )
            if nbr_separators == 0:
                result = result + separator + p
            elif nbr_separators == 1:
                result = result + p
            else:
                result = result + p[1:]
    return result
