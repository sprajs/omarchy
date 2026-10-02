# Instant wallpaper switch visual evidence

Parent: `821ae589059ffdadc970315f866c94b55d268af7`.
Candidate: `37d024fbea4e6a5e9ea9eb7fdf7add55a2e7020e`.

The captures show an isolated Qt Quick window rendered offscreen with the actual BackgroundMedia component and the actual transition, size-queue, and probe-completion function bodies from each revision. The fixture uses green and blue PNG images and delays the mocked header-probe completion by 800 ms to make the intermediate state inspectable. It substitutes only the module import and supplies the two actual Util functions the shared component needs. Quickshell desktop surfaces, IPC, and compositor behavior are not exercised.

Each still has three stages, left to right: the old wallpaper, the pending header probe, and the ready replacement. The animation compares the parent on the left with the candidate on the right. An empty transparent image appears black in this export. The candidate retains green until it can show blue. Frame timings are illustrative, not measurements of desktop switch latency.

`verify.py` generates the source-derived fixture and PNG inputs without external Python packages. With both commits in a local checkout:

```bash
python verify.py /path/to/omarchy /tmp/wallpaper-fixture
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software /usr/lib/qt6/bin/qml /tmp/wallpaper-fixture/before/fixture.qml
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software /usr/lib/qt6/bin/qml /tmp/wallpaper-fixture/after/fixture.qml
```

Each fixture exports `frame-10.png`, `frame-15.png`, `frame-30.png`, and `frame-45.png` in its own directory, then exits. The collage labels and animation were assembled with ImageMagick. These are component render captures, not live full-desktop screenshots.
