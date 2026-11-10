# Original Short — Why Can't You Reach the End of a Rainbow?

**Episode date:** 10 November 2026  
**Video slug:** `rainbow-chase`  
**Status:** original technical preview only; not approved or uploaded to YouTube/TikTok.  
**Difference from prior releases:** previous episode `rainbow-optics` explains
how rainbows form; this original story explains why **the apparent end cannot
be approached** and why the drops visible to different observers differ.

## The finished original narration (English)

1. White sunlight reaches falling raindrops, carrying many colors even though the beam looks perfectly white.
2. Entering a raindrop, each color refracts and bends by a slightly different angle inside water.
3. Some light reflects from the curved inside back surface, turning toward the front of the drop.
4. Leaving the drop, the colors bend again, sending selected rays toward your eyes at precise viewing angles.
5. Millions of droplets create the rainbow each observer sees; when you move, its apparent end moves too.

**Editorial note:** This is a qualitative educational demonstration, not a
numerical ray tracer. The perceived rainbow is an angular collection of
light from many different raindrops, not a physical colored object that
can be physically reached. The optical image depends on the observer's
position relative to light and droplets. No photos or unlicensed footage.

## Actual workflow

- Production: `.github/workflows/rainbow-chase-original-short.yml`.
- Source graphics: existing **original** 2.5D rainbow scene system,
  droplet optics, light paths and moving atmosphere; five causal beats
  `sunlight`, `refraction`, `reflection`, `emergence`, `arc`.
- English voice: **Kokoro af_heart**, natural pacing, audio-timed subtitles.
- Video: native **1080 × 1920, 30 fps H.264/AAC**, high render profile,
  ~33 s; originally composed ambient soundtrack.
- Media QA: speech, subtitle, moving video, black/frozen checks, decoded
  contact sheet, mobile safe areas, Shorts platform constraints.
- Stable delivery: `science-preview-download.yml` listens for the
  **successful main-branch production job** and verifies the whole public
  MP4 over anonymous HTTPS, comparing the downloaded bytes exactly against
  the original output. Stable slug `rainbow-chase`; the file is
  `rainbow-chase.mp4`, never a temporary Actions/sandbox download.
- Permanent history: successful verified release updates
  `docs/video-history.json`. Never add an entry for an unrendered idea.

**Important:** Run this on **main** after passing the source tests.
A green PR only verifies preflight (not a finished MP4); only a successful
complete main workflow plus the separate stable release is delivered.
Do not claim success or give a speculative direct download link before
the release asset exists and its full HTTP transfer is verified.
