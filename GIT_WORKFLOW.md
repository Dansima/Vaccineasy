# 🔀 Git Workflow Guide for Vaccineasy

This guide teaches you the essential Git commands for managing your project.

---

## 📚 Key Concepts

| Concept | What it means |
|---------|---------------|
| **Commit** | A snapshot of your code at a point in time, like a "save point" |
| **Branch** | A parallel version of your code for developing features safely |
| **Tag** | A label for a specific commit (used for releases like `v4.0`) |
| **Push** | Send your local commits to GitHub |
| **Pull** | Download new commits from GitHub to your local machine |

---

## 🔄 Daily Workflow

### 1. Check what's changed
```bash
git status
```

### 2. Stage your changes
```bash
# Stage specific files
git add app/main.py app/database.py

# Or stage everything
git add .
```

### 3. Commit (save a snapshot)
```bash
git commit -m "Add vaccination recording feature"
```
> 💡 Write commit messages that describe **what** you changed and **why**.

### 4. Push to GitHub
```bash
git push origin master
```

---

## 🌿 Feature Branches

Use branches when working on new features. This keeps `master` stable.

### Create a new branch
```bash
git checkout -b feature/export-pdf
```

### Work on your feature
```bash
# Make changes, then...
git add .
git commit -m "Add PDF export for Anexa 1"
```

### Switch back to master
```bash
git checkout master
```

### Merge your feature into master
```bash
git checkout master
git merge feature/export-pdf
git push origin master
```

### Delete the branch (after merging)
```bash
git branch -d feature/export-pdf
```

---

## 🏷️ Tagging Releases

Tags mark a specific version in your history. Use them for releases.

### Create a tag
```bash
git tag v4.0
```

### Push tags to GitHub
```bash
git push --tags
```

### View all tags
```bash
git tag -l
```

---

## 📜 Viewing History

### See commit log
```bash
git log --oneline -10
```

### See what changed in a specific commit
```bash
git show 91326bd
```

### Compare two versions
```bash
git diff v3.2 v4.0
```

---

## ⏪ Recovering Old Versions

### View a file from an old version (without changing anything)
```bash
git show v3.2:Vaccineasy_v3.2.py
```

### Restore a file from an old version
```bash
git checkout v3.2 -- Vaccineasy_v3.2.py
```

---

## 🚀 Deploying Updates (on your Ubuntu server)

```bash
# 1. Pull latest code
cd ~/Vaccineasy
git pull origin master

# 2. Rebuild and restart Docker
docker compose down
docker compose build
docker compose up -d

# 3. Check logs
docker compose logs -f vaccineasy
```

---

## ⚠️ Common Mistakes to Avoid

1. **Don't commit sensitive data** (patient Excel files, database files) — the `.gitignore` prevents this
2. **Always `git pull` before `git push`** if you work from multiple machines
3. **Write clear commit messages** — `"fix bug"` is bad, `"Fix: vaccination engine now reports all overdue vaccines"` is good
