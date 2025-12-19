# Create Feature PR Workflow

## Description
Automates the process of creating a feature branch, committing changes, pushing to remote, and creating a Pull Request using GitHub CLI.

## When to Use
Trigger this workflow when:
- A significant feature is completed and tested
- Multiple related changes need to be bundled into a PR
- You want to automate the branch → commit → push → PR flow

## Trigger
Manual trigger via `/workflow` command in Cascade chat.

---

## Instructions for Cascade

When this workflow is triggered, perform the following steps:

### Step 1: Gather Information
Ask the user for:
1. **Feature name** (used for branch name, e.g., "add-config-system")
2. **Brief description** of the changes (for commit message and PR description)
3. **PR title** (optional - defaults to feature name formatted)

### Step 2: Check Prerequisites
Before proceeding, verify:
```bash
# Check if gh CLI is installed
gh --version

# Check if authenticated
gh auth status

# Check git status for uncommitted changes
git status
```

If gh CLI is not installed or not authenticated, guide the user to:
```bash
# Install gh CLI (macOS)
brew install gh

# Authenticate
gh auth login
```

### Step 3: Create Feature Branch
```bash
# Get current branch (usually main)
git branch --show-current

# Create and switch to feature branch
git checkout -b feature/<feature-name>
```

### Step 4: Stage and Commit Changes
```bash
# Show what will be committed
git status

# Stage all changes (or specific files if user prefers)
git add .

# Commit with descriptive message
git commit -m "<type>: <description>

<detailed description of changes>

Changes:
- <change 1>
- <change 2>
- <change 3>"
```

Use conventional commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

### Step 5: Push to Remote
```bash
# Push the new branch to origin
git push -u origin feature/<feature-name>
```

### Step 6: Create Pull Request
```bash
# Create PR using gh CLI
gh pr create \
  --title "<PR title>" \
  --body "<PR description with:
  
## Summary
<Brief summary of changes>

## Changes Made
- <Change 1>
- <Change 2>
- <Change 3>

## Testing
- <How it was tested>

## Screenshots (if applicable)
N/A
" \
  --base main
```

### Step 7: Provide Summary
After completion, display:
- Branch name created
- Commit hash
- PR URL (from gh pr create output)
- Next steps (review, merge instructions)

---

## Example Usage

**User**: "I've completed the configuration system feature, create a PR"

**Cascade will**:
1. Ask for feature name: `add-config-system`
2. Create branch: `feature/add-config-system`
3. Commit with message describing the config system changes
4. Push to origin
5. Create PR with detailed description
6. Return PR URL for review

---

## Notes
- Always ensure tests pass before creating PR
- Review the diff before committing
- Use meaningful commit messages
- Link related issues in PR description if applicable
