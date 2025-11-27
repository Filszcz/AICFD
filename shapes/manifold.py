write_file("manifold.py", """
def generate(L, D, dens_mult):
    # 1 Inlet (Left), 3 Outlets (Top)
    r = D / 2.0
    z = 0.05
    
    # Calculate spacing
    leg_width = D
    gap = D
    # Total Length L is overridden to ensure geometry fits, 
    # but we scale based on D
    
    x_leg1 = D
    x_leg2 = x_leg1 + leg_width + gap
    x_leg3 = x_leg2 + leg_width + gap
    total_L = x_leg3 + leg_width + D
    
    leg_height = 2.0 * D
    
    ny = int(15 * dens_mult)
    nx_gap = int(15 * dens_mult)
    ny_leg = int(25 * dens_mult)

    return f'''
        vertices
        (
            // Bottom Baseline
            (0 {-r} {-z}) ({x_leg1} {-r} {-z}) ({x_leg1+leg_width} {-r} {-z}) 
            ({x_leg2} {-r} {-z}) ({x_leg2+leg_width} {-r} {-z}) 
            ({x_leg3} {-r} {-z}) ({x_leg3+leg_width} {-r} {-z}) ({total_L} {-r} {-z})

            // Top of Main Pipe
            (0 {r} {-z}) ({x_leg1} {r} {-z}) ({x_leg1+leg_width} {r} {-z}) 
            ({x_leg2} {r} {-z}) ({x_leg2+leg_width} {r} {-z}) 
            ({x_leg3} {r} {-z}) ({x_leg3+leg_width} {r} {-z}) ({total_L} {r} {-z})

            // Top of Legs (Outlets)
            ({x_leg1} {r+leg_height} {-z}) ({x_leg1+leg_width} {r+leg_height} {-z})
            ({x_leg2} {r+leg_height} {-z}) ({x_leg2+leg_width} {r+leg_height} {-z})
            ({x_leg3} {r+leg_height} {-z}) ({x_leg3+leg_width} {r+leg_height} {-z})

            // Z-Extrusion (Back plane, indices +14)
            (0 {-r} {z}) ({x_leg1} {-r} {z}) ({x_leg1+leg_width} {-r} {z}) 
            ({x_leg2} {-r} {z}) ({x_leg2+leg_width} {-r} {z}) 
            ({x_leg3} {-r} {z}) ({x_leg3+leg_width} {-r} {z}) ({total_L} {-r} {z})

            (0 {r} {z}) ({x_leg1} {r} {z}) ({x_leg1+leg_width} {r} {z}) 
            ({x_leg2} {r} {z}) ({x_leg2+leg_width} {r} {z}) 
            ({x_leg3} {r} {z}) ({x_leg3+leg_width} {r} {z}) ({total_L} {r} {z})

            ({x_leg1} {r+leg_height} {z}) ({x_leg1+leg_width} {r+leg_height} {z})
            ({x_leg2} {r+leg_height} {z}) ({x_leg2+leg_width} {r+leg_height} {z})
            ({x_leg3} {r+leg_height} {z}) ({x_leg3+leg_width} {r+leg_height} {z})
        );
        blocks
        (
            // Main Trunk (7 blocks horizontally)
            hex (0 1 9 8 14 15 23 22) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (1 2 10 9 15 16 24 23) ({ny} {ny} 1) simpleGrading (1 1 1)      // Under Leg 1
            hex (2 3 11 10 16 17 25 24) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (3 4 12 11 17 18 26 25) ({ny} {ny} 1) simpleGrading (1 1 1)      // Under Leg 2
            hex (4 5 13 12 18 19 27 26) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (5 6 14 13 19 20 28 27) ({ny} {ny} 1) simpleGrading (1 1 1)      // Under Leg 3
            hex (6 7 15 14 20 21 29 28) ({nx_gap} {ny} 1) simpleGrading (1 1 1)  // End cap

            // Vertical Legs
            hex (9 10 17 16 23 24 31 30) ({ny} {ny_leg} 1) simpleGrading (1 1 1)
            hex (11 12 19 18 25 26 33 32) ({ny} {ny_leg} 1) simpleGrading (1 1 1)
            hex (13 14 21 20 27 28 35 34) ({ny} {ny_leg} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 8 22 14)); }}
            outlet {{ type patch; faces (
                (16 17 31 30) (18 19 33 32) (20 21 35 34) 
            ); }}
            walls  {{ type wall;  faces (
                // Bottom
                (0 1 15 14) (1 2 16 15) (2 3 17 16) (3 4 18 17) (4 5 19 18) (5 6 20 19) (6 7 21 20)
                // End Cap
                (7 15 29 21)
                // Top segments between legs
                (8 9 23 22) (10 11 25 24) (12 13 27 26) (14 15 29 28)
                // Leg Vertical Walls
                (9 16 30 23) (10 24 31 17) 
                (11 18 32 25) (12 26 33 19)
                (13 20 34 27) (14 28 35 21)
            ); }}
            frontAndBack {{ type empty; faces (
                // Front and Back faces of all 10 blocks...
                // (Omitted for brevity, OpenFOAM allows 'wildcards' if you just group remaining faces, 
                // but explicit is better. For this code snippet, I rely on the fact that any face not in 
                // inlet/outlet/walls is empty by default in many parsers, but here we explicitly list main ones)
                (0 8 9 1) (1 9 10 2) (2 10 11 3) (3 11 12 4) (4 12 13 5) (5 13 14 6) (6 14 15 7)
                (9 16 17 10) (11 18 19 12) (13 20 21 14)
                (14 22 23 15) (15 23 24 16) (16 24 25 17) (17 25 26 18) (18 26 27 19) (19 27 28 20) (20 28 29 21)
                (23 30 31 24) (25 32 33 26) (27 34 35 28)
            ); }}
        );
        mergePatchPairs ();
    '''
""")