# Set2Tracks — Open Source Edition

![screenshot](s2t-screen.jpg)

## What is it?

Set2Tracks is a free tool that helps DJs and music lovers discover new tracks by automatically converting YouTube DJ sets into full tracklists.

Scan entire sets, listen to previews, browse tracks by genre or label, and link straight to Spotify or Apple Music. Support the artists.

## A bit of history

Set2Tracks got a warm welcome on [r/beatmatch](https://www.reddit.com/r/Beatmatch/comments/1i2pohr/a_free_tool_to_discover_tracks_from_dj_sets/) in early 2025. Thanks to everyone who checked it out and sent feedback.

We explored turning it into a subscription-based Chrome extension, but the economics didn't quite work out — hosting costs scale with every set processed, and let's be honest, this is the kind of tool people love to find for free but wouldn't pay for. No hard feelings, we get it.

Rather than let it disappear, we decided to open source the whole thing.

## Why open source?

We're focusing our energy on other projects at [Nexum Solis](https://nexumsolis.com), but Set2Tracks still works and might be useful to someone. Fork it, learn from it, build on it — it's yours now.

Fair warning: the codebase is... pragmatic. It was built fast to solve a problem, not to win any architecture awards. But it works.

## The status

Set2Tracks is currently on pause, but we're not ruling out a comeback. If you're interested in collaborating or have ideas, reach out.

---

## Technical Setup

### Requirements

Python 3.11.5 (virtual environment recommended)

### Quick Install

```bash
gh repo clone nexumsolis/set2tracks
# or just download it

./setup.sh
```

Then fill `app/web/.env` with your configuration.

### Running the app

Tailwind processor (monitors CSS changes):
```bash
# From ./tailwind folder
npx tailwindcss -i ../app/web/static/css/tailwind/input.css -o ../app/web/static/css/tailwind/output.css --watch
```

The app itself:
```bash
python app/web/run.py
```

### Manual Install

```bash
pip install -r requirements.txt
```

Copy `example.env` to `.env` and fill in your data.

### Notes

- **Production**: All you need is the content of the `web` folder.
- **Templates**: Most are in the boilerplate package. Override by copying from `./boilersaas/src/boilersaas/templates` to `./web/templates`.

---

## Contact

Questions about the project? [contact@nexumsolis.com](mailto:contact@nexumsolis.com)

Built something with it? We'd love to hear about it.

---

*A [Nexum Solis](https://nexumsolis.com) open source project.*