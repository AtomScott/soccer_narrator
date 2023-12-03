import base64
import os

import cv2
from dotenv import load_dotenv
from openai import OpenAI
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
from pydub import AudioSegment
from moviepy.editor import AudioFileClip, VideoFileClip

from src.prompts import SINGLE_FRAME_FOCUS, SEQUENTIAL_NARRATION
from pathlib import Path


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


def generate_audio(text, output_dir, model="tts-1", voice="alloy"):
    api_key = load_openai_key()
    client = OpenAI(api_key=api_key)

    speech_file_path = Path(output_dir) / "speech.mp3"
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
