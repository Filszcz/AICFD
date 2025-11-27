
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
