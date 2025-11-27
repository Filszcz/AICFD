
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
