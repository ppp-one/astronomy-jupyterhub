from glob import glob

import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from eloy import detection, psf, utils
from photutils.detection import DAOStarFinder


def find_files(target):
    print(f"Finding files for target '{target}'...\n")
    files = glob(f"data/{target}/**/*.fits", recursive=True)
    image_paths = {
        "light": {
            "RP": [],
            "G": [],
            "BP": [],
        },
        "flat": {
            "RP": [],
            "G": [],
            "BP": [],
        },
        "bias": [],
        "dark": [],
    }

    for file in files:
        header = fits.getheader(file)

        if header["IMAGETYP"].lower() == "light":
            image_paths["light"][header["FILTER"]].append(file)
        elif header["IMAGETYP"].lower() == "flat":
            image_paths["flat"][header["FILTER"]].append(file)
        elif header["IMAGETYP"].lower() == "bias":
            image_paths["bias"].append(file)
        elif header["IMAGETYP"].lower() == "dark":
            image_paths["dark"].append(file)

    print(f"Found {len(image_paths['light']['RP'])} RP light frames.")
    print(f"Found {len(image_paths['light']['G'])} G light frames.")
    print(f"Found {len(image_paths['light']['BP'])} BP light frames.")
    print(f"Found {len(image_paths['flat']['RP'])} RP flat frames.")
    print(f"Found {len(image_paths['flat']['G'])} G flat frames.")
    print(f"Found {len(image_paths['flat']['BP'])} BP flat frames.")
    print(f"Found {len(image_paths['bias'])} bias frames.")
    print(f"Found {len(image_paths['dark'])} dark frames.")

    return image_paths


def detect_stars_coords(data, threshold=5.0):
    regions = detection.stars_detection(data, threshold=threshold)
    # stars coords and cutouts
    region_coords = np.array(
        [(r.centroid_weighted[1], r.centroid_weighted[0]) for r in regions]
    )

    return region_coords


def measure_fwhm(data, coords):
    cutouts = utils.cutout(data, coords, (50, 50))
    # epsf modeling
    cutouts_normalized = cutouts / np.nanmax(cutouts, (1, 2))[:, None, None]
    epsf = np.nanmedian(cutouts_normalized, 0)
    psf_params = psf.fit_gaussian(epsf)
    fwhm = psf.gaussian_sigma_to_fwhm * np.mean(
        [psf_params["sigma_x"], psf_params["sigma_y"]]
    )
    return fwhm


def find_stars(
    data: np.ndarray,
    threshold: float = 5.0,
    peak_threshold: float | None = None,
    fwhm: float = 5.0,
    saturation_limit: float | None = None,
) -> np.ndarray:
    """
    Find stars using DAOStarFinder algorithm.

    Uses the photutils DAOStarFinder algorithm to detect point sources in
    astronomical images. The function performs background subtraction and
    returns star coordinates sorted by brightness.

    Parameters:
        data (np.ndarray): The 2D image data array.
        threshold (float, optional): Detection threshold in units of background
            standard deviation. Higher values detect fewer, brighter stars.
            Defaults to 5.0.
        fwhm (float, optional): Expected Full Width at Half Maximum of stars
            in pixels. Should match the typical seeing conditions. Defaults to 5.0.
        peak_threshold (float, optional): Threshold for the peak value of detected stars.
            Stars with peak values below this limit will be excluded. Defaults to None.
        saturation_limit (float, optional): Saturation limit for star detection.
            Stars with flux above this limit will be excluded. Defaults to None.

    Returns:
        np.ndarray: Array of detected star coordinates sorted by brightness.
            Shape is (N, 2) where N is the number of stars, and each row is (x, y).
            Returns an empty array if no stars are found.
    """
    # Calculate background statistics
    mean, median, std = sigma_clipped_stats(data, sigma=3.0)

    # Use DAOStarFinder for star detection
    dao_find = DAOStarFinder(
        fwhm=fwhm,
        threshold=threshold * std,
        exclude_border=True,
        min_separation=2 * fwhm,
    )
    dao_sources = dao_find(data)

    if dao_sources is None or len(dao_sources) == 0:
        return np.array([]).reshape(0, 2)

    # Sort sources by flux (brightness) in descending order
    sorted_indices = np.argsort(dao_sources["flux"])[::-1]
    dao_sources = dao_sources[sorted_indices]

    # Filter sources based on peak value
    if peak_threshold is None:
        peak_threshold = threshold

    dao_sources = dao_sources[dao_sources["peak"] > mean + peak_threshold * std]

    # Filter sources based on saturation limit
    if saturation_limit is not None:
        dao_sources = dao_sources[dao_sources["peak"] < saturation_limit]

    # Convert to (x, y) coordinates
    coordinates = np.column_stack([dao_sources["xcentroid"], dao_sources["ycentroid"]])

    return coordinates
