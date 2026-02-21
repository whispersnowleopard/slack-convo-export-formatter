# Slack Export Cleanup - Quick Start

## Setup

1. Put script here: `/Users/degilber/dev_projects/tools/slack_export_cleanup/slack_cleanup.py`

2. Make it executable:
```bash
chmod +x /Users/degilber/dev_projects/tools/slack_export_cleanup/slack_cleanup.py
```

3. Add alias to `~/.zshrc`:
```bash
echo 'alias slack-clean="python3 /Users/degilber/dev_projects/tools/slack_export_cleanup/slack_cleanup.py"' >> ~/.zshrc
source ~/.zshrc
```

## Daily Workflow

### Save Slack Thread
1. Copy the entire Slack conversation (just copy, don't add any headers yourself!)
2. Paste into a `.txt` file in `/Users/degilber/Triage/slack_exports/`
3. Name it something descriptive like `jet-help-discussion.txt`

### Clean It Up
```bash
cd /Users/degilber/Triage/slack_exports

# For DM conversations
slack-clean your-file.txt --type dm --output

# For channel conversations
slack-clean your-file.txt --channel "jet-help" --output
```

### Fill in Details
1. Open the generated `.md` file
2. Fill in the frontmatter fields:
   - `subject:` What was discussed
   - `context:` Why it matters, decisions made
   - `participants:` Add titles and Oracle People URLs

3. Move the `.md` file to wherever you store these (Obsidian vault?)

4. Delete the original `.txt` file

## The Script Handles

- Skips profile headers and system messages
- Handles continuation timestamps (like "1:37" without AM/PM)
- Auto-generates descriptive filenames
- Creates proper YAML frontmatter with participant placeholders
- Formats messages with bold names, italic timestamps, blank lines

## Don't Do

- ❌ Don't manually add frontmatter to the `.txt` file before running the script
- ❌ Don't edit the raw Slack export - just copy/paste it as-is
- ✅ Just paste the raw Slack text and let the script do its thing
