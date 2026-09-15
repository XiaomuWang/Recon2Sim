# GitHub publication

Repository: `https://github.com/XiaomuWang/Recon2Sim`

Expected project homepage: `https://xiaomuwang.github.io/Recon2Sim/`

The source directories and `docs/` are tracked through an explicit `.gitignore` allowlist. Raw inputs, complete reconstruction outputs, CARLA installation archives, per-frame captures, Unreal projects, caches and bundled runtimes are excluded. `docs/` contains only the eight report movies, highlight movie, posters, analysis charts, CSV tables, entity mappings, compact validation summaries and static viewer pages. These are public website assets.

## Preview without CARLA

```sh
python -m a2s.report_server --bind 127.0.0.1 --port 8000 --directory docs
```

Open `http://127.0.0.1:8000/`. Python 3.8+ and its standard library are sufficient for this preview. The server supports byte ranges for video seeking. GitHub Pages hosts the static files directly; it does not run this Python server.

## Deployment

In the repository's **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**. The `Publish report to GitHub Pages` workflow deploys `docs/` from `main`, which must also be the repository default under **Settings → General → Default branch**. Under **Settings → Environments → github-pages → Deployment branches and tags**, allow `main` to deploy. If renaming the primary branch later, update both the workflow's branch filter and the environment's allowed branch.

For a manual deployment, open **Actions → Publish report to GitHub Pages → Run workflow**, selecting the default branch. No personal access token needs to be committed or added to the website. The workflow uses GitHub's built-in deployment credentials.

## Updating report assets locally

After regenerating the local reports in `outputs/`:

```sh
python -m a2s.report_page
python tools/export_pages.py
python tools/check_pages.py
```

Commit the changed `docs/` files. The exporter preserves the requested scene order, removes installation-package/legacy-offline links, and publishes verification summaries without local machine paths. It requires completed local reconstruction outputs, while deployment only needs the already exported `docs/` directory.

For the motion-updated original seven, use `python -m a2s.motion_release run` and then `promote` after successful verification. These commands stage the captures, preserve previous reports, rebuild the seven-case highlights and regenerate the page. Configure the matching CARLA 0.9.15 client as described in README.md. A later release must use a new `--stage work/motion_release_<version>` for both commands. The published runtime summaries disclose native locomotion, reconstruction constraints and recorded-pose exceptions. After deployment, `python tools/check_motion_pages.py` checks the deployed page, seven summaries and byte-range video responses against the exported files.

Video assets are tracked directly for this initial publication; each is below GitHub's 100 MiB file limit, and the full site is below the Pages size limit. Frequent video replacements enlarge Git history, so future large or frequent datasets can be moved to separate artifact hosting. Git LFS is not required for this publication.

The complete reconstruction pipeline additionally requires the externally supplied source data and tools documented in README.md; cloning this repository alone does not reproduce unshipped datasets or install CARLA/Unreal.


## Eighth case: 157116

The public catalog now contains eight cases, with Pony 157116 first. Its approved 21-second 1080p video uses the detailed static v2 reconstruction and recorded CARLA poses. The original seven retain their published motion-updated videos. The eight-case highlights run for 96 seconds.

Local raw inputs for 157116 are under `data/` in the folder named by `configs/157116.json`; `video_files` maps front/rear/left/right to the original Chinese filenames. All four cameras are fisheye. Calibration was not supplied, so metric layout and trajectories remain visual estimates; the CARLA presentation camera is not a calibrated lens recreation. Raw videos and engine packages remain outside Git.
