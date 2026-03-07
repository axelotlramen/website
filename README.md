# Gacha Profile Viewer

A small website that visualizes

- Memory of Chaoc (MoC) team display
- Automated daily stat updates via GitHub Actions

Built using vanilla HTML, CSS, and JavaScript, with a Python automation pipeline

To run on a local computer, simply run

```bash
python3 -m http.server 8000
```

and open `http://localhost:8000`.

## How It Works

### Data Collection

The backend data is collected using Python.

- `genshin.py` is used to authenticate and communicate with the official HoYoLaB endpoints.
- `requests` handles HTTP interactions.
- The processed results are saved in the `data` folder to be used by the frontend.

The script `main.py` runs automatically every 24 hours via GitHub Actions.

## Bug Fixes

- Fix the website as right now it doesn't showcase much
- Add Endfield data
- Add specific characters owned for each game if not too much clutter

## Future Improvements

- Cycle performance color indicator
- Statistics summary panel
- Add Pure Fiction, Apocalyptic Shadow and Anomaly Arbitration

## Disclaimer

This project is a fan-made viewer and is not affiliated with HoYoverse. All assets belong to their respective owners.
