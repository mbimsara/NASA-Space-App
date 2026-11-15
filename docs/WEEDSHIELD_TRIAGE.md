# WeedShield field-photo triage

Status: implemented as a transparent, on-device screening tool. It is **not** a
trained weed or species classifier.

The browser downsizes a selected field photo to at most 900 pixels on its longest
side and counts opaque pixels as vegetation-like when green is at least 40,
colour contrast is at least 20, and green exceeds both red and blue by 8%. It
returns the matching-pixel percentage and the exact method identifier
`transparent-green-pixel-heuristic-0.1`. The photo is not uploaded or stored.

This percentage is not weed coverage. Crop canopy, weeds, residue, lighting,
shadow, camera angle, senescent plants, and soil colour may change it. The user
must inspect representative field points and locally identify crop versus weed
before any management decision. The tool never recommends herbicides.

When an HLS V2.0 context artifact exists for the selected farm, the page displays
its accepted observation count and provenance separately. HLS 30 m NDVI is not
used to classify the phone photo and cannot identify individual weeds. A future
species classifier must have an appropriately licensed, representative labelled
dataset, independent validation for the target crops/region, per-class quality
metrics, and an explicit unsupported/unknown result.
