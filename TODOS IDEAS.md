Quality Control
---------------
- Check overpass functionality - (code broken or was it just overloaded everytime I checked?)
- Document/change behaviour for download methods and image saving methods for cases like missing parent dir, file already exists, etc.
- Behaviour near poles / antimeridian

Fixes
-----
- Ensure that FeatureLayer accepts bboxes AND osm ids simultaneously
- "Cleanup" ai pass

Feature Ideas
-------------
- Other map orientations and projections
- non-rectangular bboxes
  - specified using coordinates
  - how to handle "malformed" corner coordinates?
  - Utility: get shape by osm id
