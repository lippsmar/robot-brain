"""Photoreal renders of Schlaubi (Blender/Cycles via bpy). Usage: scene.py <scene> <out.png> <texdir> [samples]"""
import math
import sys

import bpy
from mathutils import Vector

SCENE, OUT, TEX = sys.argv[1], sys.argv[2], sys.argv[3]
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 128
PCT = int(sys.argv[5]) if len(sys.argv) > 5 else 100

S = 0.10          # cube edge 10 cm
F = 0.009         # frame beam thickness
P = 0.003         # acrylic panel thickness

GLOW = {
    "blue": (0.08, 0.32, 1.0),
    "white": (1.0, 0.97, 0.92),
    "gold": (1.0, 0.5, 0.06),
    "amber": (1.0, 0.45, 0.12),
    "violet": (0.45, 0.15, 1.0),
    "turquoise": (0.05, 0.8, 0.7),
}


# ---------- helpers ----------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1100
    sc.render.film_transparent = False
    sc.render.resolution_percentage = PCT
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 8


def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out


def principled(name, color, rough=0.5, metal=0.0, emission=None, strength=0.0, image=None):
    m, nt, out = node_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image)
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = strength
    elif emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = strength
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m


def wood(name, c1, c2, scale=40.0, rough=0.55):
    m, nt, out = node_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale * 0.08, scale)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 4.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.25
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], mix.inputs["A"])
    nt.links.new(noise.outputs["Fac"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(mix.outputs["Result"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m


def opal(name):
    """Matte white opal acrylic: lets the inner light glow through."""
    m, nt, out = node_mat(name)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.95, 0.95, 0.95, 1)
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
    pr.inputs["Base Color"].default_value = (0.93, 0.93, 0.92, 1)
    pr.inputs["Roughness"].default_value = 0.42
    pr.inputs["Coat Weight"].default_value = 0.15
    pr.inputs["Coat Roughness"].default_value = 0.35
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.7
    nt.links.new(pr.outputs["BSDF"], mx.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
    nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    return m


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("bev", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    o.data.materials.append(mat)
    return o


def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def area_light(name, loc, rot, size, energy, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.color = color
    d.shape = shape
    d.size = size
    if size_y:
        d.size_y = size_y
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = rot
    bpy.context.collection.objects.link(o)
    return o


def point_light(name, loc, energy, color, radius=0.02):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = energy
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    o.location = loc
    bpy.context.collection.objects.link(o)
    return o


def world(color, strength):
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    bpy.context.scene.world = w


def camera(loc, target, lens=50, fstop=2.8, focus=None, exposure=0.0):
    bpy.context.scene.view_settings.exposure = exposure
    d = bpy.data.cameras.new("Cam")
    d.lens = lens
    d.dof.use_dof = True
    d.dof.aperture_fstop = fstop
    o = bpy.data.objects.new("Cam", d)
    o.location = loc
    bpy.context.collection.objects.link(o)
    direction = Vector(target) - Vector(loc)
    o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    d.dof.focus_distance = focus if focus else direction.length
    bpy.context.scene.camera = o
    return o


# ---------- Schlaubi ----------
def schlaubi(origin=(0, 0, 0), glow="blue", glow_power=1.0, rot_z=0.0, label=True):
    ox, oy, oz = origin
    c = (ox, oy, oz + S / 2)
    oak = wood("Oak", (0.36, 0.24, 0.14), (0.24, 0.15, 0.08), scale=90)
    acryl = opal("Opal")
    black = principled("Black", (0.02, 0.02, 0.025), 0.35)
    glass = principled("Lens", (0.02, 0.03, 0.05), 0.05, metal=0.0)
    metal = principled("Metal", (0.7, 0.7, 0.72), 0.25, metal=1.0)
    parts = []
    h = S / 2 - F / 2
    # 12 frame beams
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("beamZ", (F, F, S), (c[0] + sx * h, c[1] + sy * h, c[2]), oak, bevel=0.0012))
    for sy in (-1, 1):
        for sz in (-1, 1):
            parts.append(box("beamX", (S - 2 * F, F, F), (c[0], c[1] + sy * h, c[2] + sz * h), oak, bevel=0.0012))
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(box("beamY", (F, S - 2 * F, F), (c[0] + sx * h, c[1], c[2] + sz * h), oak, bevel=0.0012))
    # acrylic panels, slightly inset
    inner = S - 2 * F
    off = S / 2 - F * 0.55
    parts.append(box("panelTop", (inner, inner, P), (c[0], c[1], c[2] + off), acryl))
    parts.append(box("panelFront", (inner, P, inner), (c[0], c[1] - off, c[2]), acryl))
    parts.append(box("panelBack", (inner, P, inner), (c[0], c[1] + off, c[2]), acryl))
    parts.append(box("panelLeft", (P, inner, inner), (c[0] - off, c[1], c[2]), acryl))
    parts.append(box("panelRight", (P, inner, inner), (c[0] + off, c[1], c[2]), acryl))
    parts.append(box("panelBottom", (S, S, 0.004), (c[0], c[1], oz + 0.002), oak))
    # front: camera window and lens
    fy = c[1] - off - P / 2
    parts.append(cyl("camRing", 0.0085, 0.002, (c[0], fy - 0.0006, c[2] + 0.022), black, rot=(math.pi / 2, 0, 0)))
    parts.append(cyl("camLens", 0.0045, 0.0026, (c[0], fy - 0.0012, c[2] + 0.022), glass, rot=(math.pi / 2, 0, 0)))
    # mic holes
    for dx in (-0.006, 0, 0.006):
        parts.append(cyl("mic", 0.0011, 0.002, (c[0] + dx, fy - 0.0004, c[2] - 0.028), black, rot=(math.pi / 2, 0, 0), verts=16))
    # right side: vents and USB-C
    rx = c[0] + off + P / 2
    for k in range(5):
        parts.append(box("vent", (0.0012, 0.0035, 0.024), (rx + 0.0004, c[1] - 0.016 + k * 0.008, c[2] + 0.018), black))
    parts.append(box("usbc", (0.0012, 0.009, 0.0032), (rx + 0.0004, c[1], c[2] - 0.034), black, bevel=0.0012))
    # top button
    parts.append(cyl("button", 0.006, 0.003, (c[0] + 0.026, c[1] + 0.026, c[2] + off + P / 2 + 0.0012), metal))
    # "KI" engraving on the lower front beam
    if label:
        bpy.ops.object.text_add(location=(c[0] + S / 2 - F - 0.004, c[1] - S / 2 - 0.00005, oz + F * 0.5 - 0.0022), rotation=(math.pi / 2, 0, 0))
        t = bpy.context.active_object
        t.data.body = "KI"
        t.data.size = 0.0055
        t.data.extrude = 0.00015
        t.data.align_x = "RIGHT"
        t.data.materials.append(principled("Burn", (0.12, 0.06, 0.03), 0.7))
        parts.append(t)
    # inner electronics silhouette and light
    parts.append(box("pcb", (0.065, 0.03, 0.004), (c[0], c[1] + 0.005, c[2] - 0.01), principled("PCB", (0.05, 0.2, 0.08), 0.5)))
    col = GLOW[glow]
    lights = []
    for dz in (-0.012, 0.018):
        lights.append(point_light("glow", (c[0], c[1], c[2] + dz), 1.2 * glow_power, col, radius=0.03))
    # group and rotate
    pivot = bpy.data.objects.new("Schlaubi", None)
    pivot.location = (ox, oy, oz)
    bpy.context.collection.objects.link(pivot)
    bpy.context.view_layer.update()
    for o in parts + lights:
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
    pivot.rotation_euler = (0, 0, rot_z)
    return pivot


# ---------- props ----------
def desk(size=3.0, light_wood=True, z=0.0):
    if light_wood:
        m = wood("Desk", (0.72, 0.58, 0.42), (0.6, 0.45, 0.3), scale=6, rough=0.45)
    else:
        m = wood("Table", (0.32, 0.2, 0.12), (0.22, 0.13, 0.07), scale=5, rough=0.4)
    return box("desk", (size, size, 0.04), (0, 0, z - 0.02), m)


def wall(color=(0.85, 0.83, 0.8), y=0.9):
    return box("wall", (6, 0.05, 4), (0, y, 1.5), principled("Wall", color, 0.9))


def phone(loc, rot_z, screen=True):
    body = principled("PhoneBody", (0.04, 0.04, 0.045), 0.3, metal=0.4)
    p = box("phone", (0.072, 0.152, 0.008), loc, body, rot=(0, 0, rot_z), bevel=0.004)
    if screen:
        scr = principled("Screen", (1, 1, 1), 0.15, image=f"{TEX}/phone_chat.png", strength=1.2)
        s = box("phoneScreen", (0.066, 0.144, 0.0004), (loc[0], loc[1], loc[2] + 0.0042), scr, rot=(0, 0, rot_z))
        uv_fit(s)
    return p


def uv_fit(obj):
    """Map the top face to the full texture (smart project is enough for flat boxes)."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=1.0, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def laptop(loc, rot_z, open_deg=105, screen_img=None, color=(0.55, 0.56, 0.58)):
    shell = principled("LaptopShell", color, 0.35, metal=0.6)
    w, d = 0.32, 0.22
    piv = bpy.data.objects.new("Laptop", None)
    piv.location = loc
    bpy.context.collection.objects.link(piv)
    base = box("lapBase", (w, d, 0.016), (loc[0], loc[1], loc[2] + 0.008), shell, bevel=0.003)
    keys = box("lapKeys", (w * 0.86, d * 0.45, 0.0008), (loc[0], loc[1] + 0.02, loc[2] + 0.0162), principled("Keys", (0.05, 0.05, 0.06), 0.6))
    hinge_y = loc[1] + d / 2
    lid_piv = bpy.data.objects.new("LidPivot", None)
    lid_piv.location = (loc[0], hinge_y, loc[2] + 0.016)
    bpy.context.collection.objects.link(lid_piv)
    bpy.context.view_layer.update()
    lid = box("lapLid", (w, d, 0.006), (loc[0], hinge_y - d / 2, loc[2] + 0.019), shell, bevel=0.002)
    parts = [lid]
    if screen_img:
        scr = principled("LapScreen", (1, 1, 1), 0.2, image=screen_img, strength=1.0)
        s = box("lapScreen", (w * 0.92, d * 0.88, 0.0004), (loc[0], hinge_y - d / 2, loc[2] + 0.0158), scr)
        uv_fit(s)
        # screen faces down when closed -> flip texture side by rotating 180 about Y later via lid rotation
        parts.append(s)
    for o in parts:
        o.parent = lid_piv
        o.matrix_parent_inverse = lid_piv.matrix_world.inverted()
    lid_piv.rotation_euler = (-math.radians(180 - open_deg), 0, 0) if open_deg < 179 else (0, 0, 0)
    bpy.context.view_layer.update()
    for o in (base, keys, lid_piv):
        o.parent = piv
        o.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler = (0, 0, rot_z)
    return piv


def mug(loc, color=(0.92, 0.92, 0.9)):
    m = principled("Mug", color, 0.25)
    cup = cyl("mug", 0.04, 0.09, (loc[0], loc[1], loc[2] + 0.045), m, verts=64)
    coffee = cyl("coffee", 0.037, 0.002, (loc[0], loc[1], loc[2] + 0.082), principled("Coffee", (0.12, 0.06, 0.03), 0.1))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.006, location=(loc[0] + 0.05, loc[1], loc[2] + 0.05), rotation=(math.pi / 2, 0, 0))
    hnd = bpy.context.active_object
    hnd.data.materials.append(m)
    return cup


def plant(loc):
    pot = cyl("pot", 0.05, 0.09, (loc[0], loc[1], loc[2] + 0.045), principled("Pot", (0.75, 0.42, 0.28), 0.8), verts=48)
    leafm = principled("Leaf", (0.08, 0.35, 0.1), 0.45)
    for i in range(9):
        a = i / 9 * 2 * math.pi
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(loc[0] + 0.03 * math.cos(a), loc[1] + 0.03 * math.sin(a), loc[2] + 0.12 + 0.02 * (i % 3)))
        lf = bpy.context.active_object
        lf.scale = (1.8, 0.5, 0.18)
        lf.rotation_euler = (0.5, 0.3, a)
        lf.data.materials.append(leafm)
        bpy.ops.object.shade_smooth()
    return pot


def hdd(loc, rot_z=0.0):
    return box("hdd", (0.08, 0.115, 0.02), (loc[0], loc[1], loc[2] + 0.01), principled("HDD", (0.08, 0.08, 0.09), 0.4), rot=(0, 0, rot_z), bevel=0.004)


def earbuds_case(loc):
    return box("budsCase", (0.06, 0.045, 0.025), (loc[0], loc[1], loc[2] + 0.0125), principled("Buds", (0.95, 0.95, 0.95), 0.3), bevel=0.01)


def book(loc, rot_z, color):
    return box("book", (0.15, 0.22, 0.025), (loc[0], loc[1], loc[2] + 0.0125), principled("Book", color, 0.7), rot=(0, 0, rot_z), bevel=0.002)


# ---------- scenes ----------
def scene_desk():
    world((0.6, 0.65, 0.72), 0.35)
    desk()
    wall(y=0.55)
    schlaubi(glow="blue", glow_power=3.0, rot_z=math.radians(-28))
    plant((0.24, 0.22, 0))
    book((-0.25, 0.12, 0), 0.3, (0.18, 0.28, 0.4))
    area_light("window", (-0.9, -0.4, 0.9), (math.radians(60), 0, math.radians(-60)), 1.2, 35, (1, 0.97, 0.93))
    area_light("fill", (0.8, -0.7, 0.5), (math.radians(65), 0, math.radians(50)), 0.8, 6, (0.9, 0.93, 1))
    camera((0.26, -0.55, 0.2), (0.02, 0.03, 0.05), lens=55, fstop=5.6, focus=0.58, exposure=-0.5)


def scene_cafe():
    world((0.35, 0.25, 0.18), 0.25)
    desk(light_wood=False)
    schlaubi(glow="white", glow_power=1.5, rot_z=math.radians(20))
    mug((0.16, 0.06, 0))
    phone((-0.13, -0.06, 0.004), math.radians(-25))
    earbuds_case((-0.2, 0.08, 0))
    area_light("lampA", (0.3, 0.2, 0.7), (math.radians(20), math.radians(25), 0), 0.4, 40, (1, 0.78, 0.55), shape="DISK")
    area_light("window", (-1.0, -0.2, 0.8), (math.radians(55), 0, math.radians(-75)), 1.0, 20, (0.85, 0.9, 1.0))
    point_light("bokeh1", (0.6, 1.4, 0.5), 6, (1, 0.7, 0.4), 0.05)
    point_light("bokeh2", (-0.5, 1.6, 0.6), 6, (1, 0.75, 0.45), 0.05)
    point_light("bokeh3", (0.1, 1.8, 0.45), 5, (1, 0.8, 0.5), 0.05)
    camera((0.02, -0.5, 0.22), (-0.04, 0, 0.04), lens=45, fstop=3.5, focus=0.52, exposure=-1.0)


def scene_show():
    world((0.6, 0.65, 0.72), 0.3)
    desk()
    wall(y=0.6)
    schlaubi(glow="white", glow_power=3.0, rot_z=0)
    # an object held up to the camera: a small succulent leaf on a stand / a component
    plant((0.0, -0.17, 0))
    area_light("window", (-0.8, -0.5, 0.8), (math.radians(60), 0, math.radians(-55)), 1.2, 35, (1, 0.97, 0.93))
    camera((0.36, -0.42, 0.2), (0.0, -0.07, 0.06), lens=50, fstop=4.5, exposure=-0.8)


def scene_insight():
    world((0.05, 0.06, 0.09), 0.2)
    desk(light_wood=False)
    wall(color=(0.25, 0.27, 0.32), y=0.5)
    schlaubi(glow="gold", glow_power=4.0, rot_z=math.radians(-35))
    book((-0.2, 0.1, 0), -0.4, (0.5, 0.15, 0.12))
    book((-0.2, 0.1, 0.025), -0.2, (0.15, 0.2, 0.3))
    area_light("dusk", (0.9, 0.6, 0.6), (math.radians(60), 0, math.radians(125)), 1.5, 25, (1.0, 0.55, 0.35))
    camera((-0.05, -0.4, 0.11), (0, 0, 0.055), lens=65, fstop=2.8, exposure=-0.6)


def scene_cooling():
    world((0.6, 0.65, 0.72), 0.3)
    desk()
    wall(y=0.5)
    schlaubi(glow="turquoise", glow_power=2.5, rot_z=math.radians(-60))
    area_light("window", (0.9, -0.6, 0.7), (math.radians(60), 0, math.radians(55)), 1.0, 30, (1, 0.97, 0.93))
    area_light("rim", (-0.6, 0.5, 0.4), (math.radians(60), 0, math.radians(-140)), 0.6, 20, (0.85, 0.9, 1))
    camera((0.06, -0.36, 0.13), (0.01, 0.0, 0.05), lens=60, fstop=5.6, exposure=-0.7)


def scene_brain():
    world((0.45, 0.42, 0.4), 0.25)
    shelf = wood("Shelf", (0.6, 0.45, 0.3), (0.5, 0.35, 0.22), scale=5)
    box("shelf", (1.2, 0.35, 0.03), (0, 0.1, -0.015), shelf)
    wall(color=(0.78, 0.76, 0.72), y=0.3)
    laptop((-0.12, 0.1, 0), 0.0, open_deg=180, color=(0.25, 0.26, 0.28))
    hdd((0.12, 0.12, 0), 0.15)
    hdd((0.12, 0.12, 0.02), 0.1)
    box("led", (0.003, 0.003, 0.001), (0.15, 0.06, 0.0405), principled("Led", (0.1, 1, 0.3), 0.3, emission=(0.1, 1, 0.3), strength=30))
    schlaubi((0.2, -0.02, 0), glow="violet", glow_power=2.0, rot_z=math.radians(-20))
    area_light("lamp", (0.5, -0.4, 0.7), (math.radians(45), 0, math.radians(50)), 0.6, 50, (1, 0.85, 0.7))
    area_light("fill", (-0.6, -0.5, 0.5), (math.radians(60), 0, math.radians(-50)), 0.8, 15, (0.9, 0.93, 1))
    camera((0.05, -0.75, 0.3), (0.02, 0.0, 0.04), lens=50, fstop=6.3, exposure=-0.6)


def scene_analysis():
    world((0.55, 0.58, 0.62), 0.3)
    desk()
    wall(y=0.6)
    laptop((0.0, 0.15, 0), 0.0, open_deg=110, screen_img=f"{TEX}/laptop_chart.png")
    schlaubi((0.2, -0.05, 0), glow="amber", glow_power=2.0, rot_z=math.radians(-30))
    phone((-0.2, -0.13, 0.004), math.radians(15))
    mug((-0.28, 0.17, 0))
    area_light("window", (-0.9, -0.5, 0.9), (math.radians(60), 0, math.radians(-55)), 1.4, 40, (1, 0.97, 0.93))
    area_light("fill", (0.8, -0.6, 0.5), (math.radians(65), 0, math.radians(50)), 0.8, 15, (0.9, 0.93, 1))
    camera((0.02, -0.66, 0.3), (0.0, 0.02, 0.07), lens=30, fstop=5.6, exposure=-0.6)


SCENES = {
    "desk": scene_desk, "cafe": scene_cafe, "show": scene_show, "insight": scene_insight,
    "cooling": scene_cooling, "brain": scene_brain, "analysis": scene_analysis,
}

if __name__ == "__main__":
    reset()
    SCENES[SCENE]()
    bpy.context.scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
