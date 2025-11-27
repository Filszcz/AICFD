
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
