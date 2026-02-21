# Hazel Rule for Slack Export Cleanup

## Overview
Automatically process Slack exports when you save them to `/Users/degilber/Triage/slack_exports/`

## Hazel Rule Setup

**Rule Name:** Process Slack Exports

**Folder:** `/Users/degilber/Triage/slack_exports/`

### Conditions
- Extension is `txt`
- Date Added is after Date Last Matched

### Actions

#### 1. Run Shell Script (Embedded)

```bash
#!/bin/bash

# Get the input file from Hazel
input_file="$1"

# Prompt for metadata
conversation_type=$(osascript -e 'tell application "System Events"
    set typeChoice to choose from list {"channel", "dm"} with prompt "Conversation Type:" default items {"channel"}
    if typeChoice is false then return ""
    return item 1 of typeChoice
end tell')

# Exit if user cancelled
if [ -z "$conversation_type" ]; then
    exit 0
fi

# If channel, ask for channel name
channel_name=""
if [ "$conversation_type" = "channel" ]; then
    channel_name=$(osascript -e 'tell application "System Events"
        set channelInput to text returned of (display dialog "Channel name (optional):" default answer "")
        return channelInput
    end tell')
fi

# Ask for subject
subject=$(osascript -e 'tell application "System Events"
    set subjectInput to text returned of (display dialog "Subject/Title:" default answer "")
    return subjectInput
end tell')

# Build command
cmd="python3 /Users/degilber/dev_projects/tools/slack_export_cleanup/slack_cleanup.py"
cmd="$cmd \"$input_file\""
cmd="$cmd --type $conversation_type"

if [ -n "$channel_name" ]; then
    cmd="$cmd --channel \"$channel_name\""
fi

if [ -n "$subject" ]; then
    cmd="$cmd --subject \"$subject\""
fi

cmd="$cmd --output"

# Run the cleanup script
eval $cmd
```

#### 2. Move File (after script completes)
- Move `$1` to subfolder `processed`
- Creates subfolder if needed

## How It Works

1. You save a Slack export as `.txt` in `/Users/degilber/Triage/slack_exports/`
2. Hazel detects the new file
3. Dialog pops up asking:
   - Type: channel or dm?
   - Channel name (if channel)
   - Subject/title
4. Script runs and creates the `.md` file in the same directory
5. Original `.txt` moves to `processed/` subfolder

## Example Usage

**Save file:** `jet-discussion.txt`

**Hazel prompts:**
- Type: `channel`
- Channel name: `jet-help`
- Subject: `JET library access options and CDN security`

**Creates:** `2026-02-14-slack-convo-from-jet-help.md`

**Moves:** `jet-discussion.txt` → `processed/jet-discussion.txt`

## Manual Override

If you want to skip Hazel and run manually:

```bash
cd /Users/degilber/Triage/slack_exports
python3 /Users/degilber/dev_projects/tools/slack_export_cleanup/slack_cleanup.py myfile.txt --type channel --channel "jet-help" --subject "My Subject" --output
```

## Notes

- Leave channel name blank for DMs (just hit enter)
- Leave subject blank if you want to fill it in later
- The `.md` file appears in the same directory as the `.txt`
- You can then move the `.md` to your Obsidian vault or wherever
