
import math

def get_cells(length, cell_size, min_cells=2):
    if length <= 1e-6: return 1
    val = int(length / cell_size)
    return max(min_cells, val)

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
