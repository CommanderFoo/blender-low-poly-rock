# MIT License
 
# Copyright (c) 2020 PIXELDEPTH.net
# https://github.com/PopThosePringles/blender-low-poly-rock

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

bl_info = {
	"name": "Low Poly Rock",
	"description": "Create low poly rocks quickly",
	"author": "PIXELDEPTH.net",
	"version": (1, 0, 0),
	"blender": (2, 80, 0),
	"location": "View3D > Add > Mesh > Low Poly Rock",
	"category": "Add Mesh",
	"tracker_url": "https://github.com/PopThosePringles/blender-low-poly-rock/issues"
}

import bpy
import bmesh
from math import radians
from bpy.props import (

	BoolProperty,
	IntProperty,
	FloatProperty,
	FloatVectorProperty,
	EnumProperty

)


def create_mesh(ctx, scene, generator):
	mesh = bpy.data.meshes.new(name = "Low_Poly_Rock_Mesh")
	rock = bpy.data.objects.new(name = "Low_Poly_Rock", object_data = mesh)

	bm = bmesh.new()
	bmesh.ops.create_icosphere(bm,

		subdivisions = generator.subdivisions_prop,
		radius = generator.radius_prop

	)

	bm.to_mesh(mesh)
	bm.free()

	return rock

def create_displace(generator):
	tex = bpy.data.textures.new("Low_Poly_Rock_Voronoi", type = "VORONOI")

	tex.noise_scale = generator.radius_prop * generator.voronoi_noise_scale_prop
	tex.noise_intensity = generator.voronoi_intensity_prop
	tex.distance_metric = generator.voronoi_distance_prop
	tex.contrast = generator.decimate_sharpness_prop * generator.voronoi_contrast_prop
	tex.intensity = generator.voronoi_brightness_prop

	tex.weight_1 = generator.voronoi_weight_1_prop
	tex.weight_2 = generator.voronoi_weight_2_prop
	tex.weight_3 = generator.voronoi_weight_3_prop
	tex.weight_4 = generator.voronoi_weight_4_prop

	tex.use_color_ramp = True
	ramp = tex.color_ramp

	ramp.interpolation = "B_SPLINE"

	ramp.elements[0].color = generator.voronoi_color_ramp_1_prop
	ramp.elements[0].position = generator.voronoi_color_ramp_1_pos_prop

	ramp.elements[1].color = generator.voronoi_color_ramp_2_prop
	ramp.elements[1].position = generator.voronoi_color_ramp_2_pos_prop

	last = ramp.elements.new(generator.voronoi_color_ramp_3_pos_prop)

	last.color = generator.voronoi_color_ramp_3_prop

	bpy.ops.object.modifier_add(type = "DISPLACE")

	displace = bpy.context.object.modifiers["Displace"]

	displace.texture = tex
	displace.name = "Low_Poly_Displace"
	displace.mid_level = generator.displace_midlevel_prop
	displace.direction = generator.displace_direction_prop
	displace.strength = generator.radius_prop * generator.displace_strength_prop
	displace.texture_coords = generator.displace_tex_coords_prop

	return tex


def create_decimate(generator):
	decimate_collapse = bpy.ops.object.modifier_add(type = "DECIMATE")

	bpy.context.object.modifiers["Decimate"].ratio = generator.decimate_collapse_ratio_prop
	bpy.context.object.modifiers["Decimate"].name = "Low_Poly_Decimate_Collapse"

	decimate_planar = bpy.ops.object.modifier_add(type = "DECIMATE")

	bpy.context.object.modifiers["Decimate"].decimate_type = "DISSOLVE"
	bpy.context.object.modifiers["Decimate"].angle_limit = generator.decimate_planar_ratio_prop * radians(generator.decimate_planar_angle_prop)
	bpy.context.object.modifiers["Decimate"].use_dissolve_boundaries = True
	bpy.context.object.modifiers["Decimate"].name = "Low_Poly_Decimate_Planar"

	return decimate_collapse, decimate_planar


def create_remesh(generator):
	bpy.ops.object.modifier_add(type = "REMESH")
	bpy.context.object.modifiers["Remesh"].mode = generator.remesh_1_mode_prop
	bpy.context.object.modifiers["Remesh"].octree_depth = generator.remesh_1_octree_prop
	bpy.context.object.modifiers["Remesh"].scale = generator.remesh_1_scale_prop
	bpy.context.object.modifiers["Remesh"].name = "Low_Poly_Remesh_1"
	
	bpy.ops.object.modifier_add(type = "REMESH")
	bpy.context.object.modifiers["Remesh"].mode = generator.remesh_2_mode_prop
	bpy.context.object.modifiers["Remesh"].octree_depth = generator.remesh_2_octree_prop
	bpy.context.object.modifiers["Remesh"].scale = generator.remesh_2_scale_prop
	bpy.context.object.modifiers["Remesh"].name = "Low_Poly_Block_Remesh_2"

	if generator.remesh_decimate_ratio_prop < 1.0:	
		bpy.ops.object.modifier_add(type = "DECIMATE")

		bpy.context.object.modifiers["Decimate"].ratio = generator.remesh_decimate_ratio_prop
		bpy.context.object.modifiers["Decimate"].name = "Low_Poly_Remesh_Decimate"
	

def generate_low_poly_rock(generator):
	ctx = bpy.context
	scene = ctx.scene

	rock = create_mesh(ctx, scene, generator)

	rock.scale = (

		generator.x_scale_prop,
		generator.y_scale_prop,
		generator.z_scale_prop

	)

	rock.location = scene.cursor.location.copy() 
	scene.collection.objects.link(rock)
	ctx.view_layer.objects.active = rock

	tex = create_displace(generator)
	decimate_collapse, decimate_planar = create_decimate(generator)
	
	if generator.remesh_enable_prop == True:
		create_remesh(generator)

	if generator.keep_modifiers_prop == False:
		depsgraph = ctx.evaluated_depsgraph_get()
		object_eval = rock.evaluated_get(depsgraph)
		tmp = bpy.data.meshes.new_from_object(object_eval)

		rock.data = tmp
		rock.modifiers.clear()

		bpy.data.textures.remove(tex)

	rock.select_set(state = True)

	if generator.apply_scale_prop == True:
		bpy.ops.object.transform_apply(location = False, rotation = False, scale = True)

	if generator.show_wire_prop:
		ctx.object.show_wire = True
	else:
		ctx.object.show_wire = False
		
	ctx.view_layer.update()	


class Low_Poly_Rock_Generator(bpy.types.Operator):
	"""Low Poly Rock"""
	bl_idname = "mesh.add_low_poly_rock"
	bl_label = "Low Poly Rock"

	bl_options = {

		"REGISTER", "UNDO"

	}

	# General Settings

	subdivisions_prop: IntProperty(

		name = "Subdivisions",
		min = 1,
		max = 6,
		default = 4

	)

	radius_prop: FloatProperty(

		name = "Radius",
		min = 0.01,
		step = 0.1,
		default = 1.0

	)


	x_scale_prop: FloatProperty(

		name = "X",
		min = 0.01,
		default = 1.0,
		step = 0.1

	)

	y_scale_prop: FloatProperty(

		name = "Y",
		min = 0.01,
		default = 1.0,
		step = 0.1

	)

	z_scale_prop: FloatProperty(

		name = "Z",
		min = 0.01,
		default = 1.0,
		step = 0.1

	)

	# Decimate Settings

	decimate_collapse_ratio_prop: FloatProperty(

		name = "Collapse Ratio",
		min = 0.01,
		max = 1.0,
		step = 0.01,
		default = 0.06,
		description = "Decimates the rock to reduce polygons"

	)

	decimate_planar_ratio_prop: FloatProperty(

		name = "Planar Ratio",
		min = 0,
		max = 1.0,
		step = 0.1,
		default = 0.25,
		description = "Decimates the rock based on angle of faces"

	)

	decimate_planar_angle_prop: IntProperty(
	
		name = "Max Angle",
		min = 0,
		max = 180,
		default = 90,
		description = "Any angle below this will be dissolved"

	)

	decimate_sharpness_prop: FloatProperty(

		name = "Sharpness",
		min = 0.0,
		max = 3.0,
		step = 0.1,
		default = 0.80,
		description = "How sharp the rock will be.  Lower value will make it more rounded"

	)

	# Displace Settings

	displace_settings_prop: BoolProperty(

		name = "Displace Settings",
		default = False

	)

	displace_midlevel_prop: FloatProperty(

		name = "Midlevel",
		min = 0.0,
		max = 1.0,
		default = 0.5,
		description = "Material value that gives no displacement"

	)

	displace_strength_prop: FloatProperty(

		name = "Strength",
		min = -100.0,
		max = 100.0,
		default = 1,
		description = "Amount to displace the geometry"

	)

	displace_direction_prop: EnumProperty(

		items = [

			("X", "X", ""),
			("Y", "Y", ""),
			("Z", "Z", ""),
			("NORMAL", "Normal", "")

		],

		name = "",
		default = "NORMAL"

	)

	displace_tex_coords_prop: EnumProperty(

		items = [

			("LOCAL", "Local", ""),
			("GLOBAL", "Global", ""),
			("OBJECT", "Object", "")

		],

		name = "",
		default = "OBJECT"

	)

	# Voronoi Settings

	voronoi_settings_prop: BoolProperty(

		name = "Voronoi Settings",
		default = False

	)

	voronoi_distance_prop: EnumProperty(

		items = [

			("DISTANCE", "Actual Distance", ""),
			("DISTANCE_SQUARED", "Distance Squared", ""),
			("MANHATTAN", "Manhatten", ""),
			("CHEBYCHEV", "Chebychev", ""),
			("MANHATTAN", "Manhatten", "")

		],

		name = "Distance",
		default = "MANHATTAN"

	)

	voronoi_noise_scale_prop: FloatProperty(

		name = "Scale",
		min = 0.0,
		max = 2.0,
		step = 0.01,
		default = 1.0

	)

	voronoi_intensity_prop: FloatProperty(

		name = "Intensity",
		min = 0.01,
		max = 10.0,
		step = 0.01,
		default = 1.0

	)

	voronoi_brightness_prop: FloatProperty(

		name = "Brightness",
		min = 0.0,
		max = 2.0,
		step = 0.01,
		default = 0.8

	)

	voronoi_contrast_prop: FloatProperty(

		name = "Contrast",
		min = 0.0,
		max = 5.0,
		step = 0.01,
		default = 1.0

	)

	voronoi_weight_1_prop: FloatProperty(

		name = "Weight 1",
		min = -2.0,
		max = 2.0,
		step = 0.01,
		default = 1.0

	)

	voronoi_weight_2_prop: FloatProperty(

		name = "Weight 2",
		min = -2.0,
		max = 2.0,
		step = 0.01,
		default = 0.3

	)

	voronoi_weight_3_prop: FloatProperty(

		name = "Weight 3",
		min = -2.0,
		max = 2.0,
		step = 0.01,
		default = 1.0

	)

	voronoi_weight_4_prop: FloatProperty(

		name = "Weight 4",
		min = -2.0,
		max = 2.0,
		step = 0.01,
		default = 1.0

	)

	voronoi_color_ramp_prop: BoolProperty(

		name = "Color Ramp",
		default = False

	)

	voronoi_color_ramp_1_prop: FloatVectorProperty(

		name = "",
		subtype = "COLOR",
		size = 4,
		min = 0.0,
		max = 1.0,
		default = (0.0, 0.0, 0.0, 1.0)

	)

	voronoi_color_ramp_1_pos_prop: FloatProperty(

		name = "",
		min = 0.0,
		max = 1.0,
		step = 0.01,
		default = 0.0

	)

	voronoi_color_ramp_2_prop: FloatVectorProperty(

		name = "",
		subtype = "COLOR",
		size = 4,
		min = 0.0,
		max = 1.0,
		default = (0.21, 0.21, 0.2, 1.0)

	)

	voronoi_color_ramp_2_pos_prop: FloatProperty(

		name = "",
		min = 0.0,
		max = 1.0,
		step = 0.01,
		default = 0.5

	)

	voronoi_color_ramp_3_prop: FloatVectorProperty(

		name = "",
		subtype = "COLOR",
		size = 4,
		min = 0.0,
		max = 1.0,
		default = (1.0, 1.0, 1.0, 1.0)

	)

	voronoi_color_ramp_3_pos_prop: FloatProperty(

		name = "",
		min = 0.0,
		max = 1.0,
		step = 0.01,
		default = 1.0

	)
	
	# Remesh
	
	remesh_settings_prop: BoolProperty(
	
		name = "Remesh Settings",
		default = False		
	
	)
	
	remesh_enable_prop: BoolProperty(
	
		name = "Enable Remesh",
		default = False		
	
	)
	
	remesh_1_mode_prop: EnumProperty(

		items = [

			("BLOCKS", "Block", ""),
			("SMOOTH", "Smooth", ""),
			("SHARP", "Sharp", "")

		],

		name = "",
		default = "BLOCKS"

	)
	
	remesh_1_octree_prop: IntProperty(
	
		name = "Octree Depth",
		default = 5
	
	)
	
	remesh_1_scale_prop: FloatProperty(
	
		name = "Scale",
		min = 0,
		max = 0.990,
		default = 0.990,
		step = 0.01
	
	)
	
	remesh_2_mode_prop: EnumProperty(

		items = [

			("BLOCKS", "Block", ""),
			("SMOOTH", "Smooth", ""),
			("SHARP", "Sharp", "")

		],

		name = "",
		default = "SHARP"

	)
	
	remesh_2_octree_prop: IntProperty(
	
		name = "Octree Depth",
		default = 3
	
	)
	
	remesh_2_scale_prop: FloatProperty(
	
		name = "Scale",
		min = 0,
		max = 0.990,
		default = 0.990,
		step = 0.01
	
	)
	
	remesh_decimate_ratio_prop: FloatProperty(
	
		name = "Decimate Ratio",
		default = 1.0,
		max = 1.0,
		min = 0.01,
		step = 0.1
	
	)

	# Misc Settings

	misc_settings_prop: BoolProperty(

		name = "Misc Settings",
		default = False

	)

	show_wire_prop: BoolProperty(

		name = "Show Wireframe",
		default = True

	)

	apply_scale_prop: BoolProperty(

		name = "Apply Scale",
		default = True

	)

	keep_modifiers_prop: BoolProperty(

		name = "Keep Modifiers",
		default = False

	)


	def execute(self, context):
		bpy.ops.object.select_all(action = "DESELECT")

		generate_low_poly_rock(self)

		return {

			"FINISHED"

		}

	@classmethod
	def poll(cls, context):
		return (context.mode == "OBJECT")


	def draw(self, context):
		layout = self.layout

		settings_grp = layout.column()
		settings_box = settings_grp.box()

		settings_box.label(text = "General Settings:")

		settings_row = settings_box.row();

		settings_row.prop(self, "subdivisions_prop", slider = True)
		settings_row.prop(self, "radius_prop")

		scale_row = settings_box.row()

		scale_row.prop(self, "x_scale_prop")
		scale_row.prop(self, "y_scale_prop")
		scale_row.prop(self, "z_scale_prop")

		settings_box.label(text = "Decimate Settings:")

		settings_row = settings_box.row();

		settings_row.prop(self, "decimate_sharpness_prop", slider = True)
		settings_row.prop(self, "decimate_planar_angle_prop", slider = True)
		settings_box.prop(self, "decimate_collapse_ratio_prop", slider = True)

		displace_grp = layout.column()
		displace_box = displace_grp.box()

		displace_box.prop(self, "displace_settings_prop")

		if self.displace_settings_prop:
			displace_row = displace_box.row();

			displace_row.prop(self, "displace_midlevel_prop", slider = True)
			displace_row.prop(self, "displace_strength_prop", slider = True)

			displace_split = displace_box.split()

			displace_col = displace_split.column()
			displace_col.label(text = "Direction:")
			displace_col.prop(self, "displace_direction_prop")

			displace_col = displace_split.column()
			displace_col.label(text = "Texture Coordinates:")
			displace_col.prop(self, "displace_tex_coords_prop")

		voronoi_grp = layout.column()
		voronoi_box = voronoi_grp.box()

		voronoi_box.prop(self, "voronoi_settings_prop")

		if self.voronoi_settings_prop:
			voronoi_box.prop(self, "voronoi_distance_prop")

			voronoi_row = voronoi_box.row()

			voronoi_row.prop(self, "voronoi_intensity_prop", slider = True)
			voronoi_row.prop(self, "voronoi_noise_scale_prop", slider = True)

			voronoi_row = voronoi_box.row()

			voronoi_row.prop(self, "voronoi_brightness_prop", slider = True)
			voronoi_row.prop(self, "voronoi_contrast_prop", slider = True)

			voronoi_row = voronoi_box.row() 

			voronoi_row.prop(self, "voronoi_weight_1_prop", slider = True)
			voronoi_row.prop(self, "voronoi_weight_2_prop", slider = True)

			voronoi_row = voronoi_box.row() 

			voronoi_row.prop(self, "voronoi_weight_3_prop", slider = True)
			voronoi_row.prop(self, "voronoi_weight_4_prop", slider = True)

			voronoi_box.prop(self, "voronoi_color_ramp_prop")

			if self.voronoi_color_ramp_prop:
				voronoi_row = voronoi_box.row()

				voronoi_ramp_split = voronoi_row.split()

				voronoi_ramp_col = voronoi_ramp_split.column()

				voronoi_ramp_col.label(text = "Position 1:")
				voronoi_ramp_col.prop(self, "voronoi_color_ramp_1_pos_prop", slider = True)

				voronoi_ramp_col = voronoi_ramp_split.column()

				voronoi_ramp_col.label(text = "Position 1 Color:")
				voronoi_ramp_col.prop(self, "voronoi_color_ramp_1_prop")

				voronoi_row = voronoi_box.row()
				voronoi_ramp_split = voronoi_row.split()

				voronoi_ramp_col = voronoi_ramp_split.column()

				voronoi_ramp_col.label(text = "Position 2:")
				voronoi_ramp_col.prop(self, "voronoi_color_ramp_2_pos_prop", slider = True)

				voronoi_ramp_col = voronoi_ramp_split.column()

				voronoi_ramp_col.label(text = "Position 2 Color:")
				voronoi_ramp_col.prop(self, "voronoi_color_ramp_2_prop")

				voronoi_row = voronoi_box.row()
				voronoi_ramp_split = voronoi_row.split()

				voronoi_ramp_col = voronoi_ramp_split.column()

				voronoi_ramp_col.label(text = "Position 3:")
				voronoi_ramp_col.prop(self, "voronoi_color_ramp_3_pos_prop", slider = True)

				voronoi_ramp_col = voronoi_ramp_split.column()

				voronoi_ramp_col.label(text = "Position 3 Color:")
				voronoi_ramp_col.prop(self, "voronoi_color_ramp_3_prop")

		remesh_grp = layout.column()
		remesh_box = remesh_grp.box()

		remesh_box.prop(self, "remesh_settings_prop")

		if self.remesh_settings_prop:
			remesh_box.prop(self, "remesh_enable_prop")
			
			remesh_split = remesh_box.split()
			
			remesh_col = remesh_split.column()
			remesh_col_box = remesh_col.box()
			
			remesh_col_box.label(text = "Remesh 1:")
			
			remesh_col_box.prop(self, "remesh_1_mode_prop")
			remesh_col_box.prop(self, "remesh_1_octree_prop")
			remesh_col_box.prop(self, "remesh_1_scale_prop")

			remesh_col = remesh_split.column()

			remesh_col_box = remesh_col.box()
			
			remesh_col_box.label(text = "Remesh 2:")
			
			remesh_col_box.prop(self, "remesh_2_mode_prop")
			remesh_col_box.prop(self, "remesh_2_octree_prop")
			remesh_col_box.prop(self, "remesh_2_scale_prop")
			
			remesh_row = remesh_box.row()
			
			remesh_row.prop(self, "remesh_decimate_ratio_prop", slider = True)
						
		misc_settings_grp = layout.column()
		misc_settings_box = misc_settings_grp.box()

		misc_settings_box.prop(self, "misc_settings_prop")

		if self.misc_settings_prop:
			misc_settings_row = misc_settings_box.row()

			misc_settings_row.prop(self, "show_wire_prop")
			misc_settings_row.prop(self, "apply_scale_prop")

			misc_settings_row = misc_settings_box.row()

			misc_settings_row.prop(self, "keep_modifiers_prop")


def menu_low_poly_rocks(self, context):
	self.layout.operator(

		Low_Poly_Rock_Generator.bl_idname,
		text = "Low Poly Rock",
		icon = "PLUGIN"

	)


def register():
	bpy.utils.register_class(Low_Poly_Rock_Generator)
	bpy.types.VIEW3D_MT_mesh_add.append(menu_low_poly_rocks)


def unregister():
	bpy.utils.unregister_class(Low_Poly_Rock_Generator)
	bpy.types.VIEW3D_MT_mesh_add.remove(menu_low_poly_rocks)

if __name__ == "__main__":
	register()
