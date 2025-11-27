
import math

def get_cells(length, cell_size, min_cells=2):
    if length <= 1e-6: return 1
    val = int(length / cell_size)
    return max(min_cells, val)

def generate(L, D, cell_size, **kwargs):
    bw = D * kwargs.get('branch_width_ratio', 0.8)
    bh = D * kwargs.get('branch_height_ratio', 2.0)
    r = D / 2.0
    z = 0.05
    gap = D * 1.0
    
    x = [0.0]
    curr = 0.0
    for i in range(3):
        curr += gap
        x.append(curr) 
        curr += bw
        x.append(curr) 
    curr += gap
    x.append(curr) 
    
    nx_gap = get_cells(gap, cell_size)
    nx_br = get_cells(bw, cell_size)
    ny = get_cells(D, cell_size, min_cells=10)
    ny_br = get_cells(bh, cell_size, min_cells=10)

    return f'''
        vertices
        (
            ({x[0]} {-r} {-z}) ({x[1]} {-r} {-z}) ({x[2]} {-r} {-z}) ({x[3]} {-r} {-z}) 
            ({x[4]} {-r} {-z}) ({x[5]} {-r} {-z}) ({x[6]} {-r} {-z}) ({x[7]} {-r} {-z})
            
            ({x[0]} {r} {-z}) ({x[1]} {r} {-z}) ({x[2]} {r} {-z}) ({x[3]} {r} {-z}) 
            ({x[4]} {r} {-z}) ({x[5]} {r} {-z}) ({x[6]} {r} {-z}) ({x[7]} {r} {-z})
            
            ({x[1]} {r+bh} {-z}) ({x[2]} {r+bh} {-z})
            ({x[3]} {r+bh} {-z}) ({x[4]} {r+bh} {-z})
            ({x[5]} {r+bh} {-z}) ({x[6]} {r+bh} {-z})

            ({x[0]} {-r} {z}) ({x[1]} {-r} {z}) ({x[2]} {-r} {z}) ({x[3]} {-r} {z}) 
            ({x[4]} {-r} {z}) ({x[5]} {-r} {z}) ({x[6]} {-r} {z}) ({x[7]} {-r} {z})
            
            ({x[0]} {r} {z}) ({x[1]} {r} {z}) ({x[2]} {r} {z}) ({x[3]} {r} {z}) 
            ({x[4]} {r} {z}) ({x[5]} {r} {z}) ({x[6]} {r} {z}) ({x[7]} {r} {z})
            
            ({x[1]} {r+bh} {z}) ({x[2]} {r+bh} {z})
            ({x[3]} {r+bh} {z}) ({x[4]} {r+bh} {z})
            ({x[5]} {r+bh} {z}) ({x[6]} {r+bh} {z})
        );
        blocks
        (
            hex (0 1 9 8 22 23 31 30) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (1 2 10 9 23 24 32 31) ({nx_br} {ny} 1) simpleGrading (1 1 1) 
            hex (2 3 11 10 24 25 33 32) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (3 4 12 11 25 26 34 33) ({nx_br} {ny} 1) simpleGrading (1 1 1) 
            hex (4 5 13 12 26 27 35 34) ({nx_gap} {ny} 1) simpleGrading (1 1 1)
            hex (5 6 14 13 27 28 36 35) ({nx_br} {ny} 1) simpleGrading (1 1 1) 
            hex (6 7 15 14 28 29 37 36) ({nx_gap} {ny} 1) simpleGrading (1 1 1)

            hex (9 10 17 16 31 32 39 38) ({nx_br} {ny_br} 1) simpleGrading (1 1 1)
            hex (11 12 19 18 33 34 41 40) ({nx_br} {ny_br} 1) simpleGrading (1 1 1)
            hex (13 14 21 20 35 36 43 42) ({nx_br} {ny_br} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 8 30 22)); }}
            outlet {{ type patch; faces (
                (16 17 39 38) (18 19 41 40) (20 21 43 42)
            ); }}
            walls  {{ type wall;  faces (
                (0 1 23 22) (1 2 24 23) (2 3 25 24) (3 4 26 25) (4 5 27 26) (5 6 28 27) (6 7 29 28)
                (7 15 37 29)
                (8 9 31 30) (10 11 33 32) (12 13 35 34) (14 15 37 36)
                (9 16 38 31) (10 32 39 17) 
                (11 18 40 33) (12 34 41 19)
                (13 20 42 35) (14 36 43 21)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 8 9 1) (1 9 10 2) (2 10 11 3) (3 11 12 4) (4 12 13 5) (5 13 14 6) (6 14 15 7)
                (9 16 17 10) (11 18 19 12) (13 20 21 14)
                (22 23 31 30) (23 24 32 31) (24 25 33 32) (25 26 34 33) (26 27 35 34) (27 28 36 35) (28 29 37 36)
                (31 32 39 38) (33 34 41 40) (35 36 43 42)
            ); }}
        );
        mergePatchPairs ();
    '''
