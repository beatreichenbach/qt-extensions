import re


def title(text):
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text).replace('_', ' ').title()
    return text


def unique_name(name, existing_names):
    for existing_name in existing_names:
        if name.lower() == existing_name.lower():
            match = re.search(r'(.*?)(\d+)$', name)
            if match:
                number = int(match.group(2))
                name = match.group(1)
            else:
                number = 0
            name = f'{name}{number + 1}'
            return unique_name(name, existing_names)
    return name
