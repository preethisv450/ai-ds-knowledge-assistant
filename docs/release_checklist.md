# Release Checklist — D20

## Rehearse (do this twice)

- [ ] Run docs/demo_script.md end to end with a timer. Target 5:00, hard stop 5:30.
- [ ] Second run with the team watching, interrupting with the questions they
      expect examiners to ask.
- [ ] Agree who drives the laptop and who speaks. Driving and talking at once
      is how demos run long.
- [ ] Whoever drives: practise the clicks until you don't read the script.

## Test on a second device

- [ ] On a phone, open the laptop's network URL that Streamlit prints on start,
      the one that isn't localhost. Both devices on the same Wi-Fi.
- [ ] Bottom nav: all five labels readable, nothing wrapping mid-word.
- [ ] Chat input sits above the nav, never under it.
- [ ] Module Assistant: the curriculum panel stacks above the tabs.
- [ ] Knowledge Network: zoom buttons reachable, graph legible after Fit.
- [ ] On a second laptop or browser, confirm a fresh session starts clean.

## Pre-demo state

- [ ] pip install -r requirements.txt on the demo machine, fresh.
- [ ] python scripts/build_index.py completes.
- [ ] python scripts/check_concepts.py reports no problems.
- [ ] pytest passes.
- [ ] .env present with a working key, and quota checked the morning of.
- [ ] Walk every question in the demo script once and confirm each returns a
      good answer. Replace any that don't.
- [ ] Browser zoom set so the back row can read it. Close other tabs.
- [ ] Laptop on power, notifications off, screen sleep disabled.

## Submission package

- [ ] All feature branches merged into main; nothing left unmerged.
- [ ] git status clean.
- [ ] README accurate: no feature claimed that isn't built.
- [ ] user_guide.md, demo_script.md and the slides present in docs.
- [ ] usability_findings.md filled in with real session notes.
- [ ] Tag the submitted state so it can be found later.
