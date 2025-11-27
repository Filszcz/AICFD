
import math

def get_cells(length, cell_size, min_cells=2):
    if length <= 1e-6: return 1
    val = int(length / cell_size)
    return max(min_cells, val)

def generate(L, D, cell_size, **kwargs):
    opening = kwargs.get('valve_opening', 0.5) 
    thick = kwargs.get('valve_thickness', 0.2) * D
    r, z = D / 2.0, 0.05
    x_mid = L * 0.5
    x1, x2 = x_mid - thick/2, x_mid + thick/2
    
    # Vertices
    # 0-3: Bot line (-r)
    # 4-7: Mid Bot (-r_open)
    # 8-11: Mid Top (+r_open)
    # 12-15: Top line (+r)
    # +16 for back face
    
    r_open = r * opening
    nx1 = get_cells(x1, cell_size)
    nx_v = get_cells(thick, cell_size, min_cells=3)
    nx3 = get_cells(L-x2, cell_size)
    
    ny = get_cells(D, cell_size, min_cells=12)
    ny_outer = max(1, int(ny * (1-opening)/2))
    ny_inner = max(2, ny - 2*ny_outer)

    return f'''
        vertices
        (
            (0 {-r} {-z})      ({x1} {-r} {-z})      ({x2} {-r} {-z})      ({L} {-r} {-z})
            (0 {-r_open} {-z}) ({x1} {-r_open} {-z}) ({x2} {-r_open} {-z}) ({L} {-r_open} {-z})
            (0 {r_open} {-z})  ({x1} {r_open} {-z})  ({x2} {r_open} {-z})  ({L} {r_open} {-z})
            (0 {r} {-z})       ({x1} {r} {-z})       ({x2} {r} {-z})       ({L} {r} {-z})

            (0 {-r} {z})      ({x1} {-r} {z})      ({x2} {-r} {z})      ({L} {-r} {z})
            (0 {-r_open} {z}) ({x1} {-r_open} {z}) ({x2} {-r_open} {z}) ({L} {-r_open} {z})
            (0 {r_open} {z})  ({x1} {r_open} {z})  ({x2} {r_open} {z})  ({L} {r_open} {z})
            (0 {r} {z})       ({x1} {r} {z})       ({x2} {r} {z})       ({L} {r} {z})
        );
        blocks
        (
            hex (0 1 5 4 16 17 21 20) ({nx1} {ny_outer} 1) simpleGrading (1 1 1)   // Upstream Bot
            hex (4 5 9 8 20 21 25 24) ({nx1} {ny_inner} 1) simpleGrading (1 1 1)   // Upstream Mid
            hex (8 9 13 12 24 25 29 28) ({nx1} {ny_outer} 1) simpleGrading (1 1 1) // Upstream Top
            
            hex (5 6 10 9 21 22 26 25) ({nx_v} {ny_inner} 1) simpleGrading (1 1 1) // Valve Throat
            
            hex (2 3 7 6 18 19 23 22) ({nx3} {ny_outer} 1) simpleGrading (1 1 1)   // Downstream Bot
            hex (6 7 11 10 22 23 27 26) ({nx3} {ny_inner} 1) simpleGrading (1 1 1) // Downstream Mid
            hex (10 11 15 14 26 27 31 30) ({nx3} {ny_outer} 1) simpleGrading (1 1 1) // Downstream Top
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 4 20 16) (4 8 24 20) (8 12 28 24)); }}
            outlet {{ type patch; faces ((3 7 23 19) (7 11 27 23) (11 15 31 27)); }} 
            walls  {{ type wall;  faces (
                (0 1 17 16)   // Upstream Floor
                (2 3 19 18)   // Downstream Floor
                (12 13 29 28) // Upstream Ceiling
                (14 15 31 30) // Downstream Ceiling
                
                (1 5 21 17)   // Bottom Step Front
                (2 6 22 18)   // Bottom Step Back
                (9 13 29 25)  // Top Step Front
                (10 14 30 26) // Top Step Back
                
                (5 6 22 21)   // Throat Floor
                (9 10 26 25)  // Throat Ceiling
            ); }}
            frontAndBack {{ type empty; faces (
                (0 4 5 1) (4 8 9 5) (8 12 13 9) 
                (16 17 21 20) (20 21 25 24) (24 25 29 28) 
                (5 9 10 6) (21 22 26 25) 
                (2 6 7 3) (6 10 11 7) (10 14 15 11) 
                (18 19 23 22) (22 23 27 26) (26 27 31 30) 
            ); }}
        );
        mergePatchPairs ();
    '''
