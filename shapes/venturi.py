
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
