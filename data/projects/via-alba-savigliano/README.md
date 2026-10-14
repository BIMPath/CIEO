# Via Alba bridge replacement, Savigliano (CN), Italy

The reference project, and the case study of the accompanying publication. Replacement of
the road bridge carrying Via Alba over the Mellea stream: a composite steel-concrete
structure replacing a masonry arch.

| | |
|---|---|
| Asset type | `RoadBridge` |
| Profile chain | `project → it → eu` |
| Phases | 6, mapped onto 9 generic stages |
| Photographs | 354, 4032 × 3024 px, 67° horizontal field of view |
| Captured | April 2026 |
| Coverage | 37 of 37 requirements bound |

## Why it is here

Not because the bridge is interesting, but because it is the only project in the repository
for which real imagery, a real reconstruction and a real inspector's determination all
exist. It is the thing to point a change at when you want to know whether the change broke
anything.

## What the site A-Box holds

`site.ttl` carries the project, its six phases as they actually ran, and the spatial zones
and elements they bring into existence: the traffic-management zone, the work-zone
boundary, the utility trench, the excavation boundary and face, the abutments, the steel
members, the deck slab, the pavement and the restraint systems — each with its IFC
identity where one exists.

`site-additions.ttl` carries three targets added after the 2026 site inspection, which
correspond to conditions actually photographed rather than to synthetic individuals: the
ladder access to the left abutment, the steel storage area on its timber packing, and the
mobile crane set-up with its outrigger pads.

The extents on those three are the values to draw or count on the Unity marker. Keep them
in step with the polyline you author: `visibility_to_rdf.py` writes a second spatial extent
from the measured geometry, and the SHACL shape only checks that an extent exists, so two
disagreeing values pass silently.

## Project-level bindings

`clause_bindings.csv` here holds the two requirements grounded in contract documents rather
than in law — the approved utility specification and the ANAS bituminous-binder
specification. They sit at precedence 0 and override anything the national or EU profiles
say, which is the correct order: a contract specification binds the contractor whatever the
general standard permits.

## Rebuilding

```bash
python3 src/validate_data.py
python3 src/build_kb.py --project via-alba-savigliano
```
