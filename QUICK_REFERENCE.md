# Quick Reference Guide

## Where to Find Everything

### 🚀 Getting Started
→ Read: [docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md)

### 📖 Documentation
- [README.md](README.md) - Project overview
- [docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md) - How to run the pipeline
- [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - Technical details
- [docs/DELIVERY_SUMMARY.md](docs/DELIVERY_SUMMARY.md) - What was delivered
- [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) - Roadmap

### 💻 Project Organization
- [ORGANIZATION.md](ORGANIZATION.md) - How files are organized
- [MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md) - Project setup record
- [docs/README.md](docs/README.md) - Documentation index

## Common Tasks

### Run the Pipeline
```bash
# Demo mode (no AWS)
python -m src run --config config/demo_config.yaml

# Production with S3
python -m src run --config config/production_config.yaml --push
```

### Run Tests
```bash
# All tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Just orchestrator tests
pytest tests/test_orchestrator.py -v
```

### Check Git Status
```bash
# Verify local/ folder is properly ignored
git check-ignore local/

# See repository status
git status
```

### View Documentation
```bash
# Open documentation index
cat docs/README.md

# Read usage guide
cat docs/PIPELINE_GUIDE.md

# See technical details
cat docs/IMPLEMENTATION_SUMMARY.md
```

## Directory Structure

```
climate-data-monitor/
├── src/                          # Source code
├── tests/                        # Test suite (61+ tests)
├── config/                       # Configuration files
├── data/                         # Sample data
├── docs/                         # 📁 PUBLIC documentation
├── local/                        # 📁 Local-only files (git-ignored)
├── README.md                     # Project overview
├── ORGANIZATION.md               # This structure guide
├── MIGRATION_CHECKLIST.md        # Organization changes
├── QUICK_REFERENCE.md            # This file
└── pyproject.toml                # Poetry config
```

## Files to Read Based on Your Role

### If you're a user:
1. [README.md](README.md) - Overview
2. [docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md) - How to use it
3. [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - How it works

### If you're contributing:
1. [ORGANIZATION.md](ORGANIZATION.md) - Project structure
2. [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - Architecture
3. [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) - What needs building
4. Source code in `src/`

### If you're developing locally:
1. Use `/local/` for temporary files, notes, experiments
2. Nothing in `/local/` is tracked by git
3. Perfect for development work

## Key Files

| File | Purpose |
|------|---------|
| `src/orchestrator.py` | Coordinates the pipeline |
| `src/__main__.py` | CLI entry point |
| `config/demo_config.yaml` | Local testing config |
| `config/production_config.yaml.template` | AWS S3 template |
| `docs/PIPELINE_GUIDE.md` | Complete usage guide |
| `.gitignore` | Git exclusions |

## Status

- ✅ Pipeline: Fully functional, production-ready
- ✅ Tests: 61+ comprehensive tests
- ✅ Documentation: Complete and organized
- ✅ Ready to deploy

## Next Steps

1. ✅ Code is complete
2. ✅ Tests are passing
3. ✅ Documentation is organized
4. 📌 Ready for your next phase of work

---

**Last updated:** January 8, 2025
