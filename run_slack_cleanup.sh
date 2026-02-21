#!/bin/bash

# Get the input file
input_file="$1"

# Show dialog - force to foreground
conv_type=$(osascript 2>/dev/null <<EOF
tell application "Finder"
    activate
end tell
tell application "System Events"
    set typeChoice to choose from list {"channel", "dm"} with prompt "Conversation Type:" default items {"channel"} with title "Slack Export"
    if typeChoice is false then return ""
    return item 1 of typeChoice
end tell
EOF
)

# Exit if user cancelled
if [ -z "$conv_type" ]; then
    echo "User cancelled"
    exit 0
fi

# Channel name (only if channel)
channel_name=""
if [ "$conv_type" = "channel" ]; then
    channel_name=$(osascript 2>/dev/null <<EOF
tell application "Finder"
    activate
end tell
tell application "System Events"
    set channelInput to text returned of (display dialog "Channel name (optional):" default answer "" with title "Slack Export")
    return channelInput
end tell
EOF
)
fi

# Subject
subject=$(osascript 2>/dev/null <<EOF
tell application "Finder"
    activate
end tell
tell application "System Events"
    set subjectInput to text returned of (display dialog "Subject/Title:" default answer "" with title "Slack Export")
    return subjectInput
end tell
EOF
)

# Build command
cmd="python3 /Users/degilber/dev_projects/tools/slack_export_cleanup/slack_cleanup.py"
cmd="$cmd \"$input_file\""
cmd="$cmd --type $conv_type"

if [ -n "$channel_name" ]; then
    cmd="$cmd --channel \"$channel_name\""
fi

if [ -n "$subject" ]; then
    cmd="$cmd --subject \"$subject\""
fi

cmd="$cmd --output"

# Run it
echo "Running: $cmd"
eval $cmd