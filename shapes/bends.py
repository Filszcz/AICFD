
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
