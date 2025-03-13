# Video Hook Maker

A Python web application that allows you to combine multiple video files to create all possible variations. This tool is designed to help create marketing videos by combining videos.

## Features

- Upload multiple hook videos (required)
- Upload multiple Body videos (required)
- Upload optional CTA videos
- Upload optional background music
- Adjust background music volume
- Real-time progress tracking
- Download individual or all generated videos

## Requirements

- Python 3.7 or higher
- Web browser (Chrome, Firefox, Edge, etc.)

## Installation

1. Download or clone this repository to your local machine.

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

3. Use the web interface to:
   - Select hook videos (required)
   - Select body videos (required)
   - Optionally select CTA videos
   - Optionally select background music
   - Adjust background music volume
   - Click "Create Videos" to start processing

4. Wait for the processing to complete. The application will show a progress bar.

5. Once processing is complete, you can download individual videos or all videos at once.

## How It Works

The application creates all possible combinations of the selected videos:

1. Each hook video will be combined with each body video.
2. If CTA videos are provided, each combination will also include each CTA video.
3. If background music is provided, each combination will also include each background music track (plus a version without any music).

For example:
- 2 hook videos
- 3 body videos
- 1 CTA video
- 1 background music track

This would create: 2 × 3 × (1+1) × (1+1) = 24 different video combinations.

## File Structure

- `app.py`: Main Python application
- `templates/index.html`: HTML template for the web interface
- `static/style.css`: CSS styles for the web interface
- `static/script.js`: JavaScript for client-side functionality
- `uploads/`: Directory where uploaded files are stored
- `output/`: Directory where generated videos are stored

## Notes

- Large video files may take a long time to process
- The application creates temporary directories for each job
- All generated videos are saved in MP4 format with H.264 encoding
