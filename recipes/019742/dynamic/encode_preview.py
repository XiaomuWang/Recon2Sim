import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.fps=15
ed=s.sequence_editor_create();clip=ed.sequences.new_movie('Trajectory diagram',str(P/'preview/trajectory_intermediate.avi'),channel=1,frame_start=1)
s.frame_start=1;s.frame_end=int(clip.frame_final_end)-1;s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='MEDIUM';s.render.filepath=str(P/'preview/UrbanBrake019742_TrajectoryPreview.mp4');s.render.threads_mode='FIXED';s.render.threads=4
bpy.ops.render.render(animation=True)
