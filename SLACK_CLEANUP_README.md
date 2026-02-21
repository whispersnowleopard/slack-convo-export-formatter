# Slack Thread Cleanup

Python script to convert messy Slack copy-paste exports into clean, readable markdown with frontmatter and auto-generated filenames.

## Usage

```bash
# Basic usage - output to stdout
python3 slack_cleanup.py < slack_thread.txt > cleaned.md

# Auto-generate filename and write directly to file
python3 slack_cleanup.py slack_thread.txt --output

# Specify channel name (used in filename and frontmatter)
python3 slack_cleanup.py slack_thread.txt --channel "jet-help" --output
# Creates: 2026-02-13-slack-convo-from-jet-help.md

# Mark as DM conversation
python3 slack_cleanup.py slack_thread.txt --type dm --output
# Creates: 2026-02-13-slack-convo-with-albert-jones-dave-gilbert.md

# Fix "Unknown" authors (when Slack cuts off the first name)
python3 slack_cleanup.py slack_thread.txt --unknown "Michal K." --channel "jet-help" --output

# Skip frontmatter (if you don't want it)
python3 slack_cleanup.py slack_thread.txt --no-frontmatter > cleaned.md
```

## Filename Generation

When you use `--output` flag, the script auto-generates descriptive filenames:

**For channels:**
- `2026-02-13-slack-convo-from-jet-help.md` (when you provide `--channel`)
- `2026-02-13-slack-convo-albert-jones-dave-gilbert.md` (if no channel name)

**For DMs:**
- `2026-02-13-slack-convo-with-albert-jones-dave-gilbert.md` (2-3 people)
- `2026-02-13-slack-convo-group-dm.md` (4+ people)

## What it does

- **Parses two Slack formats**: 
  - `Name  [Timestamp]` (standard)
  - `[Timestamp]` alone (continuation messages)
- **Adds YAML frontmatter** with participants, date, message count, mini-bio placeholders
- **Auto-generates descriptive filenames** based on participants or channel name
- **Bold names, italic timestamps** for skimability
- **Blank lines between messages** for readability
- **Handles multi-line messages** properly

## Frontmatter with Mini-Bios

The script creates placeholder fields that you fill in manually:

```yaml
---
subject: Oracle JET Customization Support Discussion
source: Slack
type: channel
channel: jet-help
when: 2026-02-13
context: Discussion about whether JET can be used in NetSuite customizations and timeline for official support

participants:
  - name: Albert Jones
    title: Director, Software Development
    profile_url: https://people.oracle.com/apex/f?p=8000:PERSON:504878823796828::::PERSON:ajones
  - name: Dave Gilbert
    title: Partner Performance Manager
    profile_url: https://people.oracle.com/apex/f?p=8000:PERSON:504878823796828::::PERSON:dgilbert
  - name: Michal K.
    title: Senior Developer, JET Team
    profile_url: 
---
```

**Fields to fill in:**
- `subject:` Thread topic/summary
- `context:` Why this conversation matters, what decisions were made
- `participants:` Each person's title and Oracle People URL

## The "Unknown" problem

When you copy mid-thread, Slack sometimes omits the first author's name (just shows timestamps). The script marks these as "Unknown" by default.

**Fix it:**
1. Look at the Slack thread to see who those messages belong to
2. Re-run with `--unknown "Person Name"`
3. Or just manually edit the markdown afterward

## Integration ideas

Since you're into automation:

- **Hazel rule**: Auto-process any .txt file in a "Slack Exports" folder
- **Alfred workflow**: Select text, trigger script, paste cleaned version
- **Add to Obsidian**: Include in your vault with auto-tags
- **Bash alias**: `alias slack-clean='python3 ~/slack_cleanup.py'`
