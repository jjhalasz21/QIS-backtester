import numpy as np
from scipy.stats import norm


def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))


def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return _d1(S, K, T, r, sigma) - sigma * np.sqrt(T)


def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes European call price."""
    if T <= 0:
        return max(S - K, 0.0)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return float(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))


def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes European put price."""
    if T <= 0:
        return max(K - S, 0.0)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return float(K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))


def delta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Delta: dV/dS. Call in (0,1), Put in (-1,0)."""
    if T <= 0:
        if option_type == "call":
            return 1.0 if S > K else 0.0
        return -1.0 if S < K else 0.0
    d1 = _d1(S, K, T, r, sigma)
    if option_type == "call":
        return float(norm.cdf(d1))
    return float(norm.cdf(d1) - 1)


def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Gamma: d2V/dS2. Same for calls and puts."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))


def vega(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Vega: dV/dsigma per 1% change in vol. Same for calls and puts."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return float(S * norm.pdf(d1) * np.sqrt(T) / 100)


def theta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Theta: dV/dt per calendar day (negative = time decay)."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
    if option_type == "call":
        term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
    else:
        term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
    return float((term1 + term2) / 365)


def rho(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Rho: dV/dr per 1% change in rates."""
    if T <= 0:
        return 0.0
    d2 = _d2(S, K, T, r, sigma)
    if option_type == "call":
        return float(K * T * np.exp(-r * T) * norm.cdf(d2) / 100)
    return float(-K * T * np.exp(-r * T) * norm.cdf(-d2) / 100)
