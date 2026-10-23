import bpy
import math
from mathutils import Vector
import os


# Procedural, editable Blender scene for the wedding invitation hero.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, color, metallic=0.0, roughness=0.38):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


skin = material("Warm honey skin", (0.63, 0.31, 0.17), roughness=0.48)
skin_light = material("Soft warm skin", (0.82, 0.52, 0.36), roughness=0.4)
hair = material("Espresso hair", (0.035, 0.018, 0.02), roughness=0.3)
ink = material("Dark eyes", (0.018, 0.012, 0.014), roughness=0.22)
iris = material("Warm brown irises", (0.24, 0.075, 0.025), roughness=0.24)
blush = material("Rosy cheeks", (0.76, 0.25, 0.23), roughness=0.5)
ivory = material("Warm ivory silk", (0.96, 0.88, 0.73), roughness=0.28)
red = material("Wedding crimson silk", (0.58, 0.018, 0.055), metallic=0.08, roughness=0.24)
red_light = material("Vermilion silk", (0.77, 0.045, 0.085), metallic=0.06, roughness=0.26)
green = material("Emerald silk", (0.025, 0.24, 0.12), metallic=0.06, roughness=0.27)
marigold = material("Marigold petals", (1.0, 0.31, 0.015), roughness=0.56)
jasmine = material("Jasmine petals", (1.0, 0.92, 0.72), roughness=0.58)
leaf = material("Leaf green", (0.035, 0.18, 0.07), roughness=0.46)
gold = material("Antique temple gold", (0.74, 0.46, 0.12), metallic=0.72, roughness=0.24)
gold_light = material("Polished gold", (0.96, 0.71, 0.25), metallic=0.65, roughness=0.2)
gem = material("Ruby jewel", (0.48, 0.018, 0.045), metallic=0.25, roughness=0.2)
white = material("Eye whites", (0.98, 0.88, 0.72), roughness=0.4)


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def uv(name, loc, scale, mat, rot=None, seg=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if rot:
        obj.rotation_euler = rot
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)


def cylinder_between(name, a, b, radius, mat, radius2=None, vertices=16):
    a, b = Vector(a), Vector(b)
    direction = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                    radius2=radius if radius2 is None else radius2,
                                    depth=direction.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    bevel = obj.modifiers.new("Soft toy edges", "BEVEL")
    bevel.width = min(radius * 0.32, 0.07)
    bevel.segments = 3
    obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return assign(obj, mat)


def profile(name, x, y, rings, mat, sides=48):
    verts, faces = [], []
    for z, rx, ry in rings:
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            verts.append((x + rx * math.cos(angle), y + ry * math.sin(angle), z))
    for j in range(len(rings) - 1):
        for i in range(sides):
            a = j * sides + i
            b = j * sides + (i + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides - 1, -1, -1)))
    start = (len(rings) - 1) * sides
    faces.append(tuple(start + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    bevel = obj.modifiers.new("Silhouette softness", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    obj.modifiers.new("Soft normals", "WEIGHTED_NORMAL")
    return obj


def curve_line(name, points, mat, bevel=0.018):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return assign(obj, mat)


def ribbon(name, centerline, width, y, mat):
    verts, faces = [], []
    for i, (x, z) in enumerate(centerline):
        prev = centerline[max(0, i - 1)]
        nxt = centerline[min(len(centerline) - 1, i + 1)]
        dx, dz = nxt[0] - prev[0], nxt[1] - prev[1]
        length = math.sqrt(dx * dx + dz * dz) or 1
        nx, nz = -dz / length * width / 2, dx / length * width / 2
        verts.extend([(x + nx, y, z + nz), (x - nx, y, z - nz)])
    for i in range(len(centerline) - 1):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("Silk thickness", "SOLIDIFY")
    solid.thickness = 0.018
    bevel = obj.modifiers.new("Soft sari folds", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 3
    return obj


def torus(name, loc, major, minor, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=32, minor_segments=8,
                                     location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)


def face(x, z, female=False):
    # Face looks toward the camera at negative Y.
    face_mat = skin_light if female else skin
    uv("Porcelain doll face", (x, -0.075, z), (0.36, 0.30, 0.41), face_mat)
    uv("Soft ears", (x - 0.32, -0.02, z - 0.02), (0.075, 0.11, 0.13), face_mat)
    uv("Soft ears", (x + 0.32, -0.02, z - 0.02), (0.075, 0.11, 0.13), face_mat)
    # Tiny bright eyes, set gently into the cheeks.
    for ex in (x - 0.135, x + 0.135):
        uv("Eye white", (ex, -0.345, z + 0.012), (0.084, 0.039, 0.099), white)
        uv("Iris", (ex, -0.38, z + 0.005), (0.050, 0.024, 0.066), iris)
        uv("Pupil", (ex, -0.399, z + 0.005), (0.029, 0.014, 0.044), ink)
        uv("Eye glint", (ex - 0.012, -0.414, z + 0.027), (0.014, 0.008, 0.017), white, seg=16, rings=8)
        curve_line("Fine upper lash", [(ex - 0.083, -0.36, z + 0.012),
                                       (ex, -0.391, z + 0.108),
                                       (ex + 0.083, -0.36, z + 0.017)], hair, 0.012)
        curve_line("Soft eyebrow", [(ex - 0.075, -0.35, z + 0.142),
                                    (ex, -0.37, z + 0.165),
                                    (ex + 0.075, -0.35, z + 0.145)], hair, 0.018)
    for side in (-1, 1):
        uv("Doll cheek blush", (x + side * 0.21, -0.32, z - 0.12), (0.07, 0.018, 0.035), blush, seg=20, rings=12)
    uv("Little nose", (x, -0.39, z - 0.065), (0.05, 0.055, 0.076), face_mat, seg=20, rings=12)
    curve_line("Gentle smile", [(x - 0.075, -0.36, z - 0.18),
                                (x, -0.383, z - 0.205),
                                (x + 0.075, -0.36, z - 0.18)], gem, 0.014)


def flower_garland(x, female=False):
    # Tiny alternating jasmine and marigold blossoms sit over each outfit.
    pts = [(x - 0.29, -0.27, 1.73), (x - 0.25, -0.335, 1.43),
           (x - 0.12, -0.36, 1.12), (x, -0.365, 0.98),
           (x + 0.12, -0.36, 1.12), (x + 0.25, -0.335, 1.43),
           (x + 0.29, -0.27, 1.73)]
    curve_line("Jasmine garland thread", pts, leaf, 0.016)
    steps = 42
    segments = len(pts) - 1
    for i in range(steps):
        t = i / (steps - 1) * segments
        seg = min(int(t), segments - 1)
        u = t - seg
        a, b = Vector(pts[seg]), Vector(pts[seg + 1])
        pos = a.lerp(b, u)
        flower_mat = marigold if i % 8 in (0, 1) else jasmine
        radius = 0.050 if i % 8 in (0, 1) else 0.042
        uv("Wedding garland blossom", pos, (radius, radius * 0.7, radius), flower_mat, seg=16, rings=10)


def skirt_brocade(x):
    # Repeated gold buttas give the silk skirt a handwoven festive glint.
    rows = [(0.48, 0.47), (0.62, 0.43), (0.76, 0.36), (0.89, 0.30)]
    for row, (z, rx) in enumerate(rows):
        for col in range(-3, 4):
            ox = col * (rx / 3.4)
            curve = math.sqrt(max(0.12, 1 - (ox / (rx + 0.001)) ** 2))
            y = -0.02 - 0.31 * curve - 0.012
            uv("Woven gold butta", (x + ox, y, z), (0.026, 0.012, 0.042 if (row + col) % 2 else 0.03),
               gold_light, seg=12, rings=8)


def hands_in_namaste(x, base_z, female=False):
    skin_mat = skin_light if female else skin
    # Forearms fold inward from both sides; joined palms sit below the face.
    shoulder_z = 1.35
    for side in (-1, 1):
        cylinder_between("Folded upper arm", (x + side * 0.30, -0.16, shoulder_z),
                         (x + side * 0.17, -0.40, base_z + 0.10), 0.115, red if female else ivory, 0.105)
        cylinder_between("Folded forearm", (x + side * 0.17, -0.40, base_z + 0.10),
                         (x + side * 0.025, -0.51, base_z + 0.25), 0.085, skin_mat, 0.075)
        uv("Namaste palm", (x + side * 0.043, -0.535, base_z + 0.35), (0.055, 0.052, 0.14), skin_mat)
    # Overlapping rounded palms keep the greeting readable at this small scale.
    for side in (-1, 1):
        uv("Joined namaste palm", (x + side * 0.027, -0.565, base_z + 0.48),
           (0.047, 0.045, 0.17), skin_mat)
    uv("Joined hands highlight", (x, -0.59, base_z + 0.49), (0.025, 0.016, 0.025), gold_light, seg=16, rings=8)


def bride(x):
    profile("Crimson lehenga", x, 0.02,
            [(0.18, 0.45, 0.31), (0.27, 0.54, 0.34), (0.50, 0.48, 0.31),
             (0.78, 0.34, 0.25), (1.03, 0.23, 0.19), (1.12, 0.22, 0.18)], red)
    # Broad, scalloped gold hem and two delicate silk borders.
    skirt_brocade(x)
    for z, radius in ((0.24, 0.535), (0.28, 0.53), (0.33, 0.515), (0.46, 0.49)):
        torus("Sari hem and zari borders", (x, 0.02, z), radius, 0.018, gold_light if z == 0.28 else gold)
    torus("Emerald hem piping", (x, 0.02, 0.215), 0.54, 0.026, green)
    profile("Gold waist band", x, 0.0,
            [(1.00, 0.235, 0.195), (1.08, 0.235, 0.195)], gold)
    profile("Emerald green blouse", x, 0.0,
            [(1.02, 0.23, 0.19), (1.15, 0.25, 0.20), (1.40, 0.31, 0.22),
             (1.52, 0.28, 0.20)], green)
    # Silk veil forms a soft red mantle behind the head and shoulders.
    profile("Bridal veil", x, 0.11,
            [(1.15, 0.42, 0.08), (1.48, 0.44, 0.075), (1.78, 0.38, 0.06),
             (2.03, 0.30, 0.04)], red)
    # Rebuild blouse and face in front of the veil.
    profile("Green blouse front", x, -0.115,
            [(1.02, 0.23, 0.10), (1.15, 0.25, 0.10), (1.40, 0.31, 0.10),
             (1.52, 0.28, 0.08)], green)
    ribbon("Diagonal crimson pallu", [(x + 0.24, 1.52), (x + 0.15, 1.40),
                                       (x + 0.02, 1.24), (x - 0.14, 1.06)], 0.18, -0.245, red_light)
    curve_line("Pallu zari edge", [(x + 0.30, -0.255, 1.52), (x + 0.20, -0.255, 1.38),
                                   (x + 0.07, -0.26, 1.22), (x - 0.09, -0.25, 1.06)], gold_light, 0.018)
    # Sleeves and little golden cuffs.
    for side in (-1, 1):
        uv("Bridal sleeve", (x + side * 0.29, -0.11, 1.34), (0.15, 0.16, 0.19), green)
        torus("Sleeve zari piping", (x + side * 0.31, -0.11, 1.22), 0.105, 0.014, gold)
    face(x, 2.12, True)
    # Hair cap, long side locks, and decorated maang tikka.
    uv("Bride hair crown", (x, 0.0, 2.37), (0.35, 0.30, 0.23), hair)
    uv("Bride bun", (x, 0.20, 2.26), (0.19, 0.20, 0.24), hair)
    # A long dark braid with jasmine buds drapes over her left shoulder.
    for i in range(17):
        z_braid = 1.94 - i * 0.087
        side_offset = -0.31 + (0.035 if i % 2 else -0.02)
        uv("Braided hair plait", (x + side_offset, -0.16, z_braid), (0.085, 0.075, 0.10), hair, seg=20, rings=12)
        if i % 3 == 0:
            uv("Braid jasmine bud", (x + side_offset - 0.05, -0.205, z_braid), (0.032, 0.025, 0.035), jasmine, seg=12, rings=8)
    uv("Braid tassel", (x - 0.31, -0.16, 0.42), (0.085, 0.09, 0.15), hair)
    uv("Bindi", (x, -0.382, 2.14), (0.025, 0.012, 0.035), gem, seg=16, rings=8)
    cylinder_between("Maang tikka chain", (x, -0.365, 2.37), (x, -0.385, 2.16), 0.012, gold_light, vertices=10)
    uv("Maang tikka jewel", (x, -0.39, 2.31), (0.045, 0.02, 0.07), gold_light, seg=20, rings=12)
    for side in (-1, 1):
        torus("Jhumka earrings", (x + side * 0.34, -0.16, 2.00), 0.07, 0.017, gold_light, (math.pi / 2, 0, 0))
        uv("Ruby earring", (x + side * 0.34, -0.18, 1.98), (0.028, 0.022, 0.035), gem, seg=16, rings=8)
    # Two graceful necklaces.
    curve_line("Gold necklace", [(x - 0.22, -0.255, 1.51), (x - 0.16, -0.29, 1.37),
                                  (x, -0.30, 1.31), (x + 0.16, -0.29, 1.37),
                                  (x + 0.22, -0.255, 1.51)], gold_light, 0.022)
    curve_line("Long necklace", [(x - 0.18, -0.25, 1.48), (x - 0.12, -0.28, 1.25),
                                 (x, -0.30, 1.17), (x + 0.12, -0.28, 1.25),
                                 (x + 0.18, -0.25, 1.48)], gold, 0.017)
    uv("Necklace pendant", (x, -0.31, 1.17), (0.055, 0.025, 0.075), gold_light, seg=20, rings=12)
    flower_garland(x, True)
    hands_in_namaste(x, 1.22, True)


def groom(x):
    # Short, softly rounded trousers and embroidered sherwani.
    for side in (-1, 1):
        profile("Ivory churidar", x + side * 0.13, 0.0,
                [(0.18, 0.14, 0.14), (0.45, 0.13, 0.13), (0.83, 0.16, 0.15),
                 (0.98, 0.15, 0.15)], ivory, sides=32)
        uv("Ivory mojari", (x + side * 0.14, -0.10, 0.15), (0.17, 0.24, 0.09), gold, seg=24, rings=16)
    profile("Sherwani jacket", x, 0.0,
            [(0.72, 0.30, 0.20), (0.88, 0.33, 0.22), (1.25, 0.32, 0.22),
             (1.55, 0.30, 0.21), (1.68, 0.24, 0.19)], ivory)
    # Gold piping, buttons, and ceremonial red stole with zari edges.
    curve_line("Sherwani placket", [(x, -0.226, 0.78), (x, -0.235, 1.58)], gold, 0.018)
    for z in (0.96, 1.13, 1.30, 1.47):
        uv("Sherwani button", (x + 0.035, -0.25, z), (0.024, 0.018, 0.024), gold_light, seg=16, rings=8)
    profile("Ceremonial stole left", x - 0.23, -0.235,
            [(0.70, 0.075, 0.035), (1.10, 0.075, 0.035), (1.52, 0.10, 0.035),
             (1.66, 0.09, 0.03)], red)
    profile("Ceremonial stole right", x + 0.23, -0.235,
            [(0.70, 0.075, 0.035), (1.10, 0.075, 0.035), (1.52, 0.10, 0.035),
             (1.66, 0.09, 0.03)], red_light)
    for side in (-1, 1):
        xband = x + side * 0.23
        curve_line("Stole gold woven edge", [(xband - 0.06, -0.28, 0.73),
                                              (xband - 0.06, -0.28, 1.62)], gold_light, 0.012)
        curve_line("Stole gold woven edge", [(xband + 0.06, -0.28, 0.73),
                                              (xband + 0.06, -0.28, 1.62)], gold_light, 0.012)
    for side in (-1, 1):
        uv("Groom cuff", (x + side * 0.31, -0.17, 1.18), (0.12, 0.13, 0.075), gold)
    face(x, 2.12, False)
    uv("Groom hair", (x, 0.02, 2.36), (0.35, 0.30, 0.22), hair)
    uv("Swept groom quiff", (x - 0.05, -0.035, 2.49), (0.30, 0.25, 0.18), hair, rot=(0, -0.22, -0.12))
    for i in range(4):
        curve_line("Sculpted hair grooves", [(x - 0.23 + i * 0.045, -0.24, 2.43 + i * 0.012),
                                             (x - 0.04 + i * 0.035, -0.265, 2.53 + i * 0.008),
                                             (x + 0.17 + i * 0.018, -0.22, 2.49 - i * 0.012)], hair, 0.012)
    # Vermilion and gold forehead tilak, styled to match the reference dolls.
    uv("Groom forehead tilak", (x, -0.405, 2.31), (0.026, 0.012, 0.10), gem, seg=16, rings=10)
    curve_line("Tilak gold line", [(x - 0.23, -0.38, 2.35), (x, -0.417, 2.38),
                                   (x + 0.23, -0.38, 2.35)], gold_light, 0.016)
    flower_garland(x, False)
    hands_in_namaste(x, 1.22, False)


# A pair of friendly, big-headed wedding dolls, standing shoulder to shoulder.
bride(-0.67)
groom(0.67)

# Soft, warm studio lighting and a transparent backdrop for page compositing.
world = bpy.context.scene.world
world.color = (0.22, 0.16, 0.12)
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.21, 0.16, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

def area(name, loc, power, size, color, target):
    bpy.ops.object.light_add(type="AREA", location=loc)
    lamp = bpy.context.object
    lamp.name = name
    lamp.data.energy = power
    lamp.data.shape = "DISK"
    lamp.data.size = size
    lamp.data.color = color
    lamp.rotation_euler = (Vector(target) - lamp.location).to_track_quat("-Z", "Y").to_euler()

area("Large warm key", (-3.5, -4.0, 5.2), 520, 4.2, (1.0, 0.78, 0.58), (0, 0, 1.5))
area("Soft cream fill", (3.5, -3.0, 3.2), 340, 3.5, (1.0, 0.9, 0.72), (0, 0, 1.4))
area("Golden rim", (0.0, 1.8, 4.3), 420, 3.0, (1.0, 0.58, 0.28), (0, 0, 1.5))

bpy.ops.object.camera_add(location=(0, -9, 2.0))
camera = bpy.context.object
camera.name = "Invitation hero camera"
camera.rotation_euler = (Vector((0, 0, 1.47)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 3.95
bpy.context.scene.camera = camera

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = True
scene.render.resolution_percentage = 80
scene.render.image_settings.color_depth = "8"
asset_dir = os.path.dirname(os.path.abspath(__file__))
scene.render.filepath = os.path.join(asset_dir, "namaskaram-couple.png")
scene.view_settings.view_transform = "AgX"
scene.render.film_transparent = True
scene.camera.data.lens = 50
scene.render.image_settings.compression = 10
scene.render.use_file_extension = True

# Save the editable Blender project beside the generated render.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(asset_dir, "namaskaram-couple.blend"))
bpy.ops.render.render(write_still=True)
