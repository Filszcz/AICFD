
import math

def get_cells(length, cell_size, min_cells=2):
    if length <= 1e-6: return 1
    val = int(length / cell_size)
    return max(min_cells, val)

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
