# VISUAL56 · Flight Lab

Start from project root: `node pilot/visual56/server.mjs`, then open http://127.0.0.1:8808/. Requires Node with statfs support and at least20GiB free. Port8808 must be unused. No dependency install/build required. Existing SIMTRAIN53 on8807 is separate.

Real glTF UAV mesh (EdMackey/AGI, CC BY4.0), runtime graphite materials, PBR asphalt, photographed HDRI2K illumination and panorama8K background, ACES/sRGB, SSAO and shadows. Four animated rotors follow estimated RPM from replay. Model is5844 triangles, scaled to about1.03m span; it is an illustrative quad, not a calibrated Hera model. Environment is photographic projection plus local3D ground, not surveyed3D terrain.

Two actual retained SIMTRAIN53 WAL recordings supply pose/RPM. CRC/SHA-chain checked during extraction; original1200Hz WAL remains untouched. Render derivative selects30Hz snapshots and interpolates for display. This is replay, not live flight control. Buttons change camera, playback and source; drag to orbit, wheel to zoom. Lưu ảnh saves canvas PNG in evidence/visual56 via bounded same-origin local endpoint. No flight command route/proxy is provided.

Source: credits.html, evidence/visual56/acquisition.json, assets-fetch.json and sky-background-source.json. Run `python3 pilot/visual56/verify.py` for first verification receipt; it refuses to overwrite it. Acquisition scripts are preparation tools, not normal startup. Review delivery/COMPLETION-VISUAL56.md for validation and limits.
