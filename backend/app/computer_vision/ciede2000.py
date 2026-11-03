import math
from typing import Tuple

def ciede2000(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float], kl: float = 1.0, kc: float = 1.0, kh: float = 1.0) -> float:
    """
    Computes the CIEDE2000 (Delta E 2000) color difference between two CIELAB colors.
    lab1: (L1*, a1*, b1*)
    lab2: (L2*, a2*, b2*)
    """
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    # Step 1: Calculate C1, C2, and mean C
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_bar = (C1 + C2) / 2.0

    C_bar_7 = C_bar**7
    G = 0.5 * (1.0 - math.sqrt(C_bar_7 / (C_bar_7 + 25.0**7)))

    # Step 2: Compute a', C', and h'
    a1_prime = (1.0 + G) * a1
    a2_prime = (1.0 + G) * a2

    C1_prime = math.sqrt(a1_prime**2 + b1**2)
    C2_prime = math.sqrt(a2_prime**2 + b2**2)

    def compute_h_prime(b: float, a_prime: float) -> float:
        if a_prime == 0 and b == 0:
            return 0.0
        h_rad = math.atan2(b, a_prime)
        h_deg = math.degrees(h_rad)
        if h_deg < 0:
            h_deg += 360.0
        return h_deg

    h1_prime = compute_h_prime(b1, a1_prime)
    h2_prime = compute_h_prime(b2, a2_prime)

    # Step 3: Calculate Delta L', Delta C', Delta H'
    delta_L_prime = L2 - L1
    delta_C_prime = C2_prime - C1_prime

    if C1_prime * C2_prime == 0:
        delta_h_prime = 0.0
    elif abs(h2_prime - h1_prime) <= 180.0:
        delta_h_prime = h2_prime - h1_prime
    elif (h2_prime - h1_prime) > 180.0:
        delta_h_prime = (h2_prime - h1_prime) - 360.0
    else:
        delta_h_prime = (h2_prime - h1_prime) + 360.0

    delta_H_prime = 2.0 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(delta_h_prime / 2.0))

    # Step 4: Calculate L_bar', C_bar', and H_bar'
    L_bar_prime = (L1 + L2) / 2.0
    C_bar_prime = (C1_prime + C2_prime) / 2.0

    if C1_prime * C2_prime == 0:
        H_bar_prime = h1_prime + h2_prime
    elif abs(h1_prime - h2_prime) <= 180.0:
        H_bar_prime = (h1_prime + h2_prime) / 2.0
    elif (h1_prime + h2_prime) < 360.0:
        H_bar_prime = (h1_prime + h2_prime + 360.0) / 2.0
    else:
        H_bar_prime = (h1_prime + h2_prime - 360.0) / 2.0

    # Step 5: Calculate T
    T = (1.0 
         - 0.17 * math.cos(math.radians(H_bar_prime - 30.0))
         + 0.24 * math.cos(math.radians(2.0 * H_bar_prime))
         + 0.32 * math.cos(math.radians(3.0 * H_bar_prime + 6.0))
         - 0.20 * math.cos(math.radians(4.0 * H_bar_prime - 63.0)))

    # Step 6: Weighting functions SL, SC, SH
    L_term = (L_bar_prime - 50.0)**2
    SL = 1.0 + (0.015 * L_term) / math.sqrt(20.0 + L_term)
    SC = 1.0 + 0.045 * C_bar_prime
    SH = 1.0 + 0.015 * C_bar_prime * T

    # Step 7: Rotation function RT
    delta_theta = 30.0 * math.exp(-(((H_bar_prime - 275.0) / 25.0)**2))
    C_bar_prime_7 = C_bar_prime**7
    RC = 2.0 * math.sqrt(C_bar_prime_7 / (C_bar_prime_7 + 25.0**7))
    RT = -math.sin(math.radians(2.0 * delta_theta)) * RC

    # Final Delta E 2000
    term_L = delta_L_prime / (kl * SL)
    term_C = delta_C_prime / (kc * SC)
    term_H = delta_H_prime / (kh * SH)

    delta_E = math.sqrt(term_L**2 + term_C**2 + term_H**2 + RT * term_C * term_H)
    return float(delta_E)
