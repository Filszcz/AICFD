
def generate(L, D, dens_mult):
    # Square obstacle in the middle of flow
    r = D / 2.0
    z = 0.05
    obs_size = 0.3 * D
    
    x1 = (L - obs_size) / 2.0
    x2 = x1 + obs_size
    x3 = L
    
    y1 = -obs_size / 2.0
    y2 = obs_size / 2.0
    
    ny = int(20 * dens_mult)
    nx_main = int((x1 / D) * ny)
    nx_obs = int((obs_size / D) * ny)
    if nx_obs < 2: nx_obs = 2
    
    ny_mid = nx_obs
    ny_outer = int((ny - ny_mid) / 2)
    
    return f'''
        vertices
        (
            (0 {-r} {-z}) ({x1} {-r} {-z}) ({x2} {-r} {-z}) ({x3} {-r} {-z})
            (0 {y1} {-z}) ({x1} {y1} {-z}) ({x2} {y1} {-z}) ({x3} {y1} {-z})
            (0 {y2} {-z}) ({x1} {y2} {-z}) ({x2} {y2} {-z}) ({x3} {y2} {-z})
            (0 {r} {-z})  ({x1} {r} {-z})  ({x2} {r} {-z})  ({x3} {r} {-z})

            (0 {-r} {z}) ({x1} {-r} {z}) ({x2} {-r} {z}) ({x3} {-r} {z})
            (0 {y1} {z}) ({x1} {y1} {z}) ({x2} {y1} {z}) ({x3} {y1} {z})
            (0 {y2} {z}) ({x1} {y2} {z}) ({x2} {y2} {z}) ({x3} {y2} {z})
            (0 {r} {z})  ({x1} {r} {z})  ({x2} {r} {z})  ({x3} {r} {z})
        );
        blocks
        (
            // Inlet 3 blocks
            hex (0 1 5 4 16 17 21 20) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (4 5 9 8 20 21 25 24) ({nx_main} {ny_mid} 1) simpleGrading (1 1 1)
            hex (8 9 13 12 24 25 29 28) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            
            // Middle (Bottom and Top only)
            hex (1 2 6 5 17 18 22 21) ({nx_obs} {ny_outer} 1) simpleGrading (1 1 1)
            hex (9 10 14 13 25 26 30 29) ({nx_obs} {ny_outer} 1) simpleGrading (1 1 1)
            
            // Outlet 3 blocks
            hex (2 3 7 6 18 19 23 22) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
            hex (6 7 11 10 22 23 27 26) ({nx_main} {ny_mid} 1) simpleGrading (1 1 1)
            hex (10 11 15 14 26 27 31 30) ({nx_main} {ny_outer} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 16 20 4) (4 20 24 8) (8 24 28 12)); }}
            outlet {{ type patch; faces ((2 3 19 18) (6 7 23 22) (10 11 27 30)); }}
            walls  {{ type wall;  faces (
                (0 1 17 16) (1 2 18 17) (2 3 19 18) // Bottom
                (12 13 29 28) (13 14 30 29) (14 15 31 30) // Top
                // Obstacle
                (5 6 22 21) (6 10 26 22) (10 9 25 26) (9 5 21 25)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (8 12 13 9) (16 17 21 20) (20 21 25 24) (24 25 29 28)
                (1 5 6 2) (9 13 14 10) (17 18 22 21) (25 26 30 29)
                (2 6 7 3) (6 10 11 7) (10 14 15 11) (18 19 23 22) (22 23 27 26) (26 27 31 30)
            ); }}
        );
        mergePatchPairs ();
    '''
