# Original science Short — Why Do Northern Lights Glow in Different Colors?

**Production date:** 2026-11-10
**Topic slug:** `aurora-colors` (new, distinct from the existing
`aurora-dance` episode).

## Original English script (five different physical beats)

1. The solar wind carries charged particles and energy from the Sun toward Earth's magnetic environment.
2. Earth's magnetic field guides energized particles into the polar upper atmosphere, where the air is extremely thin.
3. There, fast electrons collide with oxygen and nitrogen, transferring energy to atoms and molecules high above us.
4. Excited oxygen emits green light lower down and red light higher up, while nitrogen adds blue and pink.
5. Different colors ripple through shimmering curtains in the polar sky, revealing the atmosphere's hidden layers.

Each sentence maps to the *existing working native aurora 2.5D renderer*
in order: `solar_wind`, `magnetic_field`, `collisions`,
`emission`, `curtains`. The production source-of-truth is the script
in `.github/workflows/aurora-colors-original-short.yml`. No stock video and no copying the previous
`aurora-dance` narration or storyline.

## Verified scientific references
- NASA Science — https://science.nasa.gov/sun/auroras/:
  particles from the solar wind, magnetic interaction, upper-atmosphere
  oxygen and nitrogen emission; green/red oxygen and blue/pink nitrogen.
- NOAA SWPC — https://www.spaceweather.gov/content/aurora-tutorial:
  atomic energy levels, oxygen's green/red emissions at different
  heights, violet nitrogen fringes and the impact of collision density.

Altitude is described qualitatively to avoid suggesting a sharp
single-height cutoff: specific heights vary with conditions and the
sources use overlapping intervals.

## Original technical delivery contract
The first successful production run of `Verify original aurora-colors
science Short` on `main` renders Kokoro `af_heart` English,
original CPU-drawn 2.5D scientific actions, 30 fps, full 1080×1920,
H.264/AAC, captions, original ambient soundtrack and the existing
full source-frame + media QA checks.

Only when this **whole workflow finishes successfully** does the
`science-preview-download` workflow authenticate the source run,
download the matching real MP4 artifact, validate its SHA-256,
H.264/AAC 30 fps portrait metadata and full decode, create a public
`science-preview-aurora-colors-RUN_ID` GitHub prerelease, verify a
full anonymous HTTPS GET and bytewise equality, then update
`docs/video-history.json`. This historical file is never prefilled
with imaginary videos or links.

Human factual, visual and voice-listening review is required before
any TikTok/YouTube upload; nothing auto-publishes to social networks.
