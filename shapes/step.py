
def generate(L, D, dens_mult):
    # Inlet is small (h), Outlet is large (H)
    # D here acts as the Inlet Diameter (h)
    # H = 2 * D
    h = D
    H = 2.0 * D
    z = 0.05
    
    # Inlet Section (Length L/3)
    # Outlet Section (Length 2L/3)
    x_step = L / 3.0
    x_end = L
    
    nx_inlet = int(15 * dens_mult)
    nx_outlet = int(30 * dens_mult)
    ny_h = int(15 * dens_mult)
    
    return f'''
        vertices
        (
            (0 0 {-z})       ({x_step} 0 {-z})       ({x_end} 0 {-z})
            (0 {h} {-z})     ({x_step} {h} {-z})     ({x_end} {h} {-z})
            ({x_step} {H} {-z}) ({x_end} {H} {-z})
            
            (0 0 {z})       ({x_step} 0 {z})       ({x_end} 0 {z})
            (0 {h} {z})     ({x_step} {h} {z})     ({x_end} {h} {z})
            ({x_step} {H} {z}) ({x_end} {H} {z})
        );
        blocks
        (
            hex (0 1 4 3 7 8 11 10) ({nx_inlet} {ny_h} 1) simpleGrading (1 1 1)
            hex (1 2 5 4 8 9 12 11) ({nx_outlet} {ny_h} 1) simpleGrading (1 1 1)
            hex (4 5 6 13 11 12 14 13) ({nx_outlet} {ny_h} 1) simpleGrading (1 1 1)
        );
        boundary
        (
            inlet  {{ type patch; faces ((0 10 11 3)); }}
            outlet {{ type patch; faces ((2 5 12 9) (5 6 14 12)); }}
            walls  {{ type wall;  faces (
                (0 1 8 7) (1 2 9 8) // Bottom
                (3 4 11 10) (13 6 14 13) // Top
                (4 13 13 11) // The Step Face (Vertical)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 3 4 1) (1 4 5 2) (4 13 6 5)
                (7 8 11 10) (8 9 12 11) (11 12 14 13)
            ); }}
        );
        mergePatchPairs ();
    '''
