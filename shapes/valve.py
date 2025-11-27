
def generate(L, D, dens_mult):
    # Represents a partially closed gate valve or orifice plate
    # Split into 3 x-sections: Upstream, Valve, Downstream
    # Valve section has fluid in middle, walls on top/bottom
    
    r = D / 2.0
    z = 0.05
    
    valve_len = 0.2 * D
    opening_ratio = 0.4 # 40% open in the center
    
    r_open = r * opening_ratio
    
    x1 = (L - valve_len) / 2.0
    x2 = x1 + valve_len
    x3 = L
    
    ny = int(20 * dens_mult)
    if ny % 2 != 0: ny += 1
    
    nx_main = int((x1 / D) * ny)
    nx_valve = int((valve_len / D) * ny)
    if nx_valve < 2: nx_valve = 2
    
    # We need graded vertices in Y to match the opening
    # We will define 3 blocks in Y for the WHOLE domain to keep mesh consistent
    # Y-zones: [-r, -r_open], [-r_open, r_open], [r_open, r]
    
    ny_outer = int(ny * (1-opening_ratio)/2)
    ny_inner = ny - 2*ny_outer
    
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
            // Inlet Section (3 vertical blocks)
            hex (0 1 5 4 16 17 21 20) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 20 21 25 24) ({nx_main} {ny_inner} 1) simpleGrading (1 1 1)
            hex (8 9 13 12 24 25 29 28) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)

            // Valve Section (Only Middle Block exists, Top/Bottom are voids/walls)
            hex (5 6 10 9 21 22 26 25) ({nx_valve} {ny_inner} 1) simpleGrading (1 1 1)

            // Outlet Section (3 vertical blocks)
            hex (2 3 7 6 18 19 23 22) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 22 23 27 26) ({nx_main} {ny_inner} 1) simpleGrading (1 1 1)
            hex (10 11 15 14 26 27 31 30) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 16 20 4) (4 20 24 8) (8 24 28 12)); }}
            outlet {{ type patch; faces ((2 3 19 18) (6 7 23 22) (10 11 27 30)); }}
            walls  {{ type wall;  faces (
                // Main pipe walls
                (0 1 17 16) (1 2 18 17) (2 3 19 18)
                (12 13 29 28) (13 14 30 29) (14 15 31 30)
                // Valve Faces (The "Steps")
                (1 5 21 17) (5 6 22 21) (6 2 18 22) 
                (13 9 25 29) (9 10 26 25) (10 14 30 26) 
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (8 12 13 9) // Inlet Front
                (16 17 21 20) (20 21 25 24) (24 25 29 28) // Inlet Back
                (5 9 10 6) // Valve Front
                (21 22 26 25) // Valve Back
                (2 6 7 3) (6 10 11 7) (10 14 15 11) // Outlet Front
                (18 19 23 22) (22 23 27 26) (26 27 31 30) // Outlet Back
            ); }}
        );
        mergePatchPairs ();
    '''
