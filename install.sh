#!/usr/bin/env bash
# Install agent-skills content into ~/.claude/skills and ~/.claude/commands.
# See README.md for usage. Safe to run multiple times; skips existing items
# unless --force is passed.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FORCE=0
LINK=0
DRY_RUN=0
ALL=0
GLOBAL=0
TARGETS=()

INSTALLED=0
SKIPPED=0
FAILED=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [options] <target>...

Installs into \$PWD/.claude/ by default. Pass --global for ~/.claude/.

Targets:
  <category>   Install all skills+commands in that category (e.g. git)
  <name>       Install a single skill or command by name (e.g. git-hooks)
  --all        Install everything under skills/ and commands/

Options:
  --global     Install to ~/.claude/ instead of \$PWD/.claude/
  --link       Symlink instead of copy (updates flow from repo)
  --force      Overwrite existing files at the destination
  --dry-run    Print planned actions, don't touch filesystem
  -h, --help   Show this help
EOF
}

die() { echo "error: $*" >&2; exit 2; }
log() { echo "$*"; }

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --all)     ALL=1 ;;
      --link)    LINK=1 ;;
      --force)   FORCE=1 ;;
      --dry-run) DRY_RUN=1 ;;
      --global)  GLOBAL=1 ;;
      -h|--help) usage; exit 0 ;;
      --*)       die "unknown flag: $1" ;;
      *)         TARGETS+=("$1") ;;
    esac
    shift
  done

  if (( ALL == 1 )) && (( ${#TARGETS[@]} > 0 )); then
    die "--all is mutually exclusive with positional targets"
  fi
  if (( ALL == 0 )) && (( ${#TARGETS[@]} == 0 )); then
    usage >&2
    exit 2
  fi
}

# Resolve install destination based on --global flag. Runs after parse_args.
resolve_dest() {
  if (( GLOBAL == 1 )); then
    CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
    [[ -d "$CLAUDE_HOME" ]] || die "$CLAUDE_HOME does not exist. Install Claude Code first."
  else
    CLAUDE_HOME="$(pwd)/.claude"
  fi
  SKILLS_DEST="$CLAUDE_HOME/skills"
  COMMANDS_DEST="$CLAUDE_HOME/commands"
}

preflight() {
  resolve_dest
  mkdir -p "$SKILLS_DEST" "$COMMANDS_DEST"
}

# Safety: ensure a path we're about to remove lives under ~/.claude/skills or
# ~/.claude/commands. Prevents accidental rm -rf outside the install targets.
assert_under_claude_home() {
  local target="$1"
  case "$target" in
    "$SKILLS_DEST"/*|"$COMMANDS_DEST"/*) return 0 ;;
    *) die "refusing to touch path outside install targets: $target" ;;
  esac
}

# Perform the actual copy/link/overwrite for one source -> dest pair.
# $1 = source path (file or dir), $2 = dest path, $3 = label for logs
place() {
  local src="$1" dest="$2" label="$3"

  if [[ -e "$dest" || -L "$dest" ]]; then
    if (( FORCE == 0 )); then
      log "skipped: $label (already installed, use --force to overwrite)"
      SKIPPED=$((SKIPPED + 1))
      return 0
    fi
    if (( DRY_RUN == 1 )); then
      log "would overwrite: $label"
    else
      assert_under_claude_home "$dest"
      rm -rf "$dest"
    fi
  fi

  if (( DRY_RUN == 1 )); then
    if (( LINK == 1 )); then
      log "would link: $label"
    else
      log "would install: $label"
    fi
    INSTALLED=$((INSTALLED + 1))
    return 0
  fi

  if (( LINK == 1 )); then
    ln -s "$src" "$dest"
    log "linked: $label"
  else
    if [[ -d "$src" ]]; then
      cp -R "$src" "$dest"
    else
      cp "$src" "$dest"
    fi
    log "installed: $label"
  fi
  INSTALLED=$((INSTALLED + 1))
}

install_skill() {
  local skill_dir="$1"                    # absolute path to skills/<cat>/<name>
  local name
  name="$(basename "$skill_dir")"
  place "$skill_dir" "$SKILLS_DEST/$name" "$name"
}

install_command() {
  local cmd_file="$1"                     # absolute path to commands/<cat>/<name>.md
  local name
  name="$(basename "$cmd_file")"
  place "$cmd_file" "$COMMANDS_DEST/$name" "${name%.md} (command)"
}

install_category() {
  local cat="$1"
  local skill_cat_dir="$REPO_DIR/skills/$cat"
  local cmd_cat_dir="$REPO_DIR/commands/$cat"
  local found=0

  if [[ -d "$skill_cat_dir" ]]; then
    found=1
    shopt -s nullglob
    for skill in "$skill_cat_dir"/*/; do
      [[ -f "$skill/SKILL.md" ]] || continue
      install_skill "${skill%/}"
    done
    shopt -u nullglob
  fi

  if [[ -d "$cmd_cat_dir" ]]; then
    found=1
    shopt -s nullglob
    for cmd in "$cmd_cat_dir"/*.md; do
      [[ "$(basename "$cmd")" == "README.md" ]] && continue
      install_command "$cmd"
    done
    shopt -u nullglob
  fi

  if (( found == 0 )); then
    log "failed: category '$cat' not found"
    FAILED=$((FAILED + 1))
    return 1
  fi
}

# Search for a skill folder or command file matching <name> across categories.
# Returns path on stdout; sets global AMBIGUOUS=1 if multiple matches.
AMBIGUOUS=0
find_item() {
  local name="$1"
  local matches=()
  local kind=""

  shopt -s nullglob
  for dir in "$REPO_DIR"/skills/*/"$name"/; do
    [[ -f "$dir/SKILL.md" ]] || continue
    matches+=("${dir%/}")
    kind="skill"
  done
  for file in "$REPO_DIR"/commands/*/"$name.md"; do
    matches+=("$file")
    kind="${kind:+$kind,}command"
  done
  shopt -u nullglob

  if (( ${#matches[@]} == 0 )); then
    return 1
  fi
  if (( ${#matches[@]} > 1 )); then
    AMBIGUOUS=1
    printf '%s\n' "${matches[@]}"
    return 2
  fi
  echo "$kind:${matches[0]}"
}

install_target() {
  local target="$1"

  # Category install if skills/<target>/ or commands/<target>/ exists as a dir
  if [[ -d "$REPO_DIR/skills/$target" || -d "$REPO_DIR/commands/$target" ]]; then
    install_category "$target"
    return
  fi

  # Otherwise resolve to a single item by name
  local result
  if ! result="$(find_item "$target" 2>/dev/null)"; then
    log "failed: unknown target '$target'"
    FAILED=$((FAILED + 1))
    return 1
  fi
  if (( AMBIGUOUS == 1 )); then
    log "failed: '$target' is ambiguous — specify category/name or use the category"
    FAILED=$((FAILED + 1))
    AMBIGUOUS=0
    return 1
  fi

  local kind="${result%%:*}"
  local path="${result#*:}"
  case "$kind" in
    skill)   install_skill "$path" ;;
    command) install_command "$path" ;;
  esac
}

install_all() {
  shopt -s nullglob
  for cat_dir in "$REPO_DIR"/skills/*/; do
    install_category "$(basename "${cat_dir%/}")"
  done
  for cat_dir in "$REPO_DIR"/commands/*/; do
    local cat
    cat="$(basename "${cat_dir%/}")"
    # Skip if already handled as a skill category to avoid double logging
    [[ -d "$REPO_DIR/skills/$cat" ]] && continue
    install_category "$cat"
  done
  shopt -u nullglob
}

main() {
  parse_args "$@"
  preflight

  if (( ALL == 1 )); then
    install_all
  else
    for t in "${TARGETS[@]}"; do
      install_target "$t" || true
    done
  fi

  log "done: $INSTALLED installed, $SKIPPED skipped, $FAILED failed"
  (( FAILED == 0 )) || exit 1
}

main "$@"
