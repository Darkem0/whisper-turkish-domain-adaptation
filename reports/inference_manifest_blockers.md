# Inference manifest blockers

- No selected audio path is missing.

FFmpeg executable is not discoverable on PATH. `configs/local_paths.yaml:root_mappings.ffmpeg_executable` must be filled with an existing local executable before non-WAV source conversion is attempted.
