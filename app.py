import os
import time
import shutil
import itertools
import urllib.parse
import zipfile
import io
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips, CompositeAudioClip

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload size

# Max age for old job files (1 hour)
MAX_JOB_AGE_SECONDS = 3600

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'wmv'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'aac', 'm4a'}

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

def cleanup_old_jobs():
    """Remove output directories and upload files from old jobs to free disk space."""
    now = time.time()
    cleaned_jobs = []

    # Clean old output directories
    output_folder = app.config['OUTPUT_FOLDER']
    if os.path.exists(output_folder):
        for job_id in os.listdir(output_folder):
            job_dir = os.path.join(output_folder, job_id)
            if os.path.isdir(job_dir):
                try:
                    dir_age = now - os.path.getmtime(job_dir)
                    if dir_age > MAX_JOB_AGE_SECONDS:
                        shutil.rmtree(job_dir, ignore_errors=True)
                        cleaned_jobs.append(job_id)
                except OSError:
                    pass

    # Clean old upload files
    upload_folder = app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            filepath = os.path.join(upload_folder, filename)
            try:
                file_age = now - os.path.getmtime(filepath)
                if file_age > MAX_JOB_AGE_SECONDS:
                    os.remove(filepath)
            except OSError:
                pass

    # Purge stale entries from job_progress dict
    stale_ids = [
        jid for jid, jdata in job_progress.items()
        if jdata.get('status') in ('complete', 'error') and jid in cleaned_jobs
    ]
    for jid in stale_ids:
        del job_progress[jid]

    if cleaned_jobs:
        print(f"Cleanup: removed {len(cleaned_jobs)} old job(s)")


@app.route('/upload', methods=['POST'])
def upload_files():
    # Auto-cleanup old files before accepting new upload
    cleanup_old_jobs()

    # Check if the required files are present
    if 'hooks' not in request.files or 'middle_cta' not in request.files:
        return jsonify({'error': 'Hook videos and Body videos are required'}), 400
    
    hooks = request.files.getlist('hooks')
    middle_cta = request.files.getlist('middle_cta')
    
    # Check if at least one file is selected for required fields
    if not hooks or hooks[0].filename == '':
        return jsonify({'error': 'At least one Hook video is required'}), 400
    
    if not middle_cta or middle_cta[0].filename == '':
        return jsonify({'error': 'At least one Body video is required'}), 400
    
    # Get optional files
    end_cta = request.files.getlist('end_cta') if 'end_cta' in request.files else []
    bg_music = request.files.getlist('bg_music') if 'bg_music' in request.files else []
    
    # Get music volume
    music_volume = float(request.form.get('music_volume', 0.3))
    if music_volume < 0 or music_volume > 1:
        music_volume = 0.3  # Default to 30% if invalid
    
    # Save all files
    hook_paths = []
    middle_cta_paths = []
    end_cta_paths = []
    bg_music_paths = []
    
    # Save hook videos
    for file in hooks:
        if file and file.filename != '' and allowed_video_file(file.filename):
            # Use secure_filename to sanitize the filename
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            hook_paths.append(filepath)
            print(f"Saved hook video: {filepath}")  # Debug log
    
    # Save middle/CTA videos
    for file in middle_cta:
        if file and file.filename != '' and allowed_video_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            middle_cta_paths.append(filepath)
            print(f"Saved middle video: {filepath}")  # Debug log
    
    # Save end CTA videos (optional)
    for file in end_cta:
        if file and file.filename != '' and allowed_video_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            end_cta_paths.append(filepath)
            print(f"Saved end CTA video: {filepath}")  # Debug log
    
    # Save background music (optional)
    for file in bg_music:
        if file and file.filename != '' and allowed_audio_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            bg_music_paths.append(filepath)
            print(f"Saved background music: {filepath}")  # Debug log
    
    # Start processing in a separate thread
    # In a real application, you might want to use Celery or a similar task queue
    # For simplicity, we'll just return a job ID and handle progress updates via AJAX
    job_id = str(int(time.time()))
    
    # Create a directory for this job's output
    job_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    os.makedirs(job_output_dir, exist_ok=True)
    
    # Store the file paths in the job_progress dictionary for later use
    job_progress[job_id] = {
        'hook_paths': hook_paths,
        'middle_cta_paths': middle_cta_paths,
        'end_cta_paths': end_cta_paths,
        'bg_music_paths': bg_music_paths,
        'music_volume': music_volume,
        'progress': 0,
        'current': 0,
        'total': 0,
        'status': 'uploaded',
        'output_files': []
    }
    
    # Return job ID and actual file paths to client
    return jsonify({
        'job_id': job_id,
        'hook_paths': hook_paths,
        'middle_cta_paths': middle_cta_paths,
        'end_cta_paths': end_cta_paths,
        'bg_music_paths': bg_music_paths
    })

# Global dictionary to store job progress
job_progress = {}

@app.route('/process/<job_id>', methods=['POST'])
def process_videos(job_id):
    if request.method == 'POST':
        if job_id not in job_progress:
            return jsonify({
                'error': 'Job not found'
            }), 404
        
        # Get file paths from job_progress dictionary
        job_data = job_progress[job_id]
        hook_paths = job_data['hook_paths']
        middle_cta_paths = job_data['middle_cta_paths']
        end_cta_paths = job_data['end_cta_paths']
        bg_music_paths = job_data['bg_music_paths']
        music_volume = job_data['music_volume']
        
        # Create output directory for this job
        job_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        os.makedirs(job_output_dir, exist_ok=True)
        
        # Calculate total combinations
        total_combinations = len(hook_paths) * len(middle_cta_paths)
        if end_cta_paths:
            total_combinations *= len(end_cta_paths)  # Always include end CTA if provided
        if bg_music_paths:
            total_combinations *= (len(bg_music_paths) + 1)  # +1 for no music option
        
        # Update job progress
        job_progress[job_id].update({
            'progress': 0,
            'current': 0,
            'total': total_combinations,
            'status': 'processing',
            'output_files': []
        })
        
        # Print debug info
        print(f"Starting processing for job {job_id}")
        print(f"Hook paths: {hook_paths}")
        print(f"Middle CTA paths: {middle_cta_paths}")
        print(f"End CTA paths: {end_cta_paths}")
        print(f"BG Music paths: {bg_music_paths}")
        
        # Start processing in a background thread
        import threading
        thread = threading.Thread(
            target=process_videos_background,
            args=(job_id, hook_paths, middle_cta_paths, end_cta_paths, bg_music_paths, music_volume)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'total_combinations': total_combinations,
            'status': 'processing'
        })

def process_videos_background(job_id, hook_paths, middle_cta_paths, end_cta_paths, bg_music_paths, music_volume):
    """Process videos in the background and update progress"""
    job_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)

    # Collect all input files for cleanup later
    all_input_files = list(hook_paths) + list(middle_cta_paths)
    if end_cta_paths:
        all_input_files.extend(end_cta_paths)
    if bg_music_paths:
        all_input_files.extend(bg_music_paths)
    job_progress[job_id]['input_files'] = all_input_files

    # Generate all combinations
    end_cta_options = end_cta_paths if end_cta_paths else [None]
    bg_music_options = bg_music_paths + [None] if bg_music_paths else [None]

    processed_count = 0
    output_files = []

    try:
        for hook_path, middle_path, end_path, music_path in itertools.product(
                hook_paths, middle_cta_paths, end_cta_options, bg_music_options):

            processed_count += 1
            progress = int((processed_count / job_progress[job_id]['total']) * 100)

            hook_clip = None
            middle_clip = None
            end_clip = None
            final_clip = None

            try:
                hook_clip = VideoFileClip(hook_path)
                middle_clip = VideoFileClip(middle_path)
                clips = [hook_clip, middle_clip]

                if end_path:
                    end_clip = VideoFileClip(end_path)
                    clips.append(end_clip)

                final_clip = concatenate_videoclips(clips)

                # Add background music if provided
                if music_path:
                    bg_audio = AudioFileClip(music_path)
                    if bg_audio.duration < final_clip.duration:
                        repeats = int(final_clip.duration / bg_audio.duration) + 1
                        bg_audio = concatenate_audioclips([bg_audio] * repeats).subclip(0, final_clip.duration)
                    else:
                        bg_audio = bg_audio.subclip(0, final_clip.duration)

                    bg_audio = bg_audio.volumex(music_volume)

                    if final_clip.audio is not None:
                        final_audio = CompositeAudioClip([final_clip.audio, bg_audio])
                    else:
                        final_audio = bg_audio
                    final_clip = final_clip.set_audio(final_audio)

                # Generate output filename
                hook_name = os.path.basename(hook_path).rsplit('.', 1)[0]
                middle_name = os.path.basename(middle_path).rsplit('.', 1)[0]
                end_name = os.path.basename(end_path).rsplit('.', 1)[0] if end_path else "no-end"
                music_name = os.path.basename(music_path).rsplit('.', 1)[0] if music_path else "no-music"

                output_filename = f"{hook_name}_{middle_name}_{end_name}_{music_name}.mp4"
                output_path = os.path.join(job_output_dir, output_filename)

                final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
                output_files.append(output_filename)

            except Exception as clip_err:
                print(f"Error processing combination {processed_count}: {clip_err}")
                job_progress[job_id]['last_error'] = str(clip_err)

            finally:
                for c in [final_clip, end_clip, middle_clip, hook_clip]:
                    if c is not None:
                        try:
                            c.close()
                        except Exception:
                            pass

            job_progress[job_id].update({
                'progress': progress,
                'current': processed_count,
                'total': job_progress[job_id]['total'],
                'status': 'processing' if progress < 100 else 'complete',
                'output_files': output_files
            })

        # Mark job as complete (even if some combinations failed)
        if output_files:
            job_progress[job_id]['status'] = 'complete'
            job_progress[job_id]['progress'] = 100
        else:
            job_progress[job_id]['status'] = 'error'
            job_progress[job_id]['error'] = job_progress[job_id].get(
                'last_error', 'All combinations failed')

        # Clean up input files
        cleanup_input_files(job_id)

    except Exception as e:
        job_progress[job_id]['status'] = 'error'
        job_progress[job_id]['error'] = str(e)
        print(f"Error processing videos: {e}")

def cleanup_input_files(job_id):
    """Delete input files after job is complete to save disk space"""
    if job_id not in job_progress:
        return
    
    job_data = job_progress[job_id]
    if 'input_files' not in job_data:
        return
    
    # Get list of input files
    input_files = job_data['input_files']
    
    # Check if any other jobs are using these files
    files_in_use = set()
    for other_job_id, other_job_data in job_progress.items():
        if other_job_id != job_id and 'input_files' in other_job_data:
            files_in_use.update(other_job_data['input_files'])
    
    # Delete files that are not in use by other jobs
    deleted_count = 0
    for file_path in input_files:
        if file_path not in files_in_use and os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
                print(f"Deleted input file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    
    print(f"Cleanup complete for job {job_id}: {deleted_count} files deleted")

@app.route('/progress/<job_id>', methods=['GET'])
def get_progress(job_id):
    # Return the current progress from our job_progress dictionary
    if job_id in job_progress:
        return jsonify(job_progress[job_id])
    else:
        return jsonify({
            'progress': 0,
            'status': 'not_found',
            'error': 'Job not found'
        }), 404

@app.route('/download/<job_id>/<filename>', methods=['GET'])
def download_file(job_id, filename):
    job_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    return send_from_directory(job_output_dir, filename, as_attachment=True)

@app.route('/download-all/<job_id>', methods=['GET'])
def download_all(job_id):
    """Create a zip file of all generated videos for a job and send it to the client"""
    if job_id not in job_progress:
        return jsonify({'error': 'Job not found'}), 404
    
    job_data = job_progress[job_id]
    if job_data['status'] != 'complete':
        return jsonify({'error': 'Job is not complete yet'}), 400
    
    output_files = job_data['output_files']
    if not output_files:
        return jsonify({'error': 'No output files found'}), 404
    
    # Create a zip file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        job_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        for filename in output_files:
            file_path = os.path.join(job_output_dir, filename)
            if os.path.exists(file_path):
                zf.write(file_path, filename)
    
    # Seek to the beginning of the file
    memory_file.seek(0)
    
    # Send the zip file to the client
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'videos_{job_id}.zip'
    )

if __name__ == '__main__':
    app.run(debug=True)
