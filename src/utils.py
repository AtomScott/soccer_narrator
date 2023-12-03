import base64
import os
import subprocess
from pathlib import Path

import cv2
from dotenv import load_dotenv
from moviepy.editor import (
    AudioFileClip,
    VideoFileClip,
)
from openai import OpenAI
from pycaption import Caption, CaptionNode, CaptionSet, SRTWriter
from pydub import AudioSegment
from pytube import YouTube

from src.prompts import SEQUENTIAL_NARRATION, SINGLE_FRAME_FOCUS


def get_video_length(video_path):
    clip = VideoFileClip(video_path)
    return clip.duration


def download_youtube_video(youtube_url, output_dir):
    youtube = YouTube(youtube_url)

    video_path = (
        youtube.streams.filter(progressive=True, file_extension="mp4")
        .order_by("resolution")
        .desc()
        .first()
        .download(output_path=output_dir)
    )
    return video_path


def process_video(video_path):
    base64Frames = []
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

    cap.release()
    return base64Frames


def load_openai_key():
    load_dotenv()

    openai_key = os.getenv("OPENAI_KEY")

    if openai_key is None:
        openai_key = input("Please enter your OpenAI key: ")

    return openai_key


def create_content(base64_image=None, prompt=None, detail="low"):
    content = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    if base64_image:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": detail,
                },
            }
        )
    return content


def create_prompt_messages(content):
    return [{"role": "user", "content": content}]


def call_openai_api(prompt_messages, model="gpt-4-vision-preview", max_tokens=300):
    api_key = load_openai_key()
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=prompt_messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def generate_descriptions(
    base64Frames,
    frame_sampling_rate=100,
    prompt=SINGLE_FRAME_FOCUS,
    detail="low",
):
    descriptions = []
    for i, frame in enumerate(base64Frames[0::frame_sampling_rate]):
        content = create_content(base64_image=frame, prompt=prompt, detail=detail)
        prompt_messages = create_prompt_messages(content)
        description = call_openai_api(prompt_messages)
        descriptions.append(f"Frame {i * frame_sampling_rate}: {description}")

    return "\n".join(descriptions)


def generate_narration(
    descriptions,
    prompt=SEQUENTIAL_NARRATION,
    max_tokens=300,
):
    content = create_content(prompt=prompt + descriptions)
    prompt_messages = create_prompt_messages(content)
    voiceover_narration = call_openai_api(prompt_messages, max_tokens=max_tokens)
    return voiceover_narration


def generate_audio(text, output_path, model="tts-1", voice="alloy"):
    api_key = load_openai_key()
    client = OpenAI(api_key=api_key)

    speech_file_path = Path(output_path)
    response = client.audio.speech.create(model=model, voice=voice, input=text)

    response.stream_to_file(speech_file_path)
    return speech_file_path


def overlay_audio_on_video(video_path, audio_path, output_path):
    video_clip = VideoFileClip(str(video_path))
    audio_clip = AudioFileClip(str(audio_path))

    speed_factor = audio_clip.duration / video_clip.duration

    audio_clip = AudioSegment.from_file(audio_path)
    audio_clip = audio_clip.speedup(playback_speed=speed_factor)

    temp_audio_path = "/tmp/temp_audio.wav"
    audio_clip.export(temp_audio_path, format="wav")

    audio_clip = AudioFileClip(temp_audio_path)

    audio_clip = audio_clip.set_duration(video_clip.duration)

    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_path, codec="libx264")
    return output_path


def generate_subtitles(
    text, video_length, output_path, num_chars_per_line=50, language="en-US"
):
    captions = CaptionSet({language: []})

    words = (
        text if language == "ja-JP" else text.split(" ")
    )  # Japanese doesn't use spaces between words
    word_time = video_length / len(words)
    current_time = 0
    line_length = 0
    line_start_time = 0
    line_words = []

    for i, word in enumerate(words):
        word_length = len(word)
        if (
            line_length + word_length > num_chars_per_line
            or current_time >= video_length
            or i == len(words) - 1
        ):
            # Create a new caption for the line
            start_time = line_start_time * 1000000  # Convert to milliseconds
            end_time = current_time * 1000000  # Convert to milliseconds
            caption_text = " ".join(line_words)
            captions.get_captions(language).append(
                Caption(start_time, end_time, [CaptionNode.create_text(caption_text)])
            )

            # Reset line variables
            line_length = 0
            line_start_time = current_time
            line_words = []

        line_words.append(word)
        line_length += word_length + 1  # Add 1 for the space
        current_time += word_time
        # print(current_time, line_length, word)

    # Write the captions to a .srt file
    with open(output_path, "w") as f:
        f.write(SRTWriter().write(captions))

    return output_path


def add_subtitles_to_video(video_path, srt_file, output_path):
    command = f'ffmpeg -y -i {video_path} -vf "subtitles={srt_file}" {output_path}'
    subprocess.run(command, shell=True, check=True)
