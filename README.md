# Gacha Profile Viewer

A small website that visualizes

- Pull history with dynamic icon grid
- Pity counter with gradient badges
- Win / Lose / Guaranteed border indicators
- Memory of Chaoc (MoC) team display
- Automated daily stat updates via GitHub Actions

Built using vanilla HTML, CSS, and JavaScript, with a Python automation pipeline

## How It Works

### Data Collection

The backend data is collected using Python.

- `genshin.py` is used to authenticate and communicate with the official HoYoLaB endpoints.
- `requests` handles HTTP interactions.
- The processed results are saved in the `data` folder to be used by the frontend.

The script `update_stats.py` runs automatically every 24 hours via GitHub Actions.

### Character & Light Cone Icons

Icons are generated using the ID:

```js
if (id >= 20000) {
  iconURL = `https://stardb.gg/api/static/StarRailResWebp/icon/light_cone/${id}.webp`;
} else {
  iconURL = `https://stardb.gg/api/static/StarRailResWebp/icon/character/${id}.webp`;
}
```

### Pity Gradient Logic

Pity badge color interpolates between **Low** (`#57bb8a`), **Mid** (`#ffd666`), and **High** (`#e67c73`). The range is 1-90 pity.

## Future Improvements

- Cycle performance color indicator
- Statistics summary panel
- Add Pure Fiction, Apocalyptic Shadow and Anomaly Arbitration

## Disclaimer

This project is a fan-made viewer and is not affiliated with HoYoverse. All assets belong to their respective owners.
