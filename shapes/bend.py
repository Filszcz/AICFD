
import math

def get_cells(length, cell_size, min_cells=2):
    if length <= 1e-6: return 1
    val = int(length / cell_size)
    return max(min_cells, val)

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
