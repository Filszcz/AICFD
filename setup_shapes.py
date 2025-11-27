import os

# Create directory
SHAPE_DIR = "shapes"
os.makedirs(SHAPE_DIR, exist_ok=True)

def write_file(filename, content):
    filepath = os.path.join(SHAPE_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Created {filepath}")

# 1. __init__.py
write_file("__init__.py", "")

# 2. Straight Pipe
write_file("straight.py", """
def generate(L, D, dens_mult):
    r, z = D / 2.0, 0.05
    base_y = int(20 * dens_mult)
    if base_y % 2 != 0: base_y += 1
    x_cells = int((L / D) * base_y)
    
    return f'''
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z}) ({L} {-r} {z}) ({L} {r} {z}) (0 {r} {z})
        );
        blocks ( hex (0 1 2 3 4 5 6 7) ({x_cells} {base_y} 1) simpleGrading (1 1 1) );
        edges ();
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((1 2 6 5)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7)); }}
        );
        mergePatchPairs ();
    '''
""")

# 3. Bends (Grouped 90 and 45)
write_file("bends.py", """
import math

def generate_90(L, D, dens_mult):
    r, z = D / 2.0, 0.05
    R_inner, R_outer = D, 2.0*D
    base_cells = int(20 * dens_mult)
    if base_cells % 2 != 0: base_cells += 1
    l_cells = int((L / D) * base_cells)
    arc_cells = int(2.4 * base_cells)

    cx, cy = L, -r - R_inner
    p2_in_x, p2_in_y = cx + R_inner, cy
    p2_out_x, p2_out_y = cx + R_outer, cy
    p3_in_x, p3_in_y = p2_in_x, p2_in_y - L
    p3_out_x, p3_out_y = p2_out_x, p2_out_y - L
    
    theta = math.radians(45)
    m_in_x = cx + R_inner * math.sin(theta)
    m_in_y = cy + R_inner * math.cos(theta)
    m_out_x = cx + R_outer * math.sin(theta)
    m_out_y = cy + R_outer * math.cos(theta)

    return f'''
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z})  ({L} {-r} {z})  ({L} {r} {z})  (0 {r} {z})
            ({p2_in_x} {p2_in_y} {-z}) ({p2_out_x} {p2_out_y} {-z})
            ({p2_in_x} {p2_in_y} {z})  ({p2_out_x} {p2_out_y} {z})
            ({p3_in_x} {p3_in_y} {-z}) ({p3_out_x} {p3_out_y} {-z})
            ({p3_in_x} {p3_in_y} {z})  ({p3_out_x} {p3_out_y} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (1 8 9 2 5 10 11 6) ({arc_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (8 12 13 9 10 14 15 11) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
        );
        edges
        (
            arc 1 8 ({m_in_x} {m_in_y} {-z})
            arc 5 10 ({m_in_x} {m_in_y} {z})
            arc 2 9 ({m_out_x} {m_out_y} {-z})
            arc 6 11 ({m_out_x} {m_out_y} {z})
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((12 13 15 14)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2) (1 8 10 5) (9 2 6 11) (8 12 14 10) (13 9 11 15)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7) (1 2 9 8) (5 10 11 6) (8 9 13 12) (10 14 15 11)); }}
        );
        mergePatchPairs ();
    '''

def generate_45(L, D, dens_mult):
    r, z = D / 2.0, 0.05
    R_inner, R_outer = D, 2.0*D
    base_cells = int(20 * dens_mult)
    if base_cells % 2 != 0: base_cells += 1
    l_cells = int((L / D) * base_cells)
    arc_cells = int(1.2 * base_cells)
    
    sin45, cos45 = math.sin(math.radians(45)), math.cos(math.radians(45))
    cx, cy = L, -r - R_inner
    
    p2_in_x, p2_in_y = cx + R_inner * sin45, cy + R_inner * cos45
    p2_out_x, p2_out_y = cx + R_outer * sin45, cy + R_outer * cos45
    
    p3_in_x, p3_in_y = p2_in_x + L*cos45, p2_in_y - L*sin45
    p3_out_x, p3_out_y = p2_out_x + L*cos45, p2_out_y - L*sin45

    m_in_x = cx + R_inner * math.sin(math.radians(22.5))
    m_in_y = cy + R_inner * math.cos(math.radians(22.5))
    m_out_x = cx + R_outer * math.sin(math.radians(22.5))
    m_out_y = cy + R_outer * math.cos(math.radians(22.5))

    return f'''
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z})  ({L} {-r} {z})  ({L} {r} {z})  (0 {r} {z})
            ({p2_in_x} {p2_in_y} {-z}) ({p2_out_x} {p2_out_y} {-z})
            ({p2_in_x} {p2_in_y} {z})  ({p2_out_x} {p2_out_y} {z})
            ({p3_in_x} {p3_in_y} {-z}) ({p3_out_x} {p3_out_y} {-z})
            ({p3_in_x} {p3_in_y} {z})  ({p3_out_x} {p3_out_y} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (1 8 9 2 5 10 11 6) ({arc_cells} {base_cells} 1) simpleGrading (1 1 1)
            hex (8 12 13 9 10 14 15 11) ({l_cells} {base_cells} 1) simpleGrading (1 1 1)
        );
        edges
        (
            arc 1 8 ({m_in_x} {m_in_y} {-z})
            arc 5 10 ({m_in_x} {m_in_y} {z})
            arc 2 9 ({m_out_x} {m_out_y} {-z})
            arc 6 11 ({m_out_x} {m_out_y} {z})
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((12 13 15 14)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2) (1 8 10 5) (9 2 6 11) (8 12 14 10) (13 9 11 15)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7) (1 2 9 8) (5 10 11 6) (8 9 13 12) (10 14 15 11)); }}
        );
        mergePatchPairs ();
    '''
""")

# 4. Tees
write_file("tee.py", """
def generate(L, D, dens_mult, mode="split"):
    r, z = D / 2.0, 0.05
    n_D = int(20 * dens_mult)
    if n_D % 2 != 0: n_D += 1
    n_L = int((L/D) * n_D)

    p_left = "inlet_left" if mode == "opposed" else "inlet"
    p_right = "inlet_right" if mode == "opposed" else "outlet_right"
    p_top = "outlet_top" if mode == "opposed" else "outlet_top"

    return f'''
        vertices
        (
            (0 {-r} {-z})   ({L} {-r} {-z})    ({L} {r} {-z})    (0 {r} {-z})
            (0 {-r} {z})    ({L} {-r} {z})     ({L} {r} {z})     (0 {r} {z})
            ({L+D} {-r} {-z}) ({L+2*L} {-r} {-z}) ({L+2*L} {r} {-z}) ({L+D} {r} {-z})
            ({L+D} {-r} {z})  ({L+2*L} {-r} {z})  ({L+2*L} {r} {z})  ({L+D} {r} {z})
            ({L} {r+L} {-z}) ({L+D} {r+L} {-z})
            ({L} {r+L} {z})  ({L+D} {r+L} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({n_L} {n_D} 1) simpleGrading (1 1 1)
            hex (1 8 11 2 5 12 15 6) ({n_D} {n_D} 1) simpleGrading (1 1 1)
            hex (8 9 10 11 12 13 14 15) ({n_L} {n_D} 1) simpleGrading (1 1 1)
            hex (2 11 17 16 6 15 19 18) ({n_D} {n_L} 1) simpleGrading (1 1 1)
        );
        edges ();
        boundary
        (
            {p_left}  {{ type patch; faces ((0 4 7 3)); }}
            {p_right} {{ type patch; faces ((9 10 14 13)); }}
            {p_top}   {{ type patch; faces ((17 16 18 19)); }}
            walls  {{ type wall;  faces (
                (0 1 5 4) (3 7 6 2)
                (1 8 12 5)
                (8 9 13 12) (10 11 15 14)
                (11 17 19 15) (16 2 6 18)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 3 2 1) (4 5 6 7) 
                (1 2 11 8) (5 6 15 12)
                (8 11 10 9) (12 15 14 13)
                (2 16 17 11) (6 18 19 15)
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# 5. Taper
write_file("taper.py", """
def generate(L, D, dens_mult, mode):
    ratio = 0.5
    if mode == "taper_in": d1, d2 = D, D * ratio
    else: d1, d2 = D * ratio, D
    r1, r2 = d1/2.0, d2/2.0
    z = 0.05
    n_y = int(20 * dens_mult)
    if n_y % 2 != 0: n_y += 1
    n_x = int((L/3.0 / D) * n_y)
    
    x0, x1, x2, x3 = 0, L/3.0, 2*L/3.0, L
    
    return f'''
        vertices
        (
            ({x0} {-r1} {-z}) ({x1} {-r1} {-z}) ({x1} {r1} {-z}) ({x0} {r1} {-z})
            ({x0} {-r1} {z})  ({x1} {-r1} {z})  ({x1} {r1} {z})  ({x0} {r1} {z})
            ({x2} {-r2} {-z}) ({x2} {r2} {-z})
            ({x2} {-r2} {z})  ({x2} {r2} {z})
            ({x3} {-r2} {-z}) ({x3} {r2} {-z})
            ({x3} {-r2} {z})  ({x3} {r2} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({n_x} {n_y} 1) simpleGrading (1 1 1)
            hex (1 8 9 2 5 10 11 6) ({n_x} {n_y} 1) simpleGrading (1 1 1)
            hex (8 12 13 9 10 14 15 11) ({n_x} {n_y} 1) simpleGrading (1 1 1)
        );
        edges ();
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((12 13 15 14)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2) (1 8 10 5) (2 6 11 9) (8 12 14 10) (9 11 15 13)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7) (1 2 9 8) (5 6 11 10) (8 9 13 12) (10 11 15 14)); }}
        );
        mergePatchPairs ();
    '''
""")

# --- NEW SHAPES ---

# 6. Valve (Gate/Orifice)
write_file("valve.py", """
def generate(L, D, dens_mult):
    # Represents a partially closed gate valve or orifice plate
    # Split into 3 x-sections: Upstream, Valve, Downstream
    # Valve section has fluid in middle, walls on top/bottom
    
    r = D / 2.0
    z = 0.05
    
    valve_len = 0.2 * D
    opening_ratio = 0.4 # 40% open in the center
    
    r_open = r * opening_ratio
    
    x1 = (L - valve_len) / 2.0
    x2 = x1 + valve_len
    x3 = L
    
    ny = int(20 * dens_mult)
    if ny % 2 != 0: ny += 1
    
    nx_main = int((x1 / D) * ny)
    nx_valve = int((valve_len / D) * ny)
    if nx_valve < 2: nx_valve = 2
    
    # We need graded vertices in Y to match the opening
    # We will define 3 blocks in Y for the WHOLE domain to keep mesh consistent
    # Y-zones: [-r, -r_open], [-r_open, r_open], [r_open, r]
    
    ny_outer = int(ny * (1-opening_ratio)/2)
    ny_inner = ny - 2*ny_outer
    
    return f'''
        vertices
        (
            (0 {-r} {-z})      ({x1} {-r} {-z})      ({x2} {-r} {-z})      ({x3} {-r} {-z})
            (0 {-r_open} {-z}) ({x1} {-r_open} {-z}) ({x2} {-r_open} {-z}) ({x3} {-r_open} {-z})
            (0 {r_open} {-z})  ({x1} {r_open} {-z})  ({x2} {r_open} {-z})  ({x3} {r_open} {-z})
            (0 {r} {-z})       ({x1} {r} {-z})       ({x2} {r} {-z})       ({x3} {r} {-z})

            (0 {-r} {z})      ({x1} {-r} {z})      ({x2} {-r} {z})      ({x3} {-r} {z})
            (0 {-r_open} {z}) ({x1} {-r_open} {z}) ({x2} {-r_open} {z}) ({x3} {-r_open} {z})
            (0 {r_open} {z})  ({x1} {r_open} {z})  ({x2} {r_open} {z})  ({x3} {r_open} {z})
            (0 {r} {z})       ({x1} {r} {z})       ({x2} {r} {z})       ({x3} {r} {z})
        );
        blocks
        (
            // Inlet Section (3 vertical blocks)
            hex (0 1 5 4 16 17 21 20) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 20 21 25 24) ({nx_main} {ny_inner} 1) simpleGrading (1 1 1)
            hex (8 9 13 12 24 25 29 28) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)

            // Valve Section (Only Middle Block exists, Top/Bottom are voids/walls)
            hex (5 6 10 9 21 22 26 25) ({nx_valve} {ny_inner} 1) simpleGrading (1 1 1)

            // Outlet Section (3 vertical blocks)
            hex (2 3 7 6 18 19 23 22) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 22 23 27 26) ({nx_main} {ny_inner} 1) simpleGrading (1 1 1)
            hex (10 11 15 14 26 27 31 30) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 16 20 4) (4 20 24 8) (8 24 28 12)); }}
            outlet {{ type patch; faces ((2 3 19 18) (6 7 23 22) (10 11 27 30)); }}
            walls  {{ type wall;  faces (
                // Main pipe walls
                (0 1 17 16) (1 2 18 17) (2 3 19 18)
                (12 13 29 28) (13 14 30 29) (14 15 31 30)
                // Valve Faces (The "Steps")
                (1 5 21 17) (5 6 22 21) (6 2 18 22) 
                (13 9 25 29) (9 10 26 25) (10 14 30 26) 
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (8 12 13 9) // Inlet Front
                (16 17 21 20) (20 21 25 24) (24 25 29 28) // Inlet Back
                (5 9 10 6) // Valve Front
                (21 22 26 25) // Valve Back
                (2 6 7 3) (6 10 11 7) (10 14 15 11) // Outlet Front
                (18 19 23 22) (22 23 27 26) (26 27 31 30) // Outlet Back
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# 7. Baffle
write_file("baffle.py", """
def generate(L, D, dens_mult):
    # A generic baffle extending from the bottom wall
    r = D / 2.0
    z = 0.05
    baffle_h = 0.5 * D
    baffle_t = 0.1 * D # Thickness
    
    x1 = (L - baffle_t) / 2.0
    x2 = x1 + baffle_t
    x3 = L
    
    ny = int(20 * dens_mult)
    nx_main = int((x1 / D) * ny)
    nx_baffle = int((baffle_t / D) * ny)
    if nx_baffle < 2: nx_baffle = 2
    
    # Y-split: [-r, -r + h] (Baffle zone), [-r+h, r] (Flow zone)
    y_split = -r + baffle_h
    ny_baffle = int(ny * 0.5)
    ny_flow = ny - ny_baffle
    
    return f'''
        vertices
        (
            (0 {-r} {-z})      ({x1} {-r} {-z})      ({x2} {-r} {-z})      ({x3} {-r} {-z})
            (0 {y_split} {-z}) ({x1} {y_split} {-z}) ({x2} {y_split} {-z}) ({x3} {y_split} {-z})
            (0 {r} {-z})       ({x1} {r} {-z})       ({x2} {r} {-z})       ({x3} {r} {-z})

            (0 {-r} {z})      ({x1} {-r} {z})      ({x2} {-r} {z})      ({x3} {-r} {z})
            (0 {y_split} {z}) ({x1} {y_split} {z}) ({x2} {y_split} {z}) ({x3} {y_split} {z})
            (0 {r} {z})       ({x1} {r} {z})       ({x2} {r} {z})       ({x3} {r} {z})
        );
        blocks
        (
            // Left (Bottom and Top)
            hex (0 1 5 4 12 13 17 16) ({nx_main} {ny_baffle} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 16 17 21 20) ({nx_main} {ny_flow} 1) simpleGrading (1 1 1)
            
            // Middle (Only Top is fluid)
            hex (5 6 10 9 17 18 22 21) ({nx_baffle} {ny_flow} 1) simpleGrading (1 1 1)
            
            // Right (Bottom and Top)
            hex (2 3 7 6 14 15 19 18) ({nx_main} {ny_baffle} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 18 19 23 22) ({nx_main} {ny_flow} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 12 16 4) (4 16 20 8)); }}
            outlet {{ type patch; faces ((2 3 15 14) (6 7 19 18) (10 11 23 22) (3 15 19 7)); }} 
            walls  {{ type wall;  faces (
                (0 1 13 12) (1 5 17 13) (5 6 18 17) (6 2 14 18) (2 3 15 14)
                (8 9 21 20) (9 10 22 21) (10 11 23 22)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (12 13 17 16) (16 17 21 20) // Left
                (5 9 10 6) (17 18 22 21) // Middle
                (2 6 7 3) (6 10 11 7) (14 15 19 18) (18 19 23 22) // Right
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# 8. Obstacle (Square Cylinder)
write_file("obstacle.py", """
def generate(L, D, dens_mult):
    # Square obstacle in the middle of flow
    r = D / 2.0
    z = 0.05
    obs_size = 0.3 * D
    
    x1 = (L - obs_size) / 2.0
    x2 = x1 + obs_size
    x3 = L
    
    y1 = -obs_size / 2.0
    y2 = obs_size / 2.0
    
    ny = int(20 * dens_mult)
    nx_main = int((x1 / D) * ny)
    nx_obs = int((obs_size / D) * ny)
    if nx_obs < 2: nx_obs = 2
    
    ny_mid = nx_obs
    ny_outer = int((ny - ny_mid) / 2)
    
    return f'''
        vertices
        (
            (0 {-r} {-z}) ({x1} {-r} {-z}) ({x2} {-r} {-z}) ({x3} {-r} {-z})
            (0 {y1} {-z}) ({x1} {y1} {-z}) ({x2} {y1} {-z}) ({x3} {y1} {-z})
            (0 {y2} {-z}) ({x1} {y2} {-z}) ({x2} {y2} {-z}) ({x3} {y2} {-z})
            (0 {r} {-z})  ({x1} {r} {-z})  ({x2} {r} {-z})  ({x3} {r} {-z})

            (0 {-r} {z}) ({x1} {-r} {z}) ({x2} {-r} {z}) ({x3} {-r} {z})
            (0 {y1} {z}) ({x1} {y1} {z}) ({x2} {y1} {z}) ({x3} {y1} {z})
            (0 {y2} {z}) ({x1} {y2} {z}) ({x2} {y2} {z}) ({x3} {y2} {z})
            (0 {r} {z})  ({x1} {r} {z})  ({x2} {r} {z})  ({x3} {r} {z})
        );
        blocks
        (
            // Inlet 3 blocks
            hex (0 1 5 4 16 17 21 20) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 20 21 25 24) ({nx_main} {ny_mid} 1) simpleGrading (1 1 1)
            hex (8 9 13 12 24 25 29 28) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            
            // Middle (Bottom and Top only)
            hex (1 2 6 5 17 18 22 21) ({nx_obs} {ny_outer} 1) simpleGrading (1 1 1)
            hex (9 10 14 13 25 26 30 29) ({nx_obs} {ny_outer} 1) simpleGrading (1 1 1)
            
            // Outlet 3 blocks
            hex (2 3 7 6 18 19 23 22) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 22 23 27 26) ({nx_main} {ny_mid} 1) simpleGrading (1 1 1)
            hex (10 11 15 14 26 27 31 30) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 16 20 4) (4 20 24 8) (8 24 28 12)); }}
            outlet {{ type patch; faces ((2 3 19 18) (6 7 23 22) (10 11 27 30)); }}
            walls  {{ type wall;  faces (
                (0 1 17 16) (1 2 18 17) (2 3 19 18) // Bottom
                (12 13 29 28) (13 14 30 29) (14 15 31 30) // Top
                // Obstacle
                (5 6 22 21) (6 10 26 22) (10 9 25 26) (9 5 21 25)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (8 12 13 9) (16 17 21 20) (20 21 25 24) (24 25 29 28)
                (1 5 6 2) (9 13 14 10) (17 18 22 21) (25 26 30 29)
                (2 6 7 3) (6 10 11 7) (10 14 15 11) (18 19 23 22) (22 23 27 26) (26 27 31 30)
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# 9. Backward Facing Step
write_file("step.py", """
def generate(L, D, dens_mult):
    # Inlet is small (h), Outlet is large (H)
    # D here acts as the Inlet Diameter (h)
    # H = 2 * D
    h = D
    H = 2.0 * D
    z = 0.05
    
    # Inlet Section (Length L/3)
    # Outlet Section (Length 2L/3)
    x_step = L / 3.0
    x_end = L
    
    nx_inlet = int(15 * dens_mult)
    nx_outlet = int(30 * dens_mult)
    ny_h = int(15 * dens_mult)
    
    return f'''
        vertices
        (
            (0 0 {-z})       ({x_step} 0 {-z})       ({x_end} 0 {-z})
            (0 {h} {-z})     ({x_step} {h} {-z})     ({x_end} {h} {-z})
            ({x_step} {H} {-z}) ({x_end} {H} {-z})
            
            (0 0 {z})       ({x_step} 0 {z})       ({x_end} 0 {z})
            (0 {h} {z})     ({x_step} {h} {z})     ({x_end} {h} {z})
            ({x_step} {H} {z}) ({x_end} {H} {z})
        );
        blocks
        (
            hex (0 1 4 3 7 8 11 10) ({nx_inlet} {ny_h} 1) simpleGrading (1 1 1)
            hex (1 2 5 4 8 9 12 11) ({nx_outlet} {ny_h} 1) simpleGrading (1 1 1)
            hex (4 5 6 13 11 12 14 13) ({nx_outlet} {ny_h} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 10 11 3)); }}
            outlet {{ type patch; faces ((2 5 12 9) (5 6 14 12)); }}
            walls  {{ type wall;  faces (
                (0 1 8 7) (1 2 9 8) // Bottom
                (3 4 11 10) (13 6 14 13) // Top
                (4 13 13 11) // The Step Face (Vertical)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 3 4 1) (1 4 5 2) (4 13 6 5)
                (7 8 11 10) (8 9 12 11) (11 12 14 13)
            ); }}
        );
        mergePatchPairs ();
    '''
""")

print("Shape library created successfully.")