bl_info = {
    "name": "Sequence File Menu",
    "author": "tintwotin",
    "version": (1, 0),
    "blender": (3, 4, 0),
    "location": "Video Sequence Editor > Menu > Sequence",
    "description": "File Operations for the Sequencer",
    "category": "Sequencer",
}

import bpy, os
from bpy_extras.io_utils import ExportHelper
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

# Not exposed:
# RENDER_PT_format_presets, RENDER_PT_ffmpeg_presets, RENDER_PT_format,
# RENDER_PT_stereoscopy, RENDER_PT_stamp, RENDER_PT_stamp_note, RENDER_PT_stamp_burn
from bl_ui.properties_output import RENDER_PT_encoding
from bl_ui.properties_output import RENDER_PT_encoding_video
from bl_ui.properties_output import RENDER_PT_encoding_audio
from bl_ui.properties_output import RENDER_PT_frame_range
from bl_ui.properties_output import RENDER_PT_time_stretching
from bl_ui.properties_output import RENDER_PT_post_processing
from bl_ui.properties_output import RENDER_PT_output_color_management
from bl_ui.properties_output import RENDER_PT_output_views


def export_file(context, filepath):
    dirname = os.path.dirname(filepath)
    filename = os.path.splitext(filepath)[0]
    context.scene.render.filepath = os.path.join(dirname, filename)
    bpy.ops.render.opengl(animation=True, sequencer=True)
    return {"FINISHED"}


class SEQUENCER_PT_export_folder_browser(Operator, ExportHelper):
    """Export animation"""

    bl_idname = "sequencer.export"
    bl_label = "Export"
    filename_ext = "."
    # use_filter_folder = True
    use_filter_movie = True
    use_filter_image = True
    filter_glob: StringProperty(default="", options={"HIDDEN"}, maxlen=255)

    def execute(self, context):
        return export_file(context, self.filepath)

    def draw(self, context):
        pass


class SEQUENCER_PT_export(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Export Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SEQUENCER_OT_export"

    def invoke(self, context, event):
        context.scene.render.use_sequencer = True

    def draw(self, context):
        pass


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
        layout = self.layout
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
        layout = self.layout

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
            # Output quality
            use_crf = needs_codec and ffmpeg.codec in {"H264", "MPEG4", "WEBM", "AV1"}
            if use_crf:
                layout.prop(ffmpeg, "constant_rate_factor")
            # Encoding speed
            layout.prop(ffmpeg, "ffmpeg_preset")
            # I-frames
            layout.prop(ffmpeg, "gopsize")
            # B-Frames
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
        layout = self.layout

    def draw(self, context):
        RENDER_PT_encoding_audio.draw(self, context)


class SEQUENCER_PT_export_frame_range(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Frame Range"
    bl_parent_id = "SEQUENCER_PT_export"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
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
    self.layout.operator(
        SEQUENCER_PT_export_frame_range.bl_idname, text="Sequencer Export"
    )


# Class by Meta Person https://github.com/metaperson/blender_vse/blob/main/tube/20210924%231/addon_import_strips.py
class SEQUENCER_OT_import_strips(bpy.types.Operator, ImportHelper):
    bl_description = 'import strips'
    bl_idname = 'sequencer.import_strips'
    bl_label = 'Import'

    files: bpy.props.CollectionProperty(name='Import Strips', type=bpy.types.OperatorFileListElement)

    order_by: bpy.props.EnumProperty(name='Import Order',
                description='Strips are sorted by this order',
                items=[('PICK',         'Pick',                 'No Sort, as selected order'),
                       ('CREATE_TIME',  'File Create Time',     'Sort order by the file created time'),
                       ('FILE_NAME',    'File Name',            'Sort order by the file name'),
                       ('FILE_SIZE',    'File Size',            'Sort order by the file size')],
                default='FILE_NAME')

    reversed_order: bpy.props.BoolProperty(name='Reversed order', description='Reversed order for sorting', default=False)
    
    channel: bpy.props.IntProperty(name='Channel', description='Assign channel to put strips', default=1, min=1)

    image_strip_length: bpy.props.IntProperty(name='Image Duration', description='Image strip length', default=25, min=1)
    
    fit_method: bpy.props.EnumProperty(name='Scale',
                description='Scale fit method',
                items=[('FIT',          'Scale to Fit',         'Scale image to fit within the canvas'),
                       ('FILL',         'Scale to Fill',        'Scale image to completely fill the canvas'),
                       ('STRETCH',      'Stretch to Fill',      'Stretch image to fill the canvas'),
                       ('ORIGINAL',     'Use Original Size',    'Keep image at its original size')],
                default='FIT')


    @classmethod
    def poll(cls, context):
        if not bpy.ops.sequencer.movie_strip_add.poll():
            return False
        if not bpy.ops.sequencer.sound_strip_add.poll():
            return False
        if not bpy.ops.sequencer.image_strip_add.poll():
            return False
        return True

    def execute(self, context):
        #print('ImportHelper.files : {}'.format(self.files))
        #print('file path : {}'.format(self.filepath))
        #print('Sort by order : {}'.format(self.order_by))
        
        strip_dirname = os.path.dirname(self.filepath)
        strip_files = self.files

        #for strip_file in strip_files:
        #    print(strip_file)

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

        # for strip_file in strip_files:
        #     print(strip_file)

        count_movie = 0
        count_sound = 0
        count_image = 0
        
        for strip_file in strip_files:
            strip_ext = os.path.splitext(strip_file.name)[1].lower()
            # print(strip_dirname, strip_file.name, strip_ext)
            frame_start = max([seq.frame_final_end for seq in context.sequences] or [0])
            if strip_ext in ('.avi', '.mp4', '.mpg', '.mpeg', '.mov', '.mkv', '.dv', '.flv'):
                strip_path = os.path.join(strip_dirname, strip_file.name)
                bpy.ops.sequencer.movie_strip_add(filepath=strip_path,
                                                  frame_start=frame_start,
                                                  channel=self.channel,
                                                  fit_method=self.fit_method)
                count_movie += 1
            elif strip_ext in ('.acc', '.ac3', '.flac', '.mp2', '.mp3', '.m4a','.pcm', '.ogg'):
                strip_path = os.path.join(strip_dirname, strip_file.name)
                bpy.ops.sequencer.sound_strip_add(filepath=strip_path,
                                                  frame_start=frame_start,
                                                  channel=self.channel)
                count_sound += 1
            elif strip_ext in ('.jpg', '.jpeg', '.bmp', '.png', '.gif', '.tga', '.tiff'):
                bpy.ops.sequencer.image_strip_add(directory=strip_dirname + '\\', files=[{"name":strip_file.name, "name":strip_file.name}],
                                                  show_multiview=False,
                                                  frame_start=frame_start, frame_end=frame_start+self.image_strip_length,
                                                  channel=self.channel,
                                                  fit_method=self.fit_method)
                count_image += 1
                                                  
        self.report({'INFO'}, 'Imported Movie[{}], Sound[{}], Image[{}], Total[{}]'.format(count_movie,
                                                                                           count_sound,
                                                                                           count_image,
                                                                                           count_movie + count_sound + count_image))


        return {'FINISHED'}
    
#    def draw(self, context):
#        layout = self.layout()
#        layout.label("hej")
#        #layout.operator("SEQUENCER_OT_sound_strip_add", text="Cache")
        

#class SEQUENCER_PT_import(bpy.types.Panel):
#    bl_space_type = "FILE_BROWSER"
#    bl_region_type = "TOOL_PROPS"
#    bl_label = "Import Options"
#    bl_parent_id = "FILE_PT_operator"

#    @classmethod
#    def poll(cls, context):
#        sfile = context.space_data
#        operator = sfile.active_operator
#        return operator.bl_idname == "SEQUENCER_OT_import_strips"

#    def invoke(self, context, event):
#        context.scene.render.use_sequencer = True

#    def draw(self, context):
#        layout = self.layout()
#        layout.operator("SEQUENCER_OT_sound_strip_add.cache", text="Cache")
#        pass


class SEQUENCER_MT_sequence(bpy.types.Menu):
    bl_idname = "SEQUENCER_MT_sequence"
    bl_label = "Sequence"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("sequencer.refresh_all", text="Refresh All")
        layout.operator_context = "INVOKE_DEFAULT"

        layout.separator()
        layout.operator("sequencer.import_strips", text="Import")

        props = layout.operator("sequencer.export", text="Export")

        layout.separator()
        layout.operator("render.opengl", text="Render Image").sequencer = True

        layout.separator()
        layout.operator("sound.mixdown", text="Export Audio Mixdown")

        layout.separator()
        layout.operator("sequencer.export_subtitles", text="Export Subtitles")


def prepend_sequence_menu(self, context):
    self.layout.menu("SEQUENCER_MT_sequence")


classes = (
    SEQUENCER_PT_export,
    SEQUENCER_PT_export_image,
    SEQUENCER_PT_export_color_management,
    SEQUENCER_PT_export_encoding,
    SEQUENCER_PT_export_encoding_video,
    SEQUENCER_PT_export_audio,
    SEQUENCER_PT_export_frame_range,
    SEQUENCER_PT_export_time_stretching,
    SEQUENCER_PT_export_post_processing,
    SEQUENCER_PT_export_folder_browser,
    SEQUENCER_OT_import_strips,
    #SEQUENCER_PT_import,
    SEQUENCER_MT_sequence,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.SEQUENCER_MT_editor_menus.prepend(prepend_sequence_menu)


def unregister():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.SEQUENCER_MT_editor_menus.remove(prepend_sequence_menu)


if __name__ == "__main__":
    register()

    # test call
    # bpy.ops.sequencer.export('INVOKE_DEFAULT')
