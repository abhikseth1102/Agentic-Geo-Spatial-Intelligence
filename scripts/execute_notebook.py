"""Execute the EDA notebook in order and capture real text/figure outputs."""

import ast
import base64
import contextlib
import io
import json
from pathlib import Path
import uuid
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
path = root / "notebooks/01_maritime_eda.ipynb"
doc = json.loads(path.read_text())
state = {
    "display": lambda value: print(
        value.to_string() if hasattr(value, "to_string") else value
    )
}
count = 0
for cell in doc["cells"]:
    cell["id"] = cell.get("id", uuid.uuid4().hex[:8])
    if cell["cell_type"] != "code":
        continue
    count += 1
    source = "".join(cell["source"])
    tree = ast.parse(source)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            tail = tree.body.pop()
            exec(compile(tree, "<notebook>", "exec"), state)
            value = eval(
                compile(ast.Expression(tail.value), "<notebook>", "eval"), state
            )
            if value is not None:
                state["display"](value)
        else:
            exec(compile(tree, "<notebook>", "exec"), state)
    cell["execution_count"] = count
    cell["outputs"] = []
    if output.getvalue():
        cell["outputs"].append(
            {
                "output_type": "stream",
                "name": "stdout",
                "text": output.getvalue().splitlines(True),
            }
        )
    for number in plt.get_fignums():
        buf = io.BytesIO()
        plt.figure(number).savefig(buf, format="png", dpi=140, bbox_inches="tight")
        cell["outputs"].append(
            {
                "output_type": "display_data",
                "data": {"image/png": base64.b64encode(buf.getvalue()).decode()},
                "metadata": {},
            }
        )
    plt.close("all")
path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
print(f"Executed {count} notebook cells successfully.")
