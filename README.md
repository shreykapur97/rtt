# RTT — Rhino Teaching Tools

Small tools for teaching with Rhino 8 and Grasshopper. Each tool is a Rhino
command.

## Requirements

- Rhino 8 (the tools are Python 3 scripts)

## Install

1. In Rhino, run `PackageManager`.
2. Search for **RTT** and click **Install**.
3. Restart Rhino.

**Update:** Package Manager shows when a new version is out.
**Uninstall:** remove RTT in Package Manager and restart Rhino.

No Package Manager access? Download the `.yak` file from
[Releases](https://github.com/shreykapur97/RTT/releases) and drag it into
the Rhino window.

## Tools

### `Grader`

Steps through a folder of student submissions, opening each student's
`.3dm` and `.gh` together so you can grade them one after another.

1. Run `Grader` and pick the submissions folder.
2. **Match submissions.** Files are paired automatically when a folder holds
   one `.3dm` and one `.gh`, or when the names match. Pairs whose names are
   close show up as suggestions. Link the rest by hand, then **Confirm &
   Grade**. Unpaired files are still graded on their own.
3. **Grade.** A small window stays on top. Type a grade and notes, then move
   through students with **Prev / Next** or the dropdown. Each file opens
   from a temporary copy, so student files are never changed.
   Grasshopper's solver stays locked so heavy scripts don't run on open;
   click **Unlock solver** to run one.

Grades are saved as you go, into two files in the submissions folder:

- `grades.csv`: one row per student (grade, notes, files, how they were paired)
- `meta.json`: pairings and grades, so you can close and pick up later

## Adding a tool

Tools live in `commands/`, one `.py` file per command. Add the file to the
`RTT.rhproj` project in Rhino's ScriptEditor, raise the version, and publish.
