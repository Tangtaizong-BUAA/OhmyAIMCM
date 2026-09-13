# Aesthetic calibration contract

The workspace platform lives at `figure-lab/` and is the source of truth for owner preference collection.

## Fixed v1 design

- 15 domains, 10 tasks per domain;
- 150 A/B comparisons, 300 deterministic SVG assets;
- 120 primary preferences, 20 tradeoff bundles, 10 cross-scenario reliability repeats;
- side placement randomized by a versioned seed;
- candidate, asset, task, and manifest SHA-256 hashes recorded;
- append-only decisions and append-only undo events;
- winner, strength, confidence, reason tags, and optional short note retained;
- scientific hard failures excluded before comparison.

## DeepSeek boundary

The model is hard-locked to `deepseek-v4-flash`, temperature 0, thinking disabled, JSON output. It receives task metadata only and is called only after a human clicks the coach button. The response validator rejects winner recommendations. The API key remains in the local server environment and never reaches browser JavaScript.

## Commands

```bash
python3 figure-lab/scripts/build_calibration.py
python3 figure-lab/ui/server.py --host 127.0.0.1 --port 8766
python3 figure-lab/scripts/analyze_preferences.py --annotator-id owner --session-id calibration-01
```

Do not fit a preference model until coverage, stale-hash checks, side-bias audit, and all ten reliability comparisons are reviewed. Reliability examples are excluded from primary fitting.
