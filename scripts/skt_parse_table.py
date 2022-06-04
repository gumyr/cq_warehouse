import sys


def list_splitz(base_list: list, seperator: str) -> list:
    """Split list by value

    Split list into sublists based on string value

    Args:
        baseList (list(str)): list to split
        seperator (str): separator string

    Yields:
        list(list(str)): separated lists
    """
    group = []
    for x in base_list:
        if x != seperator:
            group.append(x)
        elif group:
            yield group
            group = []


def divide_chunks(base_list: list, chunk_size: int) -> list:
    """Divide list is fixed sized chunks"""
    for i in range(0, len(base_list), chunk_size):
        yield base_list[i : i + chunk_size]


def transpose(m):
    """Transpose list of list"""
    return [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]


# Read input parameter as raw data file
with open(sys.argv[1]) as raw_file:
    # raw_table = raw_file.read().splitlines()
    raw_table = raw_file.readlines()

# Use blank lines as indictors of where to split the raw table
sectioned_table = list(list_splitz(raw_table, "\n"))

#
ordered_table = []
for sub_table in sectioned_table:
    for i in range(1, len(sub_table)):
        if sub_table[0] != sub_table[i]:
            row_count = i
            break
    if len(sub_table) % row_count != 0:
        raise RuntimeError(
            f"Invalid sub_table {sub_table} - {len(sub_table)=},{row_count=}"
        )
    try:
        ordered_table.extend(transpose(list(divide_chunks(sub_table, row_count))))
    except:
        print(f"Error - {sub_table=},{i=}")

output_table = []
for line in ordered_table:
    for i in range(len(line)):
        line[i] = line[i][:-1]
    size = f"M{line[0]}-{line[1]}-{line[2]},"
    output_table.append(size + ",".join(line))

for line in output_table:
    print(line)
