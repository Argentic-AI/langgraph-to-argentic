"""Print the prompt size of each model call as a small chart. The scale is fixed, so two runs compare."""

PER_MARK = 100  # tokens per #


def show(label: str, sizes: list[int], per: str = "model call") -> None:
    if not sizes:
        print(f"{label}: the provider reported no prompt sizes")
        return
    top = max(sizes)
    print(f"\n{label}: prompt tokens per {per} ({len(sizes)} rows, one # = {PER_MARK} tokens)")
    # at most ~25 rows: sample evenly, always keep the first and the last
    rows = sorted({round(i * (len(sizes) - 1) / 24) for i in range(25)}) if len(sizes) > 25 else range(len(sizes))
    for i in rows:
        marks = max(1, round(sizes[i] / PER_MARK))
        bar = "#" * marks if marks <= 60 else "#" * 60 + ">"
        print(f"  {i + 1:>3}  {sizes[i]:>6}  {bar}")
    print(f"  first {sizes[0]}, last {sizes[-1]}, largest {top}")
