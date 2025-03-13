# Video Combinator

A web-based application that allows users to create multiple video combinations by mixing hook videos, body videos, CTAs, and background music.

## Features

- Upload and combine multiple video files
- Add optional CTA videos to all combinations
- Add optional background music with adjustable volume
- Real-time progress tracking
- Download individual videos or all videos as a ZIP file
- Automatic cleanup of input files to save disk space

## Requirements

- Python 3.7+
- Flask
- MoviePy
- Werkzeug

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/tap1on/video-combinator.git
   cd video-combinator
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create the necessary directories (if they don't exist):
   ```
   mkdir -p uploads output
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Upload your videos:
   - **Hook Videos** (Required): These will be the beginning of each video
   - **Body Videos** (Required): These will be the middle part of each video
   - **CTA Videos** (Optional): These will be added to the end of each video
   - **Background Music** (Optional): This will be added to the videos

4. Adjust the background music volume if needed

5. Click "Create Videos" to start processing

6. Once processing is complete, you can:
   - Download individual videos by clicking on their names
   - Download all videos as a ZIP file
   - Create more videos by clicking the "Create More Videos" button

## How It Works

The application creates all possible combinations of the uploaded videos:
- Each hook video is combined with each body video
- If CTA videos are provided, they are added to all combinations
- If background music is provided, versions with and without music are created

For example, if you upload:
- 2 hook videos
- 2 body videos
- 1 CTA video
- 1 background music file

The application will create 8 different videos (2 hooks × 2 bodies × 1 CTA × 2 music options).

## License

MIT
