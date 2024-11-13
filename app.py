import gradio as gr
from moviepy.video.io.VideoFileClip import VideoFileClip

def get_video_duration(video_path):
    """Get the duration of the uploaded video."""
    clip = VideoFileClip(video_path)
    duration = clip.duration
    clip.close()
    return duration

def trim_video(video_path, start, end):
    """Trim the video based on start and end times."""
    clip = VideoFileClip(video_path)

    # Ensure start and end times are within the video duration
    duration = clip.duration
    start = max(0, min(start, duration))
    end = max(start, min(end, duration))

    # Trim the video
    trimmed_clip = clip.subclip(start, end)
    
    # Save the trimmed video
    output_path = "/tmp/trimmed_video.mp4"
    trimmed_clip.write_videofile(output_path, codec="libx264")
    trimmed_clip.close()
    
    # Return the path to the trimmed video
    return output_path

def update_sliders(video_path):
    """Update slider ranges based on video duration."""
    duration = get_video_duration(video_path)
    return gr.update(value=0, minimum=0, maximum=duration), gr.update(value=duration, minimum=0, maximum=duration), duration

# Gradio interface
with gr.Blocks() as app:
    gr.Markdown("## Video Trimmer")

    # Video upload input
    video_input = gr.Video(label="Upload your video")

    # Dynamic sliders for setting start and end times
    start_time = gr.Slider(label="Start Time (seconds)")
    end_time = gr.Slider(label="End Time (seconds)")

    # Display video duration (for reference) and set sliders
    video_duration = gr.Number(label="Video Duration (seconds)", interactive=False)
    video_input.change(fn=update_sliders, inputs=video_input, outputs=[start_time, end_time, video_duration])

    # Button to trigger trimming
    trim_button = gr.Button("Trim Video")
    
    # Display output video
    output_video = gr.Video(label="Trimmed Video Output")

    # Set up the trimming action when button is clicked
    trim_button.click(
        trim_video,
        inputs=[video_input, start_time, end_time],
        outputs=output_video,
    )

# Launch the app
app.launch()

