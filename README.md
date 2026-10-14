# Research

A Claude Code plugin for carrying an empirical study from question to manuscript with explicit scientific commitments, traceable results and separate-context review. Its current focus is observational quantitative research, especially administrative data.

## Start a study

You need Claude Code, Git and Python 3.10+. Work in a Git repository for **your study**, separate from this plugin's source repository. For a new study, run in a terminal:

```sh
mkdir my-study
cd my-study
git init
```

Open Claude Code in that directory. Add the marketplace and install Research once:

```text
/plugin marketplace add enniolopes/research
/plugin install research@research
```

Complete the install dialog; choose user scope to use Research across your study repositories. If the install requests a reload, run `/reload-plugins`. Check that `/research:scientific-method` appears when you type `/`.

Start with your own question. For example:

```text
/research:scientific-method start Is travel time to school associated with absenteeism?
```

Then talk normally:

```text
Explore alternative explanations.
Check whether the data can answer this question.
Plan the analysis before running it.
Investigate this unexpected result.
Write the results section from the evidence.
Review the paper before submission.
```

`scientific-method` coordinates the internal skills, validators and reviewer. You do not need to invoke each component manually. Explorer is already included.

## Continue or review

Open Claude Code in the same study repository. Use:

| What you want | Command |
|---|---|
| Continue the work | `/research:scientific-method` |
| See the current conclusion, blockers and next action | `/research:scientific-method status` |
| Review a manuscript | `/research:scientific-method review documents/paper.md` |

Replace the manuscript path with your file. Third-party or historical papers can also be reviewed without inventing a new protocol or execution history.

## What to expect

Research guides the agent to establish the question before choosing an analysis, record confirmatory choices before seeing their results, and write claims from inspected sources or executed evidence. New ideas remain open to exploration; a result-driven change is recorded rather than silently presented as confirmation.

The agent keeps progress and the next action in `RESEARCH.map`; plans, decisions, results and reviews remain inspectable in your study repository. At consequential steps, missing evidence, review or human authority is made explicit. A useful outcome may be a narrower conclusion, an inconclusive result or a decision not to pursue the original question.

The plugin supplies instructions and mechanical checks. It does not guarantee that every host action is intercepted, authenticate reviewer expertise, or establish scientific truth from a validator `PASS`. Prior exposure outside Git history must be disclosed; execution checks do not provide network or model isolation.

## Optional controls

For versioned quality criteria, claim adoption/revision and checks over the actual release package, opt into the experimental [decision supervisor](skills/research-map/reference/supervision.md). Its guide covers setup, commands, recovery and current limits. Native host interception and scientific efficacy remain unverified.

For manual validation or computational replay, see the [research-map guide](skills/research-map/SKILL.md). The agent normally invokes these tools when needed.

If you want only Explorer, add the marketplace above and install `explorer@research` instead of `research@research`.

## Develop the plugin

The runtime uses the Python standard library. From a checkout of **this repository**, run:

```sh
python -m unittest discover -s tests -v
```

Start with [AGENTS.md](AGENTS.md) for maintenance constraints and verification commands, and [architecture](docs/architecture.md) for ownership and change boundaries. The [runtime CLI](skills/research-map/scripts/research.py) is the code entry point; [CI](.github/workflows/test.yml) runs compilation, regression tests and metadata checks on Python 3.10 and 3.12.

License: [CC BY-NC 4.0](LICENSE).
