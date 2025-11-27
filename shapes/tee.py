
def generate(L, D, dens_mult, mode="split"):
    r, z = D / 2.0, 0.05
    n_D = int(20 * dens_mult)
    if n_D % 2 != 0: n_D += 1
    n_L = int((L/D) * n_D)

    p_left = "inlet_left" if mode == "opposed" else "inlet"
    p_right = "inlet_right" if mode == "opposed" else "outlet_right"
    p_top = "outlet_top" if mode == "opposed" else "outlet_top"

    return f'''
        vertices
        (
            (0 {-r} {-z})   ({L} {-r} {-z})    ({L} {r} {-z})    (0 {r} {-z})
            (0 {-r} {z})    ({L} {-r} {z})     ({L} {r} {z})     (0 {r} {z})
            ({L+D} {-r} {-z}) ({L+2*L} {-r} {-z}) ({L+2*L} {r} {-z}) ({L+D} {r} {-z})
            ({L+D} {-r} {z})  ({L+2*L} {-r} {z})  ({L+2*L} {r} {z})  ({L+D} {r} {z})
            ({L} {r+L} {-z}) ({L+D} {r+L} {-z})
            ({L} {r+L} {z})  ({L+D} {r+L} {z})
        );
        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({n_L} {n_D} 1) simpleGrading (1 1 1)
            hex (1 8 11 2 5 12 15 6) ({n_D} {n_D} 1) simpleGrading (1 1 1)
            hex (8 9 10 11 12 13 14 15) ({n_L} {n_D} 1) simpleGrading (1 1 1)
            hex (2 11 17 16 6 15 19 18) ({n_D} {n_L} 1) simpleGrading (1 1 1)
        );
        edges ();
        boundary
        (
            {p_left}  {{ type patch; faces ((0 4 7 3)); }}
            {p_right} {{ type patch; faces ((9 10 14 13)); }}
            {p_top}   {{ type patch; faces ((17 16 18 19)); }}
            walls  {{ type wall;  faces (
                (0 1 5 4) (3 7 6 2)
                (1 8 12 5)
                (8 9 13 12) (10 11 15 14)
                (11 17 19 15) (16 2 6 18)
            ); }}
            frontAndBack {{ type empty; faces (
                (0 3 2 1) (4 5 6 7) 
                (1 2 11 8) (5 6 15 12)
                (8 11 10 9) (12 15 14 13)
                (2 16 17 11) (6 18 19 15)
            ); }}
        );
        mergePatchPairs ();
    '''
