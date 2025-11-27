
def generate(L, D, dens_mult):
    # A generic baffle extending from the bottom wall
    r = D / 2.0
    z = 0.05
    baffle_h = 0.5 * D
    baffle_t = 0.1 * D # Thickness
    
    x1 = (L - baffle_t) / 2.0
    x2 = x1 + baffle_t
    x3 = L
    
    ny = int(20 * dens_mult)
    nx_main = int((x1 / D) * ny)
    nx_baffle = int((baffle_t / D) * ny)
    if nx_baffle < 2: nx_baffle = 2
    
    # Y-split: [-r, -r + h] (Baffle zone), [-r+h, r] (Flow zone)
    y_split = -r + baffle_h
    ny_baffle = int(ny * 0.5)
    ny_flow = ny - ny_baffle
    
    return f'''
        vertices
        (
            (0 {-r} {-z})      ({x1} {-r} {-z})      ({x2} {-r} {-z})      ({x3} {-r} {-z})
            (0 {y_split} {-z}) ({x1} {y_split} {-z}) ({x2} {y_split} {-z}) ({x3} {y_split} {-z})
            (0 {r} {-z})       ({x1} {r} {-z})       ({x2} {r} {-z})       ({x3} {r} {-z})

            (0 {-r} {z})      ({x1} {-r} {z})      ({x2} {-r} {z})      ({x3} {-r} {z})
            (0 {y_split} {z}) ({x1} {y_split} {z}) ({x2} {y_split} {z}) ({x3} {y_split} {z})
            (0 {r} {z})       ({x1} {r} {z})       ({x2} {r} {z})       ({x3} {r} {z})
        );
        blocks
        (
            // Left (Bottom and Top)
            hex (0 1 5 4 12 13 17 16) ({nx_main} {ny_baffle} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 16 17 21 20) ({nx_main} {ny_flow} 1) simpleGrading (1 1 1)
            
            // Middle (Only Top is fluid)
            hex (5 6 10 9 17 18 22 21) ({nx_baffle} {ny_flow} 1) simpleGrading (1 1 1)
            
            // Right (Bottom and Top)
            hex (2 3 7 6 14 15 19 18) ({nx_main} {ny_baffle} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 18 19 23 22) ({nx_main} {ny_flow} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 12 16 4) (4 16 20 8)); }}
            outlet {{ type patch; faces ((2 3 15 14) (6 7 19 18) (10 11 23 22) (3 15 19 7)); }} 
            walls  {{ type wall;  faces (
                (0 1 13 12) (1 5 17 13) (5 6 18 17) (6 2 14 18) (2 3 15 14)
                (8 9 21 20) (9 10 22 21) (10 11 23 22)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (12 13 17 16) (16 17 21 20) // Left
                (5 9 10 6) (17 18 22 21) // Middle
                (2 6 7 3) (6 10 11 7) (14 15 19 18) (18 19 23 22) // Right
            ); }}
        );
        mergePatchPairs ();
    '''
