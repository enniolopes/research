# Working on the Research plugin

This repository ships instructions and a Python standard-library runtime. Research project data and `.research/` state belong in the user's project, not here.

Start with [runtime ownership and verification](docs/architecture.md). Follow the existing scientific scope and public entry point in `skills/scientific-method/SKILL.md`; do not introduce engineering process into the research user's ordinary interaction.

For a behavioral fix, reproduce the defect before changing the implementation. Keep independent evidence, candidate admission, committed history, current applicability and scientific adequacy distinct. Preserve the existing public scripts, optional project formats and truthful host capability limits. Never fabricate review, authority or exposure provenance to clear a check.

Run the focused test first, then the existing CI commands:

```sh
python -m unittest discover -s tests -v
python -m py_compile skills/research-map/scripts/*.py skills/research-graph/scripts/*.py
python -m json.tool .claude-plugin/plugin.json
python -m json.tool .claude-plugin/marketplace.json
```

Schema exports must agree with `contracts.schema_files()`; edit the runtime definition before regenerating. Keep shared procedure in its owning reference and route skills/phases to it. The instruction-path and low-level dependency tests protect that boundary. A passing runtime test proves its stated mechanical contract, not improved scientific outcomes or native host enforcement.
