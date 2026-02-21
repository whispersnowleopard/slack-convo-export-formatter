#!/usr/bin/env python3
"""
Clean up Slack thread exports into readable markdown.
Handles both timestamp formats and generates frontmatter.

Usage:
    python3 slack_cleanup.py < input.txt > output.md
    python3 slack_cleanup.py input.txt > output.md
    python3 slack_cleanup.py input.txt --type dm > output.md
    python3 slack_cleanup.py input.txt --unknown "Mike Smith" > output.md

Notes:
    - If messages start with just [timestamp], they're likely continuations
      from an author that was cut off in the copy. Use --unknown to specify.
    - Use --type to specify 'channel' or 'dm' (default: channel)

Supported formats:
    Format 1: Channel thread - "Name  [H:MM AM/PM]" then message on next line
    Format 2: DM with indented timestamp - Name on one line, indented timestamp next
    Format 3: Inline DM - "Name H:MM AM/PM Message" all on one line (e.g. copied from Slack app)
    Format 3b: Continuation - "H:MM Message" with no name (continues from last known author)
"""

import re
from datetime import datetime
from typing import List, Tuple
import sys
import argparse


def parse_slack_export(text: str, unknown_name: str = "Unknown") -> List[Tuple[str, str, str]]:
    """
    Parse Slack export text into (name, timestamp, message) tuples.
    Handles multiple Slack copy/paste formats:

    Format 1: Channel thread format
        Name  [Timestamp]
        Message content

    Format 2: DM format with indented timestamp
        Name
          H:MM AM/PM
        Message content

    Format 3: Inline DM format (everything on one line)
        Name H:MM AM/PM Message content

    Format 3b: Continuation timestamp (no name, continues from last author)
        H:MM Message content
    """
    messages = []
    lines = text.split('\n')
    i = 0

    # Skip header junk (Thread, channel name, "Saved for later", etc.)
    skip_patterns = ['Thread', 'Saved for later', 'replies']
    while i < len(lines):
        line = lines[i].strip()
        if any(pattern in line for pattern in skip_patterns) or not line:
            i += 1
            continue
        # Check if this might be a channel name line (short, no brackets)
        if line and '[' not in line and len(line.split()) <= 3:
            # Likely a channel name, skip it
            i += 1
            continue
        break

    # Skip any manually-added frontmatter
    frontmatter_keywords = ['subject:', 'participants:', 'context:', 'when:', 'source:', 'type:', 'channel:']
    while i < len(lines):
        line = lines[i].strip()
        if any(line.lower().startswith(kw) for kw in frontmatter_keywords) or not line:
            i += 1
            continue
        break

    current_author = unknown_name

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Skip Slack system messages
        if stripped.startswith('This conversation is') or stripped.startswith('Message '):
            i += 1
            continue

        # Skip URLs on their own line (profile links)
        if stripped.startswith('http'):
            i += 1
            continue

        # ----------------------------------------------------------------
        # Format 1: Channel thread format - Name  [Timestamp] on same line
        # Example: "Dave Gilbert  [4:23 PM]"
        # Sometimes has reply count prefix: "24 repliesJohn 'JB' Brock [JET, US-WEST]  [4:30 PM]"
        # ----------------------------------------------------------------
        match = re.match(r'^(.+?)\s{2,}\[(.+?)\]$', stripped)
        if match:
            name = match.group(1).strip()
            timestamp = match.group(2).strip()

            # Strip reply count prefix like "24 replies" from the name
            name = re.sub(r'^\d+\s+replies?', '', name).strip()

            current_author = name

            # Collect message until next name+timestamp line
            i += 1
            message_lines = []
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()

                # Skip empty lines
                if not next_stripped:
                    i += 1
                    continue

                # Stop if we hit another name+timestamp line
                if re.match(r'^(.+?)\s{2,}\[(.+?)\]$', next_stripped):
                    break

                # Skip URLs and system messages
                if next_stripped.startswith('http') or next_stripped.startswith('This conversation') or next_stripped.startswith('Message '):
                    i += 1
                    continue

                # Strip inline timestamps like "[4:31 PM]message content"
                cleaned_line = re.sub(r'^\[(\d{1,2}:\d{2}\s*[AP]M)\]', '', next_line.rstrip())

                if cleaned_line.strip():
                    message_lines.append(cleaned_line)
                i += 1

            message = '\n'.join(message_lines).strip()
            if message:
                messages.append((name, timestamp, message))
            continue

        # ----------------------------------------------------------------
        # Format 3: Inline DM - "Name H:MM AM/PM Message" all on one line
        # Example: "Dave Gilbert 1:54 PM Hello Sandhya!"
        # Must match before Format 2 checks since these lines are not indented.
        # ----------------------------------------------------------------
        match3 = re.match(
            r'^([A-Za-z]+(?: [A-Za-z]+)+?)\s+(\d{1,2}:\d{2}\s*[AP]M)\s+(.+)$',
            stripped
        )
        if match3:
            name = match3.group(1).strip()
            timestamp = match3.group(2).strip()
            message = match3.group(3).strip()
            current_author = name
            messages.append((name, timestamp, message))
            i += 1
            continue

        # ----------------------------------------------------------------
        # Format 3b: Continuation timestamp - "H:MM Message" (no author name)
        # Example: "2:13 in 26.1, existing dashboards will be iframed."
        # Attributed to current_author (last known speaker).
        # ----------------------------------------------------------------
        match3b = re.match(r'^(\d{1,2}:\d{2}(?:\s*[AP]M)?)\s+(.+)$', stripped)
        if match3b:
            timestamp = match3b.group(1).strip()
            message = match3b.group(2).strip()
            messages.append((current_author, timestamp, message))
            i += 1
            continue

        # ----------------------------------------------------------------
        # Format 2: DM format - Check if this is an indented timestamp (with AM/PM)
        # ----------------------------------------------------------------
        is_indented_timestamp = (line.startswith('  ') and ('AM' in stripped or 'PM' in stripped))
        is_continuation_timestamp = (not line.startswith(' ') and re.match(r'^\d{1,2}:\d{2}$', stripped))

        if is_indented_timestamp or is_continuation_timestamp:
            timestamp = stripped

            # Collect message until we hit next timestamp or name+timestamp combo
            i += 1
            message_lines = []
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()

                # Skip empty lines
                if not next_stripped:
                    i += 1
                    continue

                # Stop if we hit another indented timestamp
                if next_line.startswith('  ') and ('AM' in next_stripped or 'PM' in next_stripped):
                    break

                # Stop if we hit a continuation timestamp
                if not next_line.startswith(' ') and re.match(r'^\d{1,2}:\d{2}$', next_stripped):
                    break

                # Stop if we hit a name followed by a timestamp
                if not next_line.startswith(' ') and next_stripped and i + 1 < len(lines):
                    peek_line = lines[i + 1]
                    peek_stripped = peek_line.strip()
                    if peek_line.startswith('  ') and ('AM' in peek_stripped or 'PM' in peek_stripped):
                        break

                # Skip URLs and system messages
                if next_stripped.startswith('http') or next_stripped.startswith('This conversation') or next_stripped.startswith('Message '):
                    i += 1
                    continue

                message_lines.append(next_line.rstrip())
                i += 1

            message = '\n'.join(message_lines).strip()
            if message:
                messages.append((current_author, timestamp, message))
            continue

        # ----------------------------------------------------------------
        # Format 2 continued: Non-indented, non-empty line = probably a name
        # ----------------------------------------------------------------
        if not line.startswith(' ') and stripped:
            title_keywords = ['Director', 'Manager', 'Engineer', 'Developer', 'Analyst', 'Lead',
                            'VP', 'President', 'Specialist', 'Architect', 'Consultant']
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if any(keyword in next_stripped for keyword in title_keywords) or next_stripped.startswith('http'):
                    current_author = stripped
                    i += 1
                    continue

            # Check if next line is a timestamp - this is definitely the author name
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.strip()
                if next_line.startswith('  ') and ('AM' in next_stripped or 'PM' in next_stripped):
                    current_author = stripped
                    i += 1
                    continue

            # Otherwise, assume it's a name if it's short and not a system message
            if (len(stripped.split()) <= 4 and
                not stripped.startswith('This conversation') and
                not stripped.startswith('Message ')):
                current_author = stripped

        i += 1

    return messages


def generate_frontmatter(messages: List[Tuple[str, str, str]],
                        conversation_type: str = "unknown",
                        channel_name: str = None,
                        subject: str = None) -> str:
    """Generate YAML frontmatter for the cleaned thread."""

    # Extract unique participants
    participants = sorted(set(name for name, _, _ in messages))

    # Extract all @mentions from message content
    all_text = ' '.join(msg for _, _, msg in messages)
    mentions = re.findall(r'@(\w+)', all_text)

    # Try to match mentions to participants
    participant_mentions = {}
    for mention in set(mentions):
        mention_lower = mention.lower()
        for participant in participants:
            participant_clean = re.sub(r'[^\w]', '', participant.lower())
            participant_words = participant.lower().split()

            matches = False
            if mention_lower in participant_clean or participant_clean in mention_lower:
                matches = True
            elif len(mention_lower) >= 3 and len(participant_clean) >= 3:
                if mention_lower[:3] == participant_clean[:3]:
                    matches = True
                for word in participant_words:
                    if len(word) >= 3 and mention_lower.startswith(word[:3]):
                        matches = True
                        break

            if matches:
                participant_mentions[participant] = f"@{mention}"
                break

    date_saved = datetime.now().strftime("%Y-%m-%d")

    frontmatter = "---\n"
    frontmatter += f"subject: {subject if subject else ''}\n"
    frontmatter += "source: Slack\n"
    frontmatter += f"type: {conversation_type}\n"

    if channel_name:
        frontmatter += f"channel: {channel_name}\n"

    frontmatter += f"when: {date_saved}\n"
    frontmatter += "context: \n"
    frontmatter += "\n"
    frontmatter += "participants:\n"

    for i, p in enumerate(participants):
        frontmatter += f"  - name: {p}\n"
        if p in participant_mentions:
            frontmatter += f"    mention: {participant_mentions[p]}\n"
        frontmatter += f"    title: \n"
        frontmatter += f"    org: \n"
        frontmatter += f"    note: \n"
        frontmatter += f"    profile_url: \n"
        if i < len(participants) - 1:
            frontmatter += "\n"

    frontmatter += "---\n\n"

    return frontmatter


def generate_filename(messages: List[Tuple[str, str, str]],
                     conversation_type: str,
                     channel_name: str = None) -> str:
    """Generate a descriptive filename for the cleaned thread."""

    date_str = datetime.now().strftime("%Y-%m-%d")

    def sanitize(text: str) -> str:
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-').lower()

    if conversation_type == "dm":
        participants = sorted(set(name for name, _, _ in messages if name != "Unknown"))
        if len(participants) > 3:
            name_part = "group-dm"
        else:
            name_part = "with-" + "-".join(sanitize(p) for p in participants)
        filename = f"{date_str}-slack-convo-{name_part}.md"
    else:  # channel
        if channel_name:
            channel_part = sanitize(channel_name)
            filename = f"{date_str}-slack-convo-from-{channel_part}.md"
        else:
            participants = sorted(set(name for name, _, _ in messages if name != "Unknown"))
            if len(participants) > 3:
                name_part = "channel"
            else:
                name_part = "-".join(sanitize(p) for p in participants[:3])
            filename = f"{date_str}-slack-convo-{name_part}.md"

    return filename


def format_as_markdown(messages: List[Tuple[str, str, str]],
                       include_frontmatter: bool = True,
                       conversation_type: str = "unknown",
                       channel_name: str = None,
                       subject: str = None) -> str:
    """Convert parsed messages to clean markdown."""

    output = []

    if include_frontmatter:
        output.append(generate_frontmatter(messages, conversation_type, channel_name, subject))

        participants = sorted(set(name for name, _, _ in messages))
        participant_list = ", ".join(participants)

        header_title = subject if subject else "[Subject - fill in]"
        output.append(f"# {header_title}\n")
        type_line = f"**Type:** {conversation_type}"
        if channel_name:
            type_line += f" • **Channel:** {channel_name}"
        output.append(type_line + "  ")
        output.append(f"**When:** {datetime.now().strftime('%Y-%m-%d')}  ")
        output.append(f"**Participants:** {participant_list}  ")
        output.append("**Context:** [fill in]\n")
        output.append("---\n")

    for name, timestamp, message in messages:
        output.append(f"**{name}** *[{timestamp}]*\n")
        output.append(message)
        output.append("")  # Blank line between messages

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Clean up Slack thread exports into readable markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 slack_cleanup.py < input.txt > output.md
  python3 slack_cleanup.py input.txt --type dm --output
  python3 slack_cleanup.py input.txt --channel "jet-help" --output
  python3 slack_cleanup.py input.txt --unknown "Mike Smith" --output
        """
    )
    parser.add_argument('input_file', nargs='?',
                       help='Input file (or use stdin)')
    parser.add_argument('--type', choices=['channel', 'dm'], default='channel',
                       help='Conversation type (default: channel)')
    parser.add_argument('--channel',
                       help='Channel name (for filename and frontmatter)')
    parser.add_argument('--subject',
                       help='Conversation subject/title')
    parser.add_argument('--unknown', default='Unknown',
                       help='Name to use for messages without author (default: Unknown)')
    parser.add_argument('--no-frontmatter', action='store_true',
                       help='Skip YAML frontmatter')
    parser.add_argument('--output', '-o', action='store_true',
                       help='Auto-generate output filename and write to file')

    args = parser.parse_args()

    # Read input
    if args.input_file:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()
    else:
        if sys.stdin.isatty():
            print("Paste Slack thread text (Ctrl-D when done):", file=sys.stderr)
        input_text = sys.stdin.read()

    # Parse the messages
    messages = parse_slack_export(input_text, unknown_name=args.unknown)

    if not messages:
        print("No messages could be parsed. Check input format.", file=sys.stderr)
        sys.exit(1)

    # Generate output
    output = format_as_markdown(
        messages,
        include_frontmatter=not args.no_frontmatter,
        conversation_type=args.type,
        channel_name=args.channel,
        subject=args.subject
    )

    # Write output
    if args.output:
        filename = generate_filename(messages, args.type, args.channel)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Wrote to: {filename}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
