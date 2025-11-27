import os
import math

SHAPE_DIR = "shapes"
os.makedirs(SHAPE_DIR, exist_ok=True)

def write_file(filename, content):
    filepath = os.path.join(SHAPE_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Generated {filepath}")

write_file("__init__.py", "")

# ---------------------------------------------------------------------------
# Common Helper
# ---------------------------------------------------------------------------
common_header = """
import math

def get_cells(length, cell_size, min_cells=2):
    if length <= 1e-6: return 1
    val = int(length / cell_size)
    return max(min_cells, val)
"""

# ---------------------------------------------------------------------------
# 1. Straight Pipe
# ---------------------------------------------------------------------------
write_file("straight.py", common_header + """
def generate(L, D, cell_size, **kwargs):
    r, z = D / 2.0, 0.05
    nx = get_cells(L, cell_size)
    ny = get_cells(D, cell_size, min_cells=10)
    
    return f'''
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z}) ({L} {-r} {z}) ({L} {r} {z}) (0 {r} {z})
        );
        blocks ( hex (0 1 2 3 4 5 6 7) ({nx} {ny} 1) simpleGrading (1 1 1) );
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

# ---------------------------------------------------------------------------
# 2. Bend
# ---------------------------------------------------------------------------
write_file("bend.py", common_header + """
def generate(L, D, cell_size, **kwargs):
    angle_deg = kwargs.get('bend_angle', 90.0)
    R_mid = D * kwargs.get('bend_radius', 1.5)
    r, z = D / 2.0, 0.05
    R_inner = R_mid - r
    R_outer = R_mid + r
    theta_rad = math.radians(angle_deg)
    arc_len = R_mid * theta_rad
    
    min_leg = 0.5 * D
    required_L = arc_len + (2 * min_leg)
    eff_L = max(L, required_L)
    leg_len = (eff_L - arc_len) / 2.0
    
    n_leg = get_cells(leg_len, cell_size)
    n_arc = get_cells(arc_len, cell_size * 0.6) 
    ny = get_cells(D, cell_size, min_cells=10)
    
    cx, cy = leg_len, -R_mid
    start_ang = math.pi / 2.0
    end_ang = start_ang - theta_rad
    mid_ang = start_ang - (theta_rad / 2.0)
    
    p2_in_x = cx + R_inner * math.cos(end_ang)
    p2_in_y = cy + R_inner * math.sin(end_ang)
    p2_out_x = cx + R_outer * math.cos(end_ang)
    p2_out_y = cy + R_outer * math.sin(end_ang)
    
    m_in_x = cx + R_inner * math.cos(mid_ang)
    m_in_y = cy + R_inner * math.sin(mid_ang)
    m_out_x = cx + R_outer * math.cos(mid_ang)
    m_out_y = cy + R_outer * math.sin(mid_ang)
    
    dx = math.sin(end_ang) * leg_len
    dy = -math.cos(end_ang) * leg_len
    
    p3_in_x, p3_in_y = p2_in_x + dx, p2_in_y + dy
    p3_out_x, p3_out_y = p2_out_x + dx, p2_out_y + dy
    
    y_top, y_bot = r, -r

    return f'''
        vertices
        (
            (0 {y_bot} {-z}) ({leg_len} {y_bot} {-z}) ({leg_len} {y_top} {-z}) (0 {y_top} {-z})
            (0 {y_bot} {z})  ({leg_len} {y_bot} {z})  ({leg_len} {y_top} {z})  (0 {y_top} {z})
            
            ({p2_in_x} {p2_in_y} {-z}) ({p2_out_x} {p2_out_y} {-z})
            ({p2_in_x} {p2_in_y} {z})  ({p2_out_x} {p2_out_y} {z})
            
            ({p3_in_x} {p3_in_y} {-z}) ({p3_out_x} {p3_out_y} {-z})
            ({p3_in_x} {p3_in_y} {z})  ({p3_out_x} {p3_out_y} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({n_leg} {ny} 1) simpleGrading (1 1 1)
            hex (1 8 9 2 5 10 11 6) ({n_arc} {ny} 1) simpleGrading (1 1 1)
            hex (8 12 13 9 10 14 15 11) ({n_leg} {ny} 1) simpleGrading (1 1 1)
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

# ---------------------------------------------------------------------------
# 3. Valve (FIXED & SIMPLIFIED)
# ---------------------------------------------------------------------------
write_file("valve.py", common_header + """
def generate(L, D, cell_size, **kwargs):
    opening = kwargs.get('valve_opening', 0.5) 
    thick = kwargs.get('valve_thickness', 0.2) * D
    r, z = D / 2.0, 0.05
    x_mid = L * 0.5
    x1, x2 = x_mid - thick/2, x_mid + thick/2
    
    # Vertices
    # 0-3: Bot line (-r)
    # 4-7: Mid Bot (-r_open)
    # 8-11: Mid Top (+r_open)
    # 12-15: Top line (+r)
    # +16 for back face
    
    r_open = r * opening
    nx1 = get_cells(x1, cell_size)
    nx_v = get_cells(thick, cell_size, min_cells=3)
    nx3 = get_cells(L-x2, cell_size)
    
    ny = get_cells(D, cell_size, min_cells=12)
    ny_outer = max(1, int(ny * (1-opening)/2))
    ny_inner = max(2, ny - 2*ny_outer)

    return f'''
        vertices
        (
            (0 {-r} {-z})      ({x1} {-r} {-z})      ({x2} {-r} {-z})      ({L} {-r} {-z})
            (0 {-r_open} {-z}) ({x1} {-r_open} {-z}) ({x2} {-r_open} {-z}) ({L} {-r_open} {-z})
            (0 {r_open} {-z})  ({x1} {r_open} {-z})  ({x2} {r_open} {-z})  ({L} {r_open} {-z})
            (0 {r} {-z})       ({x1} {r} {-z})       ({x2} {r} {-z})       ({L} {r} {-z})

            (0 {-r} {z})      ({x1} {-r} {z})      ({x2} {-r} {z})      ({L} {-r} {z})
            (0 {-r_open} {z}) ({x1} {-r_open} {z}) ({x2} {-r_open} {z}) ({L} {-r_open} {z})
            (0 {r_open} {z})  ({x1} {r_open} {z})  ({x2} {r_open} {z})  ({L} {r_open} {z})
            (0 {r} {z})       ({x1} {r} {z})       ({x2} {r} {z})       ({L} {r} {z})
        );
        blocks
        (
            hex (0 1 5 4 16 17 21 20) ({nx1} {ny_outer} 1) simpleGrading (1 1 1)   // Upstream Bot
            hex (4 5 9 8 20 21 25 24) ({nx1} {ny_inner} 1) simpleGrading (1 1 1)   // Upstream Mid
            hex (8 9 13 12 24 25 29 28) ({nx1} {ny_outer} 1) simpleGrading (1 1 1) // Upstream Top
            
            hex (5 6 10 9 21 22 26 25) ({nx_v} {ny_inner} 1) simpleGrading (1 1 1) // Valve Throat
            
            hex (2 3 7 6 18 19 23 22) ({nx3} {ny_outer} 1) simpleGrading (1 1 1)   // Downstream Bot
            hex (6 7 11 10 22 23 27 26) ({nx3} {ny_inner} 1) simpleGrading (1 1 1) // Downstream Mid
            hex (10 11 15 14 26 27 31 30) ({nx3} {ny_outer} 1) simpleGrading (1 1 1) // Downstream Top
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 20 16) (4 8 24 20) (8 12 28 24)); }}
            outlet {{ type patch; faces ((3 7 23 19) (7 11 27 23) (11 15 31 27)); }} 
            walls  {{ type wall;  faces (
                (0 1 17 16)   // Upstream Floor
                (2 3 19 18)   // Downstream Floor
                (12 13 29 28) // Upstream Ceiling
                (14 15 31 30) // Downstream Ceiling
                
                (1 5 21 17)   // Bottom Step Front
                (2 6 22 18)   // Bottom Step Back
                (9 13 29 25)  // Top Step Front
                (10 14 30 26) // Top Step Back
                
                (5 6 22 21)   // Throat Floor
                (9 10 26 25)  // Throat Ceiling
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (8 12 13 9) 
                (16 17 21 20) (20 21 25 24) (24 25 29 28) 
                (5 9 10 6) (21 22 26 25) 
                (2 6 7 3) (6 10 11 7) (10 14 15 11) 
                (18 19 23 22) (22 23 27 26) (26 27 31 30) 
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# ---------------------------------------------------------------------------
# 4. Obstacle
# ---------------------------------------------------------------------------
write_file("obstacle.py", common_header + """
def generate(L, D, cell_size, **kwargs):
    size_ratio = kwargs.get('obs_size', 0.3)
    offset_ratio = kwargs.get('obs_offset', 0.0)
    r, z = D / 2.0, 0.05
    obs_h = size_ratio * D
    obs_y = offset_ratio * D
    
    max_y = r - 0.05*D - obs_h/2
    min_y = -r + 0.05*D + obs_h/2
    if obs_y > max_y: obs_y = max_y
    if obs_y < min_y: obs_y = min_y
    y1, y2 = obs_y - obs_h/2, obs_y + obs_h/2
    x1, x2 = L/2 - obs_h/2, L/2 + obs_h/2
    
    ny = get_cells(D, cell_size, min_cells=12)
    nx1 = get_cells(x1, cell_size)
    nx_obs = get_cells(obs_h, cell_size)
    nx3 = get_cells(L-x2, cell_size)
    
    h_bot = y1 - (-r)
    h_top = r - y2
    ny_bot = get_cells(h_bot, cell_size)
    ny_top = get_cells(h_top, cell_size)
    ny_mid = get_cells(obs_h, cell_size, min_cells=2)
    
    return f'''
        vertices
        (
            (0 {-r} {-z}) ({x1} {-r} {-z}) ({x2} {-r} {-z}) ({L} {-r} {-z})
            (0 {y1} {-z}) ({x1} {y1} {-z}) ({x2} {y1} {-z}) ({L} {y1} {-z})
            (0 {y2} {-z}) ({x1} {y2} {-z}) ({x2} {y2} {-z}) ({L} {y2} {-z})
            (0 {r} {-z})  ({x1} {r} {-z})  ({x2} {r} {-z})  ({L} {r} {-z})

            (0 {-r} {z}) ({x1} {-r} {z}) ({x2} {-r} {z}) ({L} {-r} {z})
            (0 {y1} {z}) ({x1} {y1} {z}) ({x2} {y1} {z}) ({L} {y1} {z})
            (0 {y2} {z}) ({x1} {y2} {z}) ({x2} {y2} {z}) ({L} {y2} {z})
            (0 {r} {z})  ({x1} {r} {z})  ({x2} {r} {z})  ({L} {r} {z})
        );
        blocks
        (
            hex (0 1 5 4 16 17 21 20) ({nx1} {ny_bot} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 20 21 25 24) ({nx1} {ny_mid} 1) simpleGrading (1 1 1)
            hex (8 9 13 12 24 25 29 28) ({nx1} {ny_top} 1) simpleGrading (1 1 1)
            hex (1 2 6 5 17 18 22 21) ({nx_obs} {ny_bot} 1) simpleGrading (1 1 1)
            hex (9 10 14 13 25 26 30 29) ({nx_obs} {ny_top} 1) simpleGrading (1 1 1)
            hex (2 3 7 6 18 19 23 22) ({nx3} {ny_bot} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 22 23 27 26) ({nx3} {ny_mid} 1) simpleGrading (1 1 1)
            hex (10 11 15 14 26 27 31 30) ({nx3} {ny_top} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 20 16) (4 8 24 20) (8 12 28 24)); }}
            outlet {{ type patch; faces ((3 7 23 19) (7 11 27 23) (11 15 31 27)); }}
            walls  {{ type wall;  faces (
                (0 1 17 16) (1 2 18 17) (2 3 19 18) 
                (12 13 29 28) (13 14 30 29) (14 15 31 30) 
                (5 9 25 21) (6 10 26 22) (5 6 22 21) (9 10 26 25)
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

# ---------------------------------------------------------------------------
# 5. Venturi
# ---------------------------------------------------------------------------
write_file("venturi.py", common_header + """
def generate(L, D, cell_size, **kwargs):
    beta = kwargs.get('throat_ratio', 0.5)
    lc_r = kwargs.get('conv_len_ratio', 0.25)
    ld_r = kwargs.get('div_len_ratio', 0.5)
    r_in = D / 2.0
    r_throat = (D * beta) / 2.0
    z = 0.05
    
    l_conv = lc_r * L
    l_div = ld_r * L
    l_throat = L - l_conv - l_div
    if l_throat < 0.05 * L:
        l_throat = 0.05 * L
        scale = (L - l_throat) / (l_conv + l_div)
        l_conv *= scale
        l_div *= scale
    
    x0, x1 = 0, l_conv
    x2 = l_conv + l_throat
    x3 = L
    
    nx1 = get_cells(l_conv, cell_size)
    nx2 = get_cells(l_throat, cell_size)
    nx3 = get_cells(l_div, cell_size)
    ny = get_cells(D, cell_size, min_cells=10)

    return f'''
        vertices
        (
            ({x0} {-r_in} {-z}) ({x1} {-r_throat} {-z}) ({x2} {-r_throat} {-z}) ({x3} {-r_in} {-z})
            ({x0} {r_in} {-z})  ({x1} {r_throat} {-z})  ({x2} {r_throat} {-z})  ({x3} {r_in} {-z})
            
            ({x0} {-r_in} {z}) ({x1} {-r_throat} {z}) ({x2} {-r_throat} {z}) ({x3} {-r_in} {z})
            ({x0} {r_in} {z})  ({x1} {r_throat} {z})  ({x2} {r_throat} {z})  ({x3} {r_in} {z})
        );
        blocks
        (
            hex (0 1 5 4 8 9 13 12) ({nx1} {ny} 1) simpleGrading (1 1 1)
            hex (1 2 6 5 9 10 14 13) ({nx2} {ny} 1) simpleGrading (1 1 1)
            hex (2 3 7 6 10 11 15 14) ({nx3} {ny} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 8 12 4)); }}
            outlet {{ type patch; faces ((3 7 15 11)); }}
            walls  {{ type wall;  faces (
                (0 1 9 8) (1 2 10 9) (2 3 11 10)
                (4 5 13 12) (5 6 14 13) (6 7 15 14)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (1 5 6 2) (2 6 7 3)
                (8 9 13 12) (9 10 14 13) (10 11 15 14)
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# ---------------------------------------------------------------------------
# 6. Manifold
# ---------------------------------------------------------------------------
write_file("manifold.py", common_header + """
def generate(L, D, cell_size, **kwargs):
    bw = D * kwargs.get('branch_width_ratio', 0.8)
    bh = D * kwargs.get('branch_height_ratio', 2.0)
    r = D / 2.0
    z = 0.05
    gap = D * 1.0
    
    x = [0.0]
    curr = 0.0
    for i in range(3):
        curr += gap
        x.append(curr) 
        curr += bw
        x.append(curr) 
    curr += gap
    x.append(curr) 
    
    nx_gap = get_cells(gap, cell_size)
    nx_br = get_cells(bw, cell_size)
    ny = get_cells(D, cell_size, min_cells=10)
    ny_br = get_cells(bh, cell_size, min_cells=10)

    return f'''
        vertices
        (
            ({x[0]} {-r} {-z}) ({x[1]} {-r} {-z}) ({x[2]} {-r} {-z}) ({x[3]} {-r} {-z}) 
            ({x[4]} {-r} {-z}) ({x[5]} {-r} {-z}) ({x[6]} {-r} {-z}) ({x[7]} {-r} {-z})
            
            ({x[0]} {r} {-z}) ({x[1]} {r} {-z}) ({x[2]} {r} {-z}) ({x[3]} {r} {-z}) 
            ({x[4]} {r} {-z}) ({x[5]} {r} {-z}) ({x[6]} {r} {-z}) ({x[7]} {r} {-z})
            
            ({x[1]} {r+bh} {-z}) ({x[2]} {r+bh} {-z})
            ({x[3]} {r+bh} {-z}) ({x[4]} {r+bh} {-z})
            ({x[5]} {r+bh} {-z}) ({x[6]} {r+bh} {-z})

            ({x[0]} {-r} {z}) ({x[1]} {-r} {z}) ({x[2]} {-r} {z}) ({x[3]} {-r} {z}) 
            ({x[4]} {-r} {z}) ({x[5]} {-r} {z}) ({x[6]} {-r} {z}) ({x[7]} {-r} {z})
            
            ({x[0]} {r} {z}) ({x[1]} {r} {z}) ({x[2]} {r} {z}) ({x[3]} {r} {z}) 
            ({x[4]} {r} {z}) ({x[5]} {r} {z}) ({x[6]} {r} {z}) ({x[7]} {r} {z})
            
            ({x[1]} {r+bh} {z}) ({x[2]} {r+bh} {z})
            ({x[3]} {r+bh} {z}) ({x[4]} {r+bh} {z})
            ({x[5]} {r+bh} {z}) ({x[6]} {r+bh} {z})
        );
        blocks
        (
            hex (0 1 9 8 22 23 31 30) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (1 2 10 9 23 24 32 31) ({nx_br} {ny} 1) simpleGrading (1 1 1) 
            hex (2 3 11 10 24 25 33 32) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (3 4 12 11 25 26 34 33) ({nx_br} {ny} 1) simpleGrading (1 1 1) 
            hex (4 5 13 12 26 27 35 34) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (5 6 14 13 27 28 36 35) ({nx_br} {ny} 1) simpleGrading (1 1 1) 
            hex (6 7 15 14 28 29 37 36) ({nx_gap} {ny} 1) simpleGrading (1 1 1)

            hex (9 10 17 16 31 32 39 38) ({nx_br} {ny_br} 1) simpleGrading (1 1 1)
            hex (11 12 19 18 33 34 41 40) ({nx_br} {ny_br} 1) simpleGrading (1 1 1)
            hex (13 14 21 20 35 36 43 42) ({nx_br} {ny_br} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 8 30 22)); }}
            outlet {{ type patch; faces (
                (16 17 39 38) (18 19 41 40) (20 21 43 42)
            ); }}
            walls  {{ type wall;  faces (
                (0 1 23 22) (1 2 24 23) (2 3 25 24) (3 4 26 25) (4 5 27 26) (5 6 28 27) (6 7 29 28)
                (7 15 37 29)
                (8 9 31 30) (10 11 33 32) (12 13 35 34) (14 15 37 36)
                (9 16 38 31) (10 32 39 17) 
                (11 18 40 33) (12 34 41 19)
                (13 20 42 35) (14 36 43 21)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 8 9 1) (1 9 10 2) (2 10 11 3) (3 11 12 4) (4 12 13 5) (5 13 14 6) (6 14 15 7)
                (9 16 17 10) (11 18 19 12) (13 20 21 14)
                (22 23 31 30) (23 24 32 31) (24 25 33 32) (25 26 34 33) (26 27 35 34) (27 28 36 35) (28 29 37 36)
                (31 32 39 38) (33 34 41 40) (35 36 43 42)
            ); }}
        );
        mergePatchPairs ();
    '''
""")

print("All shapes generated successfully.")