import gradio as gr
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import concatenate_videoclips
from gradio_rangeslider import RangeSlider

import glob
import os
import subprocess


def list_font_files():
    """List all .ttf files in /usr/share/fonts/truetype/."""
    font_dir = "/usr/share/fonts/truetype/"
    return [f for f in glob.glob(font_dir + "**/*.ttf", recursive=True)]

def overlay_text_on_video(video_path, text, color, size, position, time_range, font_file, use_background, bg_color):
    """Overlay text on a video using FFmpeg."""
    # Generate output path
    output_path = "/tmp/processed_video.mp4"
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Convert RGBA or RGB to hex
    def rgba_to_hex(rgba):
        # Extract RGB values and convert to integers
        if rgba is None:
            return None
        print(rgba)
        rgb = rgba.strip("rgba()").split(",")[:3]
        rgb = [int(float(c)) for c in rgb]
        return "#{:02x}{:02x}{:02x}".format(*rgb)
    
    # Convert colors to hex
    hex_color = rgba_to_hex(color)
    hex_bg_color = rgba_to_hex(bg_color) if use_background else None
    
    # Define position mappings
    position_mappings = {
        "top": "x=(w-text_w)/2:y=10",
        "top left": "x=10:y=10",
        "top right": "x=w-text_w-10:y=10",
        "bottom": "x=(w-text_w)/2:y=h-text_h-10",
        "bottom left": "x=10:y=h-text_h-10",
        "bottom right": "x=w-text_w-10:y=h-text_h-10",
        "center": "x=(w-text_w)/2:y=(h-text_h)/2"
    }
    
    if hex_bg_color is not None:
        # Text box style
        box_param = f":box=1:boxcolor={hex_bg_color}@0.5:boxborderw=10" if use_background else ""        
    else: 
        box_param =""

    # Construct the drawtext filter
    drawtext_filter = (
        f"drawtext=fontfile='{font_file}':text='{text}':"
        f"fontcolor={hex_color}:fontsize={size}:{position_mappings[position]}{box_param}"
    )
    
    # Get FFmpeg command
    ffmpeg_command = [
        "ffmpeg", "-i", video_path, "-vf", drawtext_filter,
        "-codec:a", "copy", output_path
    ]
    
    try:
        # Run the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        return output_path, "Video processing complete."
    except subprocess.CalledProcessError as e:
        return None, f"Error processing video: {str(e)}"



def get_video_duration(video_path):
    """Get the duration of the uploaded video."""
    clip = VideoFileClip(video_path)
    duration = clip.duration
    clip.close()
    return duration

def update_slider_range(video_path):
    """Update the RangeSlider based on the uploaded video's duration."""
    duration = get_video_duration(video_path)
    return gr.update(value=(0, duration), minimum=0, maximum=duration)

def process_video(video_path, trim_range, action):
    """Process the video based on the selected action (trim or delete)."""
    start, end = trim_range
    clip = VideoFileClip(video_path)
    
    if action == "Trim":
        # Keep only the selected range
        trimmed_clip = clip.subclip(start, end)
        output_path = "/tmp/trimmed_video.mp4"
        trimmed_clip.write_videofile(output_path, codec="libx264")
        trimmed_clip.close()
    elif action == "Delete":
        # Delete the selected range and keep the remaining parts
        before_clip = clip.subclip(0, start) if start > 0 else None
        after_clip = clip.subclip(end, clip.duration) if end < clip.duration else None
        
        if before_clip and after_clip:
            result_clip = concatenate_videoclips([before_clip, after_clip])
        elif before_clip:
            result_clip = before_clip
        elif after_clip:
            result_clip = after_clip
        else:
            result_clip = None

        output_path = "/tmp/modified_video.mp4"
        if result_clip:
            result_clip.write_videofile(output_path, codec="libx264")
            result_clip.close()
    else:
        output_path = None

    clip.close()
    return output_path, f"Action: {action}, Range: Start={start}s, End={end}s"

# Gradio interface
with gr.Blocks() as app: 
    gr.Markdown("## Video Editor with Trim, Delete and add Text !")
    
    # Video uploader
    video_input = gr.Video(label="Upload Your Video")
        
    with gr.Tab("Edit"):
        # RangeSlider for time range
        range_slider = RangeSlider(
            label="Select Time Range",
            value=(0, 1),  # Default value
            minimum=0,
            maximum=1,     # Default range
            step=0.1
        )
        
        # Dropdown for selecting action
        action_selector = gr.Dropdown(
            choices=["Trim", "Delete"],
            label="Choose Action",
            value="Trim"
        )
        
        # Button to perform the action
        action_button = gr.Button("Process Video")
    
    with gr.Tab("Text..."):
        # Text input
        text_input = gr.Textbox(label="Text to Overlay")
        
        # Color picker
        color_picker = gr.ColorPicker(label="Text Color", value="#FFFFFF")
        
        # Font size slider
        font_size = gr.Slider(label="Font Size", minimum=10, maximum=100, value=24, step=1)
        
        # Placement dropdown
        placement_dropdown = gr.Dropdown(
            label="Text Placement",
            choices=["top", "top left", "top right", "bottom", "bottom left", "bottom right", "center"],
            value="top"
        )
        
        # Font file dropdown
        font_dropdown = gr.Dropdown(
            label="Font File",
            choices=list_font_files(),
            value=list_font_files()[0] if list_font_files() else None
        )
        
        # Checkbox for background
        use_background = gr.Checkbox(label="Add Background to Text", value=False)
        background_color_picker = gr.ColorPicker(label="Background Color", value="#000000", interactive=True)
        
        # Process button
        process_button = gr.Button("Process Video")
           # Connect the processing function
    
    # Output fields
    output_video = gr.Video(label="Processed Video")
    output_text = gr.Textbox(label="Processing Details")
    
    # Update slider range when a video is uploaded
    video_input.change(
        fn=update_slider_range,
        inputs=video_input,
        outputs=range_slider,
    )
    
    # Process video based on action
    action_button.click(
        fn=process_video,
        inputs=[video_input, range_slider, action_selector],
        outputs=[output_video, output_text],
    )

    # Text Process video based on action
    process_button.click(
            overlay_text_on_video,
            inputs=[video_input, text_input, color_picker, font_size, placement_dropdown, font_dropdown, use_background, background_color_picker],
            outputs=[output_video, output_text]
        )

# Launch the app
app.launch()

