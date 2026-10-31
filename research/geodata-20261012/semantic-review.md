# Geographic source review / 2026-10-12

Single-agent semantic review of four captured primary documentation/policy sources and five normalized claims. No independent reviewer claim. Refinery validates evidence spans, capture hashes and applicable structural bites; this review checks interpretation.

AWS provider readme explicitly describes Copernicus as a surface model containing buildings, infrastructure and vegetation. Claim span now uses the explicit object phrase instead of relying on the DSM acronym. Point-center georeferencing matches COG GeoTIFF PixelIsPoint tags. Copernicus collection documentation specifies EGM2008 EPSG3855 and metre elevations; the local TIFF horizontal keys and pixel extraction are independently checked. Source publication/distribution year is not an individual pixel acquisition timestamp.

OSM copyright establishes data attribution and ODbL terms; raster tile policy disallows offline/bulk prefetch. Implementation uses a bounded Overpass vector extract, own rendering and source-attributed local data, zero public raster tile requests. This is a source policy/engineering decision, not a comprehensive legal compliance opinion.

The dataset is public sample context for existing SITL Home, not evidence of a certified operational survey site. Unknown obstacle currency, local bare-ground error, geoid/launch conversion and camera calibration remain explicit. Research claims are not promoted into measured device/field facts or operational flight permission.
