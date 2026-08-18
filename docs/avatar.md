# Avatar

## Honest status

Real-time talking-avatar lip sync (MuseTalk, per the spec) is **not
installed**. It's a full diffusion-based video pipeline with its own
multi-GB checkpoint set and a PyTorch/CUDA pinning that would likely
conflict with the rest of this stack — installing and validating it
reliably wasn't something this build could responsibly claim to have done.

`app/avatar/musetalk.py` defines the real interface
(`is_available()`, `generate_talking_frame()`) so the integration point
exists and is checked rather than assumed — it always reports unavailable
until a real MuseTalk installation is placed at `models/musetalk/`.

## What actually ships and works

- **Face upload/storage**: `POST /api/avatar/{entity_id}/face` (multipart
  image), stored at `entities/<id>/face/avatar.<ext>`, served back via
  `GET /api/avatar/{entity_id}/face`. Entity picker in the Entities page
  lets you click a face thumbnail to change it.
- **State-driven static avatar**: `frontend/src/components/AvatarFace.tsx` —
  shows the entity's face image with a ring/pulse animation reflecting real
  state (idle / listening while the mic is recording / thinking while
  transcribing / speaking while a reply streams in), wired into the Live
  Chat page. This is the documented fallback the spec itself calls for when
  full lip sync isn't available (section 9: "provide a non-avatar fallback
  ... core AI must continue working").

## To add real lip sync later

1. Install MuseTalk per its own repo instructions into `models/musetalk/`.
2. Implement `generate_talking_frame()` in `app/avatar/musetalk.py` for real
   (currently raises `MuseTalkError` unconditionally).
3. Add a frame-streaming endpoint and swap `AvatarFace`'s static `<img>` for
   a video/canvas element consuming that stream.
