
def generate(L, D, dens_mult):
    r, z = D / 2.0, 0.05
    base_y = int(20 * dens_mult)
    if base_y % 2 != 0: base_y += 1
    x_cells = int((L / D) * base_y)
    
    return f'''
        vertices
        (
            (0 {-r} {-z}) ({L} {-r} {-z}) ({L} {r} {-z}) (0 {r} {-z})
            (0 {-r} {z}) ({L} {-r} {z}) ({L} {r} {z}) (0 {r} {z})
        );
        blocks ( hex (0 1 2 3 4 5 6 7) ({x_cells} {base_y} 1) simpleGrading (1 1 1) );
        edges ();
        boundary
        (
            inlet  {{ type patch; faces ((0 4 7 3)); }}
            outlet {{ type patch; faces ((1 2 6 5)); }}
            walls  {{ type wall;  faces ((0 1 5 4) (3 7 6 2)); }}
            frontAndBack {{ type empty; faces ((0 3 2 1) (4 5 6 7)); }}
        );
        mergePatchPairs ();
    '''
