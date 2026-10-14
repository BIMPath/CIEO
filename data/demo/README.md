# `data/demo/` — synthetic observations

**This is not data, and nothing produced from it is a result.** Every number here is
invented to exercise a code path.

It exists so the adapters, the rules and the reasoning can be run and checked before a real
point cloud, a real game-engine scene and real detector output are available — and so a
newcomer can watch the whole chain work without first reproducing a photogrammetric
reconstruction.

```bash
python3 src/build_kb.py --project via-alba-savigliano
python3 src/run_reasoning.py          # reads the synthetic observations below
python3 tests/verify_repo.py
```

| File | Replace it with |
|---|---|
| `viewpoints.json` | Camera poses from your depth-estimation and registration pipeline. |
| `conditions.ttl`, `observation_conditions.json` | Output of `unity/VisibilityBatchRunner.cs` run against your phase scenes. |
| `detections.json`, `observations.ttl` | Your detector's inference over your site imagery, passed through `src/observation_adapter.py`. |
| `image_zones.csv` | Your own image-to-zone grounding. |

Regenerate the synthetic set with `python3 src/make_demo_data.py`.

The decision states this produces are *not* the ones in the publication. Those come from
the real imagery of the Via Alba inspection, which is not redistributed here.
