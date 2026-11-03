# Early semantic scene preflight (before Kokoro model installation)

The shared one-click workflow now creates the original scene plan **before**
downloading/installing the large neural speech dependencies. It immediately
checks each authored scene against the same specialized action classifiers used
by the volcano, aurora, lightning and rainbow renderers. A scene with no
supported action fails with an actionable scene ID; consecutive repeated
actions are review warnings, not fabricated replacements.

The exact checked scene plan is then reused for TTS and rendering. This
avoids expensive work on scripts that would previously fail only after voice
setup, and prevents silent generic imagery substitutions. Cartoon, landscape,
and Earth/ocean formats preserve their current behavior. The JSON report is
archived with the preview. No fact-checking or artistic-quality claims are made.

This is a pipeline reliability/cost improvement, not a new graphics backend.
