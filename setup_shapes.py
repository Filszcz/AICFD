import os

SHAPE_DIR = "shapes"
os.makedirs(SHAPE_DIR, exist_ok=True)

def write_file(filename, content):
    filepath = os.path.join(SHAPE_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Updated {filepath}")

write_file("__init__.py", "")

# 1. Straight Pipe
write_file("straight.py", """
def generate(L, D, dens_mult, **kwargs):
    # kwargs: None used, but kept for compatibility
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

# 2. Bends (Variable Radius)
write_file("bends.py", """
import math

def generate_90(L, D, dens_mult, **kwargs):
    # kwargs: 'curve_radius_ratio' (default 1.5) -> R_mid = ratio * D
    ratio = kwargs.get('curve_radius_ratio', 1.5)
    
    r, z = D / 2.0, 0.05
    R_mid = ratio * D
    R_inner = R_mid - r
    R_outer = R_mid + r
    
    base_cells = int(20 * dens_mult)
    if base_cells % 2 != 0: base_cells += 1
    
    # Calculate leg length based on total L and arc radius
    # To keep total path length approx L, we split remainder into straight legs
    arc_len = (math.pi * R_mid) / 2.0
    straight_len = max(0, (L - arc_len) / 2.0)
    
    l_cells = int((straight_len / D) * base_cells)
    if l_cells < 2: l_cells = 2
    arc_cells = int((arc_len / D) * base_cells)
    
    cx, cy = straight_len, -r - R_inner
    
    # Points
    p2_in_x, p2_in_y = cx + R_inner, cy
    p2_out_x, p2_out_y = cx + R_outer, cy
    
    p3_in_x, p3_in_y = p2_in_x, p2_in_y - straight_len
    p3_out_x, p3_out_y = p2_out_x, p2_out_y - straight_len
    
    theta = math.radians(45)
    m_in_x = cx + R_inner * math.sin(theta)
    m_in_y = cy + R_inner * math.cos(theta)
    m_out_x = cx + R_outer * math.sin(theta)
    m_out_y = cy + R_outer * math.cos(theta)

    return f'''
        vertices
        (
            (0 {-r} {-z}) ({straight_len} {-r} {-z}) ({straight_len} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z})  ({straight_len} {-r} {z})  ({straight_len} {r} {z})  (0 {r} {z})
            
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

# 3. Valve (Variable Opening)
write_file("valve.py", """
def generate(L, D, dens_mult, **kwargs):
    # kwargs: 'valve_opening' (0.1 to 0.9)
    # kwargs: 'valve_pos' (0.2 to 0.8) - position along L
    
    opening_ratio = kwargs.get('valve_opening', 0.5) 
    pos_ratio = kwargs.get('valve_pos', 0.5)
    
    r = D / 2.0
    z = 0.05
    valve_len = 0.2 * D
    
    # Calculate X positions
    x_center = L * pos_ratio
    x1 = x_center - (valve_len / 2.0)
    x2 = x_center + (valve_len / 2.0)
    x3 = L
    
    r_open = r * opening_ratio
    
    ny = int(20 * dens_mult)
    if ny % 2 != 0: ny += 1
    
    nx1 = int((x1 / D) * ny)
    nx_valve = int((valve_len / D) * ny)
    nx3 = int(((x3-x2) / D) * ny)
    if nx1 < 2: nx1 = 2
    if nx_valve < 2: nx_valve = 2
    if nx3 < 2: nx3 = 2
    
    ny_outer = int(ny * (1-opening_ratio)/2)
    ny_inner = ny - 2*ny_outer
    if ny_inner < 1: ny_inner = 1
    
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
            hex (0 1 5 4 16 17 21 20) ({nx1} {ny_outer} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 20 21 25 24) ({nx1} {ny_inner} 1) simpleGrading (1 1 1)
            hex (8 9 13 12 24 25 29 28) ({nx1} {ny_outer} 1) simpleGrading (1 1 1)

            hex (5 6 10 9 21 22 26 25) ({nx_valve} {ny_inner} 1) simpleGrading (1 1 1)

            hex (2 3 7 6 18 19 23 22) ({nx3} {ny_outer} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 22 23 27 26) ({nx3} {ny_inner} 1) simpleGrading (1 1 1)
            hex (10 11 15 14 26 27 31 30) ({nx3} {ny_outer} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 16 20 4) (4 20 24 8) (8 24 28 12)); }}
            outlet {{ type patch; faces ((2 3 19 18) (6 7 23 22) (10 11 27 30)); }}
            walls  {{ type wall;  faces (
                (0 1 17 16) (1 2 18 17) (2 3 19 18)
                (12 13 29 28) (13 14 30 29) (14 15 31 30)
                (1 5 21 17) (5 6 22 21) (6 2 18 22) 
                (13 9 25 29) (9 10 26 25) (10 14 30 26) 
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (8 12 13 9) 
                (16 17 21 20) (20 21 25 24) (24 25 29 28) 
                (5 9 10 6) 
                (21 22 26 25) 
                (2 6 7 3) (6 10 11 7) (10 14 15 11) 
                (18 19 23 22) (22 23 27 26) (26 27 31 30) 
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# 4. Obstacle (Variable Size/Pos)
write_file("obstacle.py", """
def generate(L, D, dens_mult, **kwargs):
    # kwargs: 'obs_size_ratio' (0.1 to 0.5)
    # kwargs: 'obs_pos' (0.2 to 0.8)
    
    size_ratio = kwargs.get('obs_size_ratio', 0.3)
    pos_ratio = kwargs.get('obs_pos', 0.5)
    
    r = D / 2.0
    z = 0.05
    obs_size = size_ratio * D
    
    x_center = L * pos_ratio
    x1 = x_center - (obs_size / 2.0)
    x2 = x_center + (obs_size / 2.0)
    x3 = L
    
    y1 = -obs_size / 2.0
    y2 = obs_size / 2.0
    
    ny = int(20 * dens_mult)
    nx1 = int((x1 / D) * ny)
    nx_obs = int((obs_size / D) * ny)
    nx3 = int(((x3-x2) / D) * ny)
    
    if nx1 < 2: nx1 = 2
    if nx_obs < 2: nx_obs = 2
    if nx3 < 2: nx3 = 2
    
    ny_mid = nx_obs
    ny_outer = int((ny - ny_mid) / 2)
    if ny_outer < 1: ny_outer = 1
    
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
            hex (0 1 5 4 16 17 21 20) ({nx1} {ny_outer} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 20 21 25 24) ({nx1} {ny_mid} 1) simpleGrading (1 1 1)
            hex (8 9 13 12 24 25 29 28) ({nx1} {ny_outer} 1) simpleGrading (1 1 1)
            
            hex (1 2 6 5 17 18 22 21) ({nx_obs} {ny_outer} 1) simpleGrading (1 1 1)
            hex (9 10 14 13 25 26 30 29) ({nx_obs} {ny_outer} 1) simpleGrading (1 1 1)
            
            hex (2 3 7 6 18 19 23 22) ({nx3} {ny_outer} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 22 23 27 26) ({nx3} {ny_mid} 1) simpleGrading (1 1 1)
            hex (10 11 15 14 26 27 31 30) ({nx3} {ny_outer} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 16 20 4) (4 20 24 8) (8 24 28 12)); }}
            outlet {{ type patch; faces ((2 3 19 18) (6 7 23 22) (10 11 27 30)); }}
            walls  {{ type wall;  faces (
                (0 1 17 16) (1 2 18 17) (2 3 19 18) 
                (12 13 29 28) (13 14 30 29) (14 15 31 30) 
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

# 5. Venturi (Variable Throat)
write_file("venturi.py", """
def generate(L, D, dens_mult, **kwargs):
    # kwargs: 'throat_ratio' (0.3 to 0.7)
    
    beta = kwargs.get('throat_ratio', 0.5)
    
    r_in = D / 2.0
    r_throat = (D * beta) / 2.0
    z = 0.05
    
    l_conv = 0.25 * L
    l_throat = 0.15 * L
    l_div = 0.6 * L
    
    x0, x1 = 0, l_conv
    x2 = l_conv + l_throat
    x3 = L
    
    ny = int(20 * dens_mult)
    nx1 = int((l_conv/D) * ny)
    nx2 = int((l_throat/D) * ny)
    nx3 = int((l_div/D) * ny)
    
    if nx1 < 2: nx1 = 2
    if nx2 < 2: nx2 = 2
    if nx3 < 2: nx3 = 2

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

# 6. Step (Variable Expansion)
write_file("step.py", """
def generate(L, D, dens_mult, **kwargs):
    # D is inlet Height (h)
    # kwargs: 'expansion_ratio' (H/h) - (1.5 to 3.0)
    
    ratio = kwargs.get('expansion_ratio', 2.0)
    h = D
    H = ratio * D
    z = 0.05
    
    x_step = L / 3.0
    x_end = L
    
    nx_inlet = int(15 * dens_mult)
    nx_outlet = int(30 * dens_mult)
    ny_h = int(15 * dens_mult)
    ny_top = int(ny_h * (ratio - 1.0))
    if ny_top < 1: ny_top = 1
    
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
            hex (4 5 6 13 11 12 14 13) ({nx_outlet} {ny_top} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 10 11 3)); }}
            outlet {{ type patch; faces ((2 5 12 9) (5 6 14 12)); }}
            walls  {{ type wall;  faces (
                (0 1 8 7) (1 2 9 8) 
                (3 4 11 10) (13 6 14 13) 
                (4 13 13 11) 
            ); }}
            frontAndBack {{ type empty; faces (
                (0 3 4 1) (1 4 5 2) (4 13 6 5)
                (7 8 11 10) (8 9 12 11) (11 12 14 13)
            ); }}
        );
        mergePatchPairs ();
    '''
""")

# 7. Cylinder (Variable Diam)
write_file("cylinder.py", """
import math
def generate(L, D, dens_mult, **kwargs):
    # kwargs: 'cyl_size_ratio' (0.2 to 0.6)
    ratio = kwargs.get('cyl_size_ratio', 0.4)
    
    r_chan = D / 2.0
    r_cyl = (ratio * D) / 2.0
    z = 0.05
    cx, cy = L / 2.0, 0.0
    
    cos45 = math.cos(math.radians(45))
    x_in_r = cx + r_cyl * cos45
    x_in_l = cx - r_cyl * cos45
    y_in_u = cy + r_cyl * cos45
    y_in_d = cy - r_cyl * cos45
    
    nx = int(20 * dens_mult)
    ny = int(10 * dens_mult) 

    return f'''
        vertices
        (
            (0 {-r_chan} {-z}) ({L} {-r_chan} {-z}) ({L} {r_chan} {-z}) (0 {r_chan} {-z})
            (0 {-r_chan} {z}) ({L} {-r_chan} {z}) ({L} {r_chan} {z}) (0 {r_chan} {z})
            
            ({x_in_l} {y_in_d} {-z}) ({x_in_r} {y_in_d} {-z}) 
            ({x_in_r} {y_in_u} {-z}) ({x_in_l} {y_in_u} {-z})
            
            ({x_in_l} {y_in_d} {z}) ({x_in_r} {y_in_d} {z}) 
            ({x_in_r} {y_in_u} {z}) ({x_in_l} {y_in_u} {z})
        );
        blocks
        (
            hex (0 1 9 8 4 5 13 12) ({nx} {ny} 1) simpleGrading (1 1 1)
            hex (9 1 2 10 13 5 6 14) ({ny} {nx} 1) simpleGrading (1 1 1)
            hex (11 10 2 3 15 14 6 7) ({nx} {ny} 1) simpleGrading (1 1 1)
            hex (0 8 11 3 4 12 15 7) ({ny} {nx} 1) simpleGrading (1 1 1)
        );
        edges
        (
            arc 8 9 ({cx} {cy-r_cyl} {-z})
            arc 9 10 ({cx+r_cyl} {cy} {-z})
            arc 10 11 ({cx} {cy+r_cyl} {-z})
            arc 11 8 ({cx-r_cyl} {cy} {-z})
            arc 12 13 ({cx} {cy-r_cyl} {z})
            arc 13 14 ({cx+r_cyl} {cy} {z})
            arc 14 15 ({cx} {cy+r_cyl} {z})
            arc 15 12 ({cx-r_cyl} {cy} {z})
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((1 2 6 5)); }}
            walls  {{ type wall;  faces (
                (0 1 5 4) (3 7 6 2) 
                (8 12 13 9) (9 13 14 10) (10 14 15 11) (11 15 12 8)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 3 11 8) (8 11 10 9) (9 10 2 1)
                (4 12 15 7) (12 13 14 15) (13 5 6 14)
            ); }}
        );
        mergePatchPairs ();
    '''
""")

print("All shapes updated to support variable parameters (kwargs).")