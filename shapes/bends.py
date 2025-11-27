
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
