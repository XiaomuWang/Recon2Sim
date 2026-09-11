"""Use bundled Blender FFmpeg to encode the diagram as browser-compatible H264."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.fps=10;s.frame_start=1;s.frame_end=1201
ed=s.sequence_editor_create();ed.sequences.new_movie('Trajectory diagram',str(P/'preview/trajectory_replay_mp4v.mp4'),channel=1,frame_start=1)
s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='MEDIUM';s.render.ffmpeg.ffmpeg_preset='GOOD';s.render.ffmpeg.audio_codec='NONE'
s.view_settings.view_transform='Standard';s.render.filepath=str(P/'preview/trajectory_replay.mp4');bpy.ops.render.render(animation=True)
