bl_info = {
    "name": "Sequence File Menu",
    "author": "tintwotin, Meta Person",
    "version": (1, 7),
    "blender": (5, 2, 0),
    "location": "Video Sequence Editor > Menu > Sequence",
    "description": "File Operations for the Sequencer",
    "category": "Sequencer",
}

import bpy, os, re
from bpy_extras.io_utils import ExportHelper
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from pathlib import Path

# UI layout panel elements imported from standard Blender UI
from bl_ui.properties_output import RENDER_PT_format
from bl_ui.properties_output import RENDER_PT_encoding
from bl_ui.properties_output import RENDER_PT_encoding_video
from bl_ui.properties_output import RENDER_PT_encoding_audio
from bl_ui.properties_output import RENDER_PT_frame_range
from bl_ui.properties_output import RENDER_PT_time_stretching
from bl_ui.properties_output import RENDER_PT_post_processing
from bl_ui.properties_output import RENDER_PT_output_color_management
from bl_ui.properties_output import RENDER_PT_output_views

audio_extensions = [
    ".wav",
    ".ogg",
    ".oga",
    ".mp3",
    ".mp2",
    ".ac3",
    ".aac",
    ".flac",
    ".wma",
    ".eac3",
    ".aif",
    ".aiff",
    ".m4a",
    ".mka"
]

image_extensions = [
    ".png",
    ".tga",
    ".bmp",
    ".jpg",
    ".jpeg",
    ".sgi",
    ".rgb",
    ".rgba",
    ".tif",
    ".tiff",
    ".tx",
    ".jp2",
    ".j2c",
    ".hdr",
    ".dds",
    ".dpx",
    ".cin",
    ".exr",
    ".psd",
    ".pdd",
    ".psb",
    ".webp"
]

video_extensions = [
    ".avi",
    ".flc",
    ".mov",
    ".movie",
    ".mp4",
    ".m4v",
    ".m2v",
    ".m2t",
    ".m2ts",
    ".mts",
    ".ts",
    ".mv",
    ".avs",
    ".wmv",
    ".ogv",
    ".r3d",
    ".dv",
    ".mpeg",
    ".mpg",
    ".mpg2",
    ".vob",
    ".mkv",
    ".flv",
    ".divx",
    ".xvid",
    ".mxf",
    ".gif",
    ".webm"
]

text_extensions = [
    ".txt",
]

valid_extensions = image_extensions + video_extensions + audio_extensions + text_extensions
delimiter = ";*"
valid_extensions_str = delimiter.join(valid_extensions)


def export_file(context, filepath):
    dirname = os.path.dirname(filepath)
    filename = os.path.splitext(filepath)[0]
    context.scene.render.filepath = os.path.join(dirname, filename)
    bpy.ops.render.opengl(animation=True, sequencer=True)
    return {"FINISHED"}


class SEQUENCER_PT_export_browser(Operator, ExportHelper):
    """Export the sequence with audio"""

    bl_idname = "sequencer.export"
    bl_label = "Export"
    filename_ext = "."
    use_filter_movie = True
    use_filter_image = True
    filter_glob: StringProperty(default=valid_extensions_str, options={"HIDDEN"}, maxlen=255)
    auto_range: bpy.props.BoolProperty(name='Auto Range', description='Set the range to include the imported strips', default=True)

    def draw(self, context):
        # Override default draw to prevent properties displaying outside panels
        pass

    def execute(self, context):
        if self.auto_range:
            selection = context.selected_strips
            bpy.ops.sequencer.select_all(action='SELECT')
            bpy.ops.sequencer.set_range_to_strips()
            bpy.ops.sequencer.select_all(action='DESELECT')
            for s in selection: 
                s.select = True
        
        return export_file(context, self.filepath)


class SEQUENCER_PT_export(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Export Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator and operator.bl_idname == "SEQUENCER_OT_export"

    def invoke(self, context, event):
        context.scene.render.use_sequencer = True

    def draw(self, context):
        layout = self.layout
        window = context.window
        screen = context.screen

        # If statusbar is hidden, still show messages at the top
        if not screen.show_statusbar:
            layout.template_reports_banner()
            layout.template_running_jobs()

        # Workspace scene configuration selector drawn on top inside the Export panel
        layout.template_ID(window, "scene", new="scene.new", unlink="scene.delete")
        layout.separator()


class SEQUENCER_PT_export_format(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Format"
    bl_parent_id = "SEQUENCER_PT_export"

    def draw(self, context):
        RENDER_PT_format.draw(self, context)


class SEQUENCER_PT_export_image(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Output"
    bl_parent_id = "SEQUENCER_PT_export"

    def draw(self, context):
        layout = self.layout
        rd = context.scene.render
        image_settings = rd.image_settings

        layout.use_property_split = True

        col = layout.column(heading="Saving")
        col.prop(rd, "use_file_extension")
        col.prop(rd, "use_render_cache")

        layout.template_image_settings(image_settings, color_management=False)

        if not rd.is_movie_format:
            col = layout.column(heading="Image Sequence")
            col.prop(rd, "use_overwrite")
            col.prop(rd, "use_placeholder")


class SEQUENCER_PT_export_color_management(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Color Management"
    bl_parent_id = "SEQUENCER_PT_export_image"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        RENDER_PT_output_color_management.draw(self, context)


class SEQUENCER_PT_export_encoding(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Encoding"
    bl_parent_id = "SEQUENCER_PT_export_image"

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.image_settings.file_format in {"FFMPEG", "XVID", "H264", "THEORA"}

    def draw(self, context):
        RENDER_PT_encoding.draw(self, context)


class SEQUENCER_PT_export_encoding_video(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Video"
    bl_parent_id = "SEQUENCER_PT_export_encoding"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        rd = context.scene.render
        if rd.image_settings.file_format in {"FFMPEG", "XVID", "H264", "THEORA"}:
            ffmpeg = context.scene.render.ffmpeg

            needs_codec = ffmpeg.format in {
                "AVI",
                "QUICKTIME",
                "MKV",
                "OGG",
                "MPEG4",
                "WEBM",
            }
            if needs_codec:
                layout.prop(ffmpeg, "codec")
            if needs_codec and ffmpeg.codec == "NONE":
                return
            if ffmpeg.codec == "DNXHD":
                layout.prop(ffmpeg, "use_lossless_output")
            
            use_crf = needs_codec and ffmpeg.codec in {"H264", "MPEG4", "WEBM", "AV1"}
            if use_crf:
                layout.prop(ffmpeg, "constant_rate_factor")
            
            layout.prop(ffmpeg, "ffmpeg_preset")
            layout.prop(ffmpeg, "gopsize")
            
            row = layout.row(align=True, heading="Max B-frames")
            row.prop(ffmpeg, "use_max_b_frames", text="")
            sub = row.row(align=True)
            sub.active = ffmpeg.use_max_b_frames
            sub.prop(ffmpeg, "max_b_frames", text="")

            if not use_crf or ffmpeg.constant_rate_factor == "NONE":
                col = layout.column()

                sub = col.column(align=True)
                sub.prop(ffmpeg, "video_bitrate")
                sub.prop(ffmpeg, "minrate", text="Minimum")
                sub.prop(ffmpeg, "maxrate", text="Maximum")

                col.prop(ffmpeg, "buffersize", text="Buffer")
                col.separator()

                col.prop(ffmpeg, "muxrate", text="Mux Rate")
                col.prop(ffmpeg, "packetsize", text="Mux Packet Size")


class SEQUENCER_PT_export_audio(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Audio"
    bl_parent_id = "SEQUENCER_PT_export_encoding"

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.image_settings.file_format in {"FFMPEG", "XVID", "H264", "THEORA"}

    def draw(self, context):
        RENDER_PT_encoding_audio.draw(self, context)


class SEQUENCER_PT_export_frame_range(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Frame Range"
    bl_parent_id = "SEQUENCER_PT_export"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sfile = context.space_data
        operator = sfile.active_operator
        
        # Display Auto Range here inside the Frame Range fold-out panel
        if operator and hasattr(operator, "auto_range"):
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout.prop(operator, "auto_range")
            layout.separator()

        RENDER_PT_frame_range.draw(self, context)


class SEQUENCER_PT_export_time_stretching(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Time Stretching"
    bl_parent_id = "SEQUENCER_PT_export_frame_range"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        RENDER_PT_time_stretching.draw(self, context)


class SEQUENCER_PT_export_post_processing(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Post Processing"
    bl_parent_id = "SEQUENCER_PT_export"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        RENDER_PT_post_processing.draw(self, context)


def menu_func_export(self, context):
    self.layout.operator("sequencer.export", text="Sequencer Export")


def find_first_empty_channel(start_frame, end_frame):
    scene = bpy.context.sequencer_scene
    if not scene or not scene.sequence_editor:
        return 1
    sequences = scene.sequence_editor.sequences_all
    for ch in range(1, len(sequences) + 1):
        for seq in sequences:
            if (
                seq.channel == ch
                and seq.frame_final_start < end_frame
                and (seq.frame_final_start + seq.frame_final_duration) > start_frame
            ):
                break
        else:
            return ch
    return 1


class SEQUENCER_OT_import_strips(bpy.types.Operator, ImportHelper):
    bl_description = 'Import multiple strips of mixed types'
    bl_idname = 'sequencer.import_strips'
    bl_label = 'Import'

    files: bpy.props.CollectionProperty(name='Import Strips', type=bpy.types.OperatorFileListElement)

    insert_method: bpy.props.EnumProperty(name='Insert Position',
                description='Insert method',
                items=[('PLAYHEAD', 'Playhead', 'Insert at playhead position'),
                       ('APPEND', 'Append', 'Append strips to the end of sequence')],
                 default='PLAYHEAD')

    channel: bpy.props.IntProperty(name='Channel', description='Assign channel to put strips', default=1, min=1)

    relative_path: bpy.props.BoolProperty(name='Relative Path', description='Use a relative path', default=False)

    fit_method: bpy.props.EnumProperty(name='Fit Method',
                description='Scale fit method',
                items=[('FIT', 'Scale to Fit', 'Scale image to fit within the canvas'),
                       ('FILL', 'Scale to Fill', 'Scale image to completely fill the canvas'),
                       ('STRETCH', 'Stretch to Fill', 'Stretch image to fill the canvas'),
                       ('ORIGINAL', 'Use Original Size', 'Keep image at its original size')],
                default='FIT')
    
    order_by: bpy.props.EnumProperty(name='Import Order',
                description='Strips are sorted by this order',
                items=[('PICK', 'Pick', 'No Sort, as selected order'),
                       ('CREATE_TIME', 'File Create Time', 'Sort order by the file created time'),
                       ('FILE_NAME', 'File Name', 'Sort order by the file name'),
                       ('FILE_SIZE', 'File Size', 'Sort order by the file size')],
                default='FILE_NAME')

    reversed_order: bpy.props.BoolProperty(name='Reversed Order', description='Reversed order for sorting', default=False)

    image_strip_length: bpy.props.IntProperty(name='Image Duration', description='Image strip length', default=75, min=1)

    use_placeholders: bpy.props.BoolProperty(name='Image Placeholders', description='Use placeholders for missing images', default=True)

    adjust_playback_rate: bpy.props.BoolProperty(name='Adjust Strip FPS', description='Play at normal speed regardless of scene FPS', default=True)

    use_framerate: bpy.props.BoolProperty(name='Override Scene FPS', description='Set the scene frame rate according to framerate of Movie strip', default=True)

    set_view_transform: bpy.props.BoolProperty(name='Set View Transform', description='Set appropriate view transform based on media color space', default=True)

    add_sound: bpy.props.BoolProperty(name='Import Sound', description='Import sound for Movie strips', default=True)
    mono: bpy.props.BoolProperty(name='Mix to Mono', description='Mix sound channels to mono', default=False)
    cache: bpy.props.BoolProperty(name='Cache Sound', description='Cache the sound of Sound strips', default=False)
    
    auto_range: bpy.props.BoolProperty(name='Adjust Range', description='Set the range to include the imported strips', default=True)

    # Exposed options from SEQUENCER_OT_image_strip_add
    move_strips: bpy.props.BoolProperty(name='Move Strips', description='Automatically begin translating strips with the mouse after adding them to the timeline', default=False)
    
    image_import_type: bpy.props.EnumProperty(name='Import As',
                description='Mode for importing selected images',
                items=[('DETECT', 'Auto Detect', 'Add images as individual strips, unless their filenames match Blenders numbered sequence pattern'),
                       ('SEQUENCE', 'Image Sequence', 'Import all selected images as a single image sequence'),
                       ('INDIVIDUAL', 'Individual Images', 'Add each selected image as an individual strip')],
                default='DETECT')

    filter_glob: StringProperty(default=valid_extensions_str, options={"HIDDEN"}, maxlen=255)

    @classmethod
    def poll(cls, context):
        scene = context.sequencer_scene
        return scene is not None

    def draw(self, context):
        # Override default draw to prevent duplicate rendering of properties above the panels
        pass

    def execute(self, context):
        if not context.sequencer_scene.sequence_editor:
            context.sequencer_scene.sequence_editor_create()

        seq_editor = context.sequencer_scene.sequence_editor
        
        strip_dirname = os.path.dirname(self.filepath)
        if not self.relative_path:
            strip_dirname = os.path.abspath(strip_dirname)
        strip_files = self.files

        # Sort the list based on user settings
        if self.order_by == 'PICK':
            if self.reversed_order:
                strip_files = reversed(strip_files)
            else:
                strip_files = list(strip_files)
        elif self.order_by == 'CREATE_TIME':
            strip_files = sorted(strip_files, key=lambda x: os.path.getctime(os.path.join(strip_dirname, x.name)), reverse=self.reversed_order)
        elif self.order_by == 'FILE_NAME':
            strip_files = sorted(strip_files, key=lambda x: x.name, reverse=self.reversed_order)
        elif self.order_by == 'FILE_SIZE':
            strip_files = sorted(strip_files, key=lambda x: os.path.getsize(os.path.join(strip_dirname, x.name)), reverse=self.reversed_order)
        else:
            return {'CANCELLED'}

        count_movie = 0
        count_sound = 0
        count_image = 0
        count_text = 0
        
        imported_strips = []
        empty_channel = find_first_empty_channel(0, 10000000000)

        # Categorize sorted input list
        movie_files = []
        sound_files = []
        image_files = []
        text_files = []

        for strip_file in strip_files:
            strip_ext = os.path.splitext(strip_file.name)[1].lower()
            if strip_ext in video_extensions:
                movie_files.append(strip_file)
            elif strip_ext in audio_extensions:
                sound_files.append(strip_file)
            elif strip_ext in image_extensions:
                image_files.append(strip_file)
            elif strip_ext in text_extensions:
                text_files.append(strip_file)

        # Dynamic positioning helper
        def get_next_placement(imported_strips):
            if self.insert_method == "APPEND":
                current_strips = seq_editor.sequences_all if (seq_editor and seq_editor.sequences_all) else []
                all_ends = [seq.frame_final_end for seq in current_strips] + [seq.frame_final_end for seq in imported_strips]
                frame_start = max(all_ends) if all_ends else 0
                channel = self.channel
            else:  # "PLAYHEAD"
                if any(seq.frame_final_end for seq in imported_strips):
                    frame_start = max([seq.frame_final_end for seq in imported_strips] or [context.sequencer_scene.frame_current])
                    channel = max(self.channel, empty_channel) 
                else:
                    frame_start = context.sequencer_scene.frame_current
                    channel = self.channel
            return frame_start, channel

        # 1. Process Movie Files
        for movie_file in movie_files:
            strip_path = os.path.join(strip_dirname, movie_file.name)
            if not self.relative_path:
                strip_path = os.path.abspath(strip_path)
            
            frame_start, channel = get_next_placement(imported_strips)
            bpy.ops.sequencer.movie_strip_add(filepath=strip_path,
                                              frame_start=frame_start,
                                              channel=channel,
                                              fit_method=self.fit_method,
                                              set_view_transform=self.set_view_transform,
                                              adjust_playback_rate=self.adjust_playback_rate,
                                              sound=self.add_sound,
                                              use_framerate=self.use_framerate,
                                              relative_path=self.relative_path,
                                              overlap=False,
                                              move_strips=self.move_strips,
                                              )
            count_movie += 1
            new_strip = context.sequencer_scene.sequence_editor.active_strip
            if new_strip:
                imported_strips.append(new_strip)

        # 2. Process Sound Files
        for sound_file in sound_files:
            strip_path = os.path.join(strip_dirname, sound_file.name)
            if not self.relative_path:
                strip_path = os.path.abspath(strip_path)
            
            frame_start, channel = get_next_placement(imported_strips)
            bpy.ops.sequencer.sound_strip_add(filepath=strip_path,
                                              frame_start=frame_start,
                                              channel=channel,
                                              cache=self.cache,
                                              mono=self.mono,
                                              relative_path=self.relative_path,
                                              overlap=False,
                                              )
            count_sound += 1
            new_strip = context.sequencer_scene.sequence_editor.active_strip
            if new_strip:
                imported_strips.append(new_strip)

        # 3. Process Text Files
        for text_file in text_files:
            strip_path = os.path.join(strip_dirname, text_file.name)
            if not self.relative_path:
                strip_path = os.path.abspath(strip_path)
            
            frame_start, channel = get_next_placement(imported_strips)
            bpy.ops.sequencer.effect_strip_add(type='TEXT',
                                              frame_start=frame_start,
                                              length=self.image_strip_length,
                                              channel=channel,
                                              move_strips=self.move_strips,
                                              )
            count_text += 1
            new_strip = context.sequencer_scene.sequence_editor.active_strip
            if new_strip:
                new_strip.frame_final_duration = self.image_strip_length
                with open(strip_path) as f:
                    content = f.read()
                new_strip.text = content
                imported_strips.append(new_strip)

        # 4. Process Image Files using the specified import behavior
        if image_files:
            if self.image_import_type == 'INDIVIDUAL':
                for image_file in image_files:
                    frame_start, channel = get_next_placement(imported_strips)
                    bpy.ops.sequencer.image_strip_add(directory=strip_dirname + os.sep, 
                                                      files=[{"name": image_file.name}],
                                                      show_multiview=False,
                                                      frame_start=frame_start,
                                                      length=self.image_strip_length,
                                                      channel=channel,
                                                      fit_method=self.fit_method,
                                                      set_view_transform=self.set_view_transform,
                                                      use_placeholders=self.use_placeholders,
                                                      relative_path=self.relative_path,
                                                      overlap=False,
                                                      move_strips=self.move_strips,
                                                      image_import_type='INDIVIDUAL'
                                                      )               
                    count_image += 1
                    new_strip = context.sequencer_scene.sequence_editor.active_strip
                    if new_strip:
                        new_strip.frame_final_duration = self.image_strip_length
                        imported_strips.append(new_strip)
            else:
                # SEQUENCE or DETECT mode processing
                frame_start, channel = get_next_placement(imported_strips)
                bpy.ops.sequencer.image_strip_add(directory=strip_dirname + os.sep, 
                                                  files=[{"name": f.name} for f in image_files],
                                                  show_multiview=False,
                                                  frame_start=frame_start,
                                                  channel=channel,
                                                  fit_method=self.fit_method,
                                                  set_view_transform=self.set_view_transform,
                                                  use_placeholders=self.use_placeholders,
                                                  relative_path=self.relative_path,
                                                  overlap=False,
                                                  move_strips=self.move_strips,
                                                  image_import_type=self.image_import_type
                                                  )               
                count_image += 1
                new_strip = context.sequencer_scene.sequence_editor.active_strip
                if new_strip:
                    imported_strips.append(new_strip)

        if self.auto_range:
            selection = context.selected_strips
            bpy.ops.sequencer.select_all(action='SELECT')
            bpy.ops.sequencer.set_range_to_strips()
            bpy.ops.sequencer.select_all(action='DESELECT')
            for s in selection: 
                s.select = True  
                                                  
        self.report({'INFO'}, 'Imported Movie[{}], Sound[{}], Image[{}], Text[{}], Total[{}]'.format(count_movie,
                                                                                           count_sound,
                                                                                           count_image,
                                                                                           count_text,
                                                                                           count_movie + count_sound + count_image + count_text))

        return {'FINISHED'}


class SEQUENCER_PT_import_strips(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Import Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator and operator.bl_idname == "SEQUENCER_OT_import_strips"

    set_default_filter_settings: bool = True
    def draw(self, context):
        if SEQUENCER_PT_import_strips.set_default_filter_settings:
            context.space_data.params.use_filter = True        # enable Filter
            context.space_data.params.use_filter_movie = True  # set movie filter as default
            context.space_data.params.use_filter_image = True  # set movie filter as default
            context.space_data.params.use_filter_sound = True  # set movie filter as default
            SEQUENCER_PT_import_strips.set_default_filter_settings = False
            
        layout = self.layout
        window = context.window
        screen = context.screen

        # If statusbar is hidden, still show messages at the top
        if not screen.show_statusbar:
            layout.template_reports_banner()
            layout.template_running_jobs()

        # Workspace scene configuration selector drawn on top inside the Import panel
        layout.template_ID(window, "scene", new="scene.new", unlink="scene.delete")
        layout.separator()

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        prefs = context.preferences
        system = prefs.system

        sfile = context.space_data
        operator = sfile.active_operator

        if not operator:
            return

        # General
        box = layout.box()
        box = box.column(align=True)
        box.label(text="Placement & Sorting", icon="FILE_TICK")
        box.prop(operator, "insert_method")
        box.prop(operator, "channel")
        box.prop(operator, "relative_path")
        box.prop(operator, "auto_range")
        box.prop(operator, "move_strips")
        box.separator()

        box = box.column(align=True)      
        box.prop(operator, "order_by")
        box.prop(operator, "reversed_order")
        box.separator()

        # Movie Settings
        box = layout.box()
        box = box.column(align=True)
        box.label(text="Movie Settings", icon="FILE_MOVIE")
        box.prop(system, "sequencer_proxy_setup")
        box.prop(operator, "adjust_playback_rate")
        box.prop(operator, "use_framerate")
        box.prop(operator, "add_sound")

        # Image Settings (Exposing the requested image-specific parameters)
        box = layout.box()
        box = box.column(align=True)
        box.label(text="Image / Sequence Settings", icon="IMAGE_DATA")
        box.prop(operator, "image_import_type")
        box.prop(operator, "fit_method")
        box.prop(operator, "set_view_transform")
        box.prop(operator, "image_strip_length")
        box.prop(operator, "use_placeholders")
        
        # Sound Settings
        box = layout.box()
        box = box.column(align=True)
        box.label(text="Sound Settings", icon="FILE_SOUND")
        box.prop(operator, "mono")
        box.prop(operator, "cache")        


class SEQUENCER_MT_sequence(bpy.types.Menu):
    bl_idname = "SEQUENCER_MT_sequence"
    bl_label = "Sequence"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("sequencer.refresh_all", text="Refresh All")
        layout.operator_context = "INVOKE_DEFAULT"

        layout.separator()
        layout.operator("sequencer.import_strips", text="Import Media")

        layout.separator()
        layout.operator("sequencer.export", text="Export Sequence")
        layout.operator("sound.mixdown", text="Export Audio")
        layout.operator("sequencer.export_subtitles", text="Export Subtitles")

        layout.separator()
        layout.operator("render.opengl", text="Render Frame").sequencer = True


def prepend_sequence_menu(self, context):
    self.layout.menu("SEQUENCER_MT_sequence")


classes = (
    SEQUENCER_PT_export,
    SEQUENCER_PT_export_format,
    SEQUENCER_PT_export_image,
    SEQUENCER_PT_export_color_management,
    SEQUENCER_PT_export_encoding,
    SEQUENCER_PT_export_encoding_video,
    SEQUENCER_PT_export_audio,
    SEQUENCER_PT_export_frame_range,
    SEQUENCER_PT_export_time_stretching,
    SEQUENCER_PT_export_post_processing,
    SEQUENCER_PT_export_browser,
    SEQUENCER_OT_import_strips,
    SEQUENCER_PT_import_strips,
    SEQUENCER_MT_sequence,
)


def register():
    # Force clean up of any previously registered 'SEQUENCER_PT_scene_selector'
    # class that might be lingering in the active Blender session context.
    try:
        if hasattr(bpy.types, "SEQUENCER_PT_scene_selector"):
            bpy.utils.unregister_class(bpy.types.SEQUENCER_PT_scene_selector)
    except Exception as e:
        print("Could not clean up duplicate SEQUENCER_PT_scene_selector:", e)

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.SEQUENCER_MT_editor_menus.prepend(prepend_sequence_menu)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.SEQUENCER_MT_editor_menus.remove(prepend_sequence_menu)


if __name__ == "__main__":
    register()
