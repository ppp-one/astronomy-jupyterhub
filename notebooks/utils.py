import batman
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from typing import Tuple, Callable, Optional
import warnings


def find_nearest_idx(array, value):
    """
    Finds nearest index in array from value provided

    Params:


    Returns:
        index

    Raises:
        None

    """

    array = np.asarray(array)
    if array.ndim == 1:
        idx = (np.abs(array - value)).argmin()
    else:
        idx = np.sum((np.abs(array - value)), axis=-1).argmin()
    return int(idx)


def calculate_next_transit_time(
    reference_time: float, period: float, start_time: float
) -> float:
    """
    Calculate the next transit time after a given start time.

    Parameters:
    -----------
    reference_time : float
        Reference transit time (BJD)
    period : float
        Orbital period in days
    start_time : float
        Time after which to find the next transit (BJD)

    Returns:
    --------
    float
        Next transit time (BJD)
    """
    transit_time = reference_time
    # Find the next transit after start_time
    while transit_time < start_time:
        transit_time += period
    return transit_time


def fit_quadratic_baseline(
    x: np.ndarray, y: np.ndarray
) -> Callable[[np.ndarray], np.ndarray]:
    """
    Fit a quadratic polynomial to baseline data points.

    This function fits a second-order polynomial to account for systematic
    trends in the out-of-transit data (e.g., instrumental drift, stellar variability).

    Parameters:
    -----------
    x : np.ndarray
        Time values for baseline points
    y : np.ndarray
        Flux values for baseline points

    Returns:
    --------
    Callable
        Function that evaluates the quadratic model at given x values
    """
    # Fit quadratic polynomial: ax² + bx + c
    coeffs = np.polyfit(x, y, deg=2)

    def quadratic_model(x_val: np.ndarray) -> np.ndarray:
        return coeffs[0] * x_val**2 + coeffs[1] * x_val + coeffs[2]

    return quadratic_model


def transit_fit(
    time: np.ndarray,
    flux: np.ndarray,
    duration_known: float,  # ~1.79 hours
    period_known: float,
    transittime: float,
    a_guess: float,
    rp_guess: float,
    inc_guess: float,
    plot_results: bool = True,
) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Fit a transit model to photometric data using the batman package.

    This function performs a least-squares fit of a transit light curve model
    to observed photometric data, accounting for systematic trends with a
    quadratic baseline correction.

    Parameters:
    -----------
    time : np.ndarray
        Time array (BJD)
    flux : np.ndarray
        Normalized flux measurements
    duration_known : float
        Known transit duration in days
    period_known : float
        Known orbital period in days
    transittime : float
        Reference transit time (BJD)
    a_guess : float
        Initial guess for semi-major axis in stellar radii
    rp_guess : float
        Initial guess for planet-to-star radius ratio
    inc_guess : float
        Initial guess for orbital inclination in degrees
    plot_results : bool
        Whether to create diagnostic plots

    Returns:
    --------
    Tuple[np.ndarray, np.ndarray, dict]
        - Best-fit parameters
        - Parameter uncertainties (1-sigma)
        - Dictionary with fit results and diagnostics
    """

    # Validate inputs
    if len(time) != len(flux):
        raise ValueError("Time and flux arrays must have the same length")
    if len(time) < 10:
        raise ValueError("Insufficient data points for fitting")

    # Calculate the transit time closest to the data
    t0_guess = calculate_next_transit_time(transittime, period_known, time[0])

    # Initial parameter guesses
    u1_guess = 0.4  # Quadratic limb darkening coefficient
    u2_guess = 0.3  # Quadratic limb darkening coefficient

    # Parameter names for output
    param_names = [
        "Mid-transit time (t0)",
        "Period",
        "a/Rs",
        "Rp/Rs",
        "Inclination (deg)",
        "u1",
        "u2",
    ]

    # Initial parameter vector
    p0 = [t0_guess, period_known, a_guess, rp_guess, inc_guess, u1_guess, u2_guess]

    # Define transit boundaries for baseline fitting
    # Select points outside the transit for baseline correction
    half_duration = duration_known / 2
    starttime_idx = np.argmin(np.abs(time - (t0_guess - half_duration)))
    endtime_idx = np.argmin(np.abs(time - (t0_guess + half_duration)))

    # Fit quadratic baseline to out-of-transit data
    baseline_time = np.concatenate((time[:starttime_idx], time[endtime_idx:]))
    baseline_flux = np.concatenate((flux[:starttime_idx], flux[endtime_idx:]))

    baseline_model = fit_quadratic_baseline(baseline_time, baseline_flux)

    def transit_model(
        t: np.ndarray,
        t0: float,
        per: float,
        a: float,
        rp: float,
        inc: float,
        u1: float,
        u2: float,
    ) -> np.ndarray:
        """
        Combined transit + baseline model.

        Parameters:
        -----------
        t : np.ndarray
            Time array
        t0 : float
            Mid-transit time
        per : float
            Orbital period
        a : float
            Semi-major axis in stellar radii
        rp : float
            Planet-to-star radius ratio
        inc : float
            Orbital inclination (degrees)
        u1, u2 : float
            Quadratic limb darkening coefficients

        Returns:
        --------
        np.ndarray
            Model flux values
        """
        # Set up batman transit parameters
        params = batman.TransitParams()
        params.t0 = t0  # Mid-transit time
        params.per = per  # Orbital period
        params.rp = rp  # Planet radius / stellar radius
        params.a = a  # Semi-major axis / stellar radius
        params.inc = inc  # Inclination (degrees)
        params.ecc = 0.0  # Eccentricity (circular orbit)
        params.w = 90.0  # Longitude of periastron (degrees)
        params.limb_dark = "quadratic"  # Limb darkening model
        params.u = [u1, u2]  # Limb darkening coefficients

        # Generate transit model
        transit = batman.TransitModel(params, t)
        transit_curve = transit.light_curve(params)

        # Apply baseline correction
        return transit_curve * baseline_model(t)

    # Define parameter bounds for fitting
    # [lower_bounds], [upper_bounds]
    bounds = (
        [time[0], period_known - 1 / 24, 2.0, 0.01, 80.0, 0.0, 0.01],  # Lower bounds
        [time[-1], period_known + 1 / 24, 50.0, 0.20, 90.0, 1.0, 1.0],  # Upper bounds
    )

    try:
        # Perform the fit
        popt, pcov = curve_fit(
            transit_model,
            time,
            flux,
            p0=p0,
            bounds=bounds,
            maxfev=5000,  # Increase max function evaluations
        )

        # Calculate parameter uncertainties
        perr = np.sqrt(np.diag(pcov))

        # Generate best-fit model
        best_fit = transit_model(time, *popt)
        residuals = flux - best_fit

        # Calculate fit statistics
        rms_residuals = np.sqrt(np.mean(residuals**2))

        # Print results
        print("=" * 60)
        print("TRANSIT FIT RESULTS")
        print("=" * 60)

        print(f"\nRMS residuals: {rms_residuals:.6f}")
        print(f"Number of data points: {len(time)}")

        print(f"\nInitial parameter guesses:")
        for name, val in zip(param_names, p0):
            if "time" in name.lower():
                print(f"  {name:>25}: {val:.6f} BJD")
            elif "period" in name.lower():
                print(f"  {name:>25}: {val:.6f} days")
            elif "inclination" in name.lower():
                print(f"  {name:>25}: {val:.2f}°")
            else:
                print(f"  {name:>25}: {val:.6f}")

        print(f"\nBest-fit parameters:")
        for name, val, err in zip(param_names, popt, perr):
            if "time" in name.lower():
                print(f"  {name:>25}: {val:.6f} ± {err:.6f} BJD")
            elif "period" in name.lower():
                print(f"  {name:>25}: {val:.6f} ± {err:.6f} days")
            elif "inclination" in name.lower():
                print(f"  {name:>25}: {val:.2f} ± {err:.2f}°")
            else:
                print(f"  {name:>25}: {val:.6f} ± {err:.6f}")

        # Create diagnostic plots
        if plot_results:
            fig, (ax1, ax2) = plt.subplots(
                2,
                1,
                figsize=(12, 8),
                sharex=True,
                gridspec_kw={"height_ratios": [3, 1]},
            )

            # Main light curve plot
            ax1.plot(
                time,
                flux,
                "k.",
                label="Observed data",
            )
            ax1.plot(
                time,
                transit_model(time, *p0),
                color="tab:blue",
                label="Initial guess",
            )
            ax1.plot(time, best_fit, "r-", label="Best-fit model")

            # Mark transit center
            ax1.axvline(
                popt[0],
                ls="--",
                color="gray",
                alpha=0.7,
                label=f"Fitted t₀ = {popt[0]:.6f} BJD",
            )

            ax1.set_ylabel("Relative Flux")
            ax1.legend(loc="best")
            ax1.grid(True)
            ax1.set_title(f"Transit Light Curve Fit")

            # Residuals plot
            ax2.plot(time, residuals, "k.", alpha=0.7)
            ax2.axhline(0, ls="--", color="red", alpha=0.7)

            ax2.set_xlabel("Time (BJD)")
            ax2.set_ylabel("Residuals")
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

        # Prepare results dictionary
        results = {
            "parameters": popt,
            "uncertainties": perr,
            "parameter_names": param_names,
            "best_fit_model": best_fit,
            "residuals": residuals,
            "rms_residuals": rms_residuals,
            "covariance_matrix": pcov,
        }

        return popt, perr, results

    except Exception as e:
        print(f"Fitting failed: {str(e)}")
        print("Try adjusting initial parameter guesses or bounds.")
        raise
