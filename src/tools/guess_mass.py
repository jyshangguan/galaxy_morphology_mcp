import os
import sys
import contextlib
os.environ['XLA_PYTHON_CLIENT_PREALLOCATE']='false'
import numpy as np
from astropy.io import ascii
from typing import Annotated, Union, Dict

from galfits import gsutils
from astropy.io import fits
from astropy.wcs import WCS
from astropy.cosmology import Planck18 as cosmo

@contextlib.contextmanager
def redirect_stdout_fd_to_stderr():
    stdout_fd = sys.stdout.fileno()
    saved_fd = os.dup(stdout_fd)
    
    try:
        os.dup2(sys.stderr.fileno(), stdout_fd)
        yield
    finally:
        os.dup2(saved_fd, stdout_fd)
        os.close(saved_fd)

def genlyric(fits_dir, galid, bands, fluxs, fluxs_err, lyric_file, z_fit=4.0):
    with open(lyric_file,'w') as param_file:
        param_file.write("# This is a galfitS configuration file for galaxy "+str(galid)+"\n")
        param_file.write("# The config file provide a galfitS setup to perform a single sersic SED fitting with multi-band images.\n")
        imgatlas = []
        for idx, band, flux, flux_err in zip(range(len(bands)), bands, fluxs, fluxs_err):
            if idx == 0:
                header = fits.getheader(os.path.join(fits_dir, band + ".fits"))
                shape = fits.getdata(os.path.join(fits_dir, band + ".fits")).shape
                ra,dec = WCS(header).all_pix2world((shape[0]+1)/2, (shape[1]+1)/2, 1)
                # Region information
                param_file.write("# Region information\n")
                param_file.write('R1) '+str(galid)+'\n')  # name of the target
                param_file.write('R2) ['+str(ra)+','+str(dec)+']\n')  # sky coordinate of the target [RA, Dec]
                param_file.write('R3) '+str(z_fit)+' \n\n') # redshift of the target

            imagel = chr(ord('a') + idx)    
            if np.size(flux) > 0 and ((flux.ndim > 0 and flux[0] > -90) or (flux.ndim == 0 and flux > -90)):
                imgatlas.append(imagel)
            else:
                continue
            mockfile = os.path.join(fits_dir, band + ".fits")
            param_file.write('# Image '+imagel.upper()+' \n')
            param_file.write('I'+imagel+'1)  [' + mockfile + ',0] \n') #sci image
            param_file.write('I'+imagel+'2)  '+band+'\n') # band name
            param_file.write('I'+imagel+'3)  [' + mockfile + ',2] \n') # sigma image
            param_file.write('I'+imagel+'4)  [' + mockfile + ',3]\n') #psf image
            param_file.write('I'+imagel+'5)  1\n') # PSF fine sampling factor relative to data
            param_file.write('I'+imagel+'6)  [Noimg,0]\n') #mask image
            param_file.write('I'+imagel+'7)  cR\n') # unit of the image
            param_file.write('I'+imagel+'8)  -1 \n') # size to make cutout image region for fitting, unit arcsec
            param_file.write('I'+imagel+'9)  1 \n') # Conversion from image unit to flambda, -1 for default
            param_file.write('I'+imagel+'10) 27.461825709242483\n') # Magnitude photometric zeropoint                          ## mag zp calculate
            param_file.write('I'+imagel+'11) uniform\n') # sky model
            param_file.write('I'+imagel+'12) [[0,-0.5,0.5,0.1,0]]\n') # sky parameter, (value, min, max, step)
            param_file.write('I'+imagel+'13) 0\n') # allow relative shifting
            param_file.write('I'+imagel+'14) [[0,-5,5,0.1,0],[0,-5,5,0.1,0]]\n') # [shiftx, shifty]
            param_file.write('I'+imagel+'15) 1\n\n') # Use SED information

        age= round(cosmo.age(z_fit).value,2)-0.2 
        age_list = [0] + list(np.logspace(-1, np.log10(age), 5))

        param_file.write("# Image atlas\n")
        param_file.write("Aa1) 'all'\n") # name of the image atlas
        param_file.write("Aa2) "+str(imgatlas)+"\n") # images in this atlas
        param_file.write('Aa3) 0\n') # whether the images have same pixel size
        param_file.write('Aa4) 0\n') # link relative shiftings
        param_file.write('Aa5) []\n') # spectra
        param_file.write('Aa6) []\n') # aperture size
        param_file.write('Aa7) []\n\n') # references images
        
        param_file.write("# Profile A\n")
        param_file.write('Pa1) total\n') # name of the component
        param_file.write('Pa2) sersic\n') # profile type
        param_file.write('Pa3) [0,-0.3,0.3,0.1,0]\n') # x-center [arcsec]
        param_file.write('Pa4) [0,-0.3,0.3,0.1,0]\n') # y-center [arcsec]
        param_file.write('Pa5) [0.2,0.1,1.7,0.1,0]\n') # effective radius [arcsec]
        param_file.write('Pa6) [2,0.5,6,0.1,0]\n') # Sersic index
        param_file.write('Pa7) [0,-90,90,1,0]\n') # position angle (PA) [degrees: Up=0, Left=90]
        param_file.write('Pa8) [0.8,0.5,1,0.01,0]\n') # axis ratio (b/a) [0.1=round, 1=flat]
        param_file.write(f'Pa9) [[-2,-8,0,0.1,1],[-2,-8,0,0.1,1],[-2,-8,0,0.1,1],[-2,-8,0,0.1,1],[-2,-8,0,0.1,1]]\n') # contemporary log star formation fraction         ## sfr
        param_file.write(f'Pa10) [{round(age_list[0],2)}, {round(age_list[1],2)}, {round(age_list[2], 2)}, {round(age_list[3],2)}, {round(age_list[4],2)}, {round(age_list[5],2)}]\n') # burst stellar age [Gyr]          ## age 
        param_file.write('Pa11) [[0.02,0.001,0.04,0.001,1]]\n') # metallicity [Z=0.02=Solar]
        param_file.write('Pa12) [[0.7,0.3,5.1,0.1,1]]\n') # Av dust extinction [mag]
        param_file.write('Pa13) [100,40,200,1,0]\n') # stellar velocity dispersion
        param_file.write('Pa14) [9,6,12,0.1,1]\n') # log stellar mass
        param_file.write('Pa15) bins \n') # star formation history type: burst/conti                    ## change to bins 
        param_file.write('Pa16) [-2,-4,-2,0.1,0]\n') # logU nebular ionization parameter
        param_file.write('Pa26) [3,0,5,0.1,0]\n') # amplitude of the 2175A bump on extinction curve
        param_file.write('Pa27) 0\n') # SED model, 0: full; 1: stellar only; 2: nebular only; 3: dust only
        param_file.write('Pa28) [8.14,4.5,10,0.1,0]\n') # log dust mass
        param_file.write('Pa29) [1.0, 0.1, 50, 0.1, 0]\n') # Umin, minimum radiation field
        param_file.write('Pa30) [1.0, 0.47, 7.32, 0.1, 0]\n') # qPAH, mass fraction of PAH
        param_file.write('Pa31) [1.0, 1.0, 3.0, 0.1, 0]\n') # alpha, powerlaw slope of U
        param_file.write('Pa32) [0.1, 0, 1.0, 0.1, 0]\n\n') # gamma, fraction illuminated by star forming region

        # Galaixes
        param_file.write("# Galaxy A\n")
        param_file.write('Ga1) mygal\n') # name of the galaxy
        param_file.write("Ga2) ['a']\n") # profile component
        param_file.write('Ga3) ['+str(z_fit)+',0.01,12.0,0.01,0]\n') # galaxy redshift
        param_file.write('Ga4) 0.01\n') # the EB-V of Galactic dust reddening 
        param_file.write('Ga5) [1.0,0.5,2,0.05,0]\n') # normalization of spectrum when images+spec fitting
        param_file.write('Ga6) []\n') # narrow lines in nebular
        param_file.write('Ga7) 1\n\n') # number of components for narrow lines

def guess_mass(
    config_path: Annotated[str, "Path to the input .lyric configuration file"],
    workplace: Annotated[str, "Path to directory containing .gssummary file"],
    mass_output: Annotated[str, "Root directory for data storage and output. The directory of config_path will be used if None"] = None,
    model_name: Annotated[Union[str, None], "Name of the model for redshift lookup. The name of the last galaxy will be used if None"] = None,
    galaxy_id:  Annotated[Union[str, None], "Galaxy ID or name identifier. It will be set from the .lyric file if None"] = None,
) -> Annotated[Dict, "The status of generation of .lyric file for pure SED fitting"]:
    """
    Generate mass estimation configuration from GalfitS results.

    This function reads GalfitS fitting results from a .gssummary file,
    extracts flux information for specified bands and model components,
    and generates a pure SED .lyric file for subsequent pure SED fitting.

    Args:
        config_path: Path to input .lyric configuration file
        workplace: Directory containing {targ}.gssummary file from previous fit
        mass_output: Root directory for data storage and output
        model_name: Model name. The name of the last galaxy will be used if None.
        galaxy_id: Galaxy identifier

    Returns:
        A dictionary containing the status of .lyric file generation and the path to the generated file.
    """

    with redirect_stdout_fd_to_stderr():
        Myfitter, targ, fs = gsutils.read_config_file(config_path, workplace)

    smfile = ascii.read(f"{workplace}/{targ}.gssummary")
    for loopx in range(len(smfile)):
        Myfitter.lmParameters[smfile['pname'][loopx]].value = smfile["best_value"][loopx] ## load the best fitting results

    Myfitter.loose_fix_pars()
    Myfitter.cal_model_image()

    ## read the model flux 
    bands = Myfitter.GSdata.allbands
    fluxes_total = np.array([0.]*len(bands))

    model_idx = None
    for idx in range(len(Myfitter.model_list)):
        if Myfitter.model_list[idx].name == model_name:
            model_idx = idx
            break
    model_idx = model_idx if model_idx is not None else -1    
    model_name = model_name or Myfitter.model_list[model_idx].name
    galaxy_id = galaxy_id or targ

    for model_subcom_name in Myfitter.model_list[model_idx].subnames:
        fluxes = []
        for idx_band in range(len(bands)):

            im = Myfitter.GSdata.get_image(idx_band)
            zp = im.magzp
            logNorm = Myfitter.pardict[f"logNorm_{model_subcom_name}_{bands[idx_band]}"]
            logMass = Myfitter.pardict[f"logM_{model_subcom_name}"]

            mag_best_2 = zp - 2.5*(logNorm + logMass) ## key 

            flux_mJy = 3631*10**( - mag_best_2 / 2.5) * 10**3 ## from magnitude to flux (m Jy)
            # print("the mag read from gssummary is ", mag_best_2, "flux(mJy) is ", flux_mJy)
            fluxes.append(flux_mJy)
        fluxes = np.array(fluxes)
        fluxes_total += fluxes
    fluxes_err = 0.1 * fluxes_total ## for simplicity, we just assume err is 0.1 * flux.

    mass_output = mass_output or os.path.dirname(config_path)
    fits_dir = os.path.join(mass_output, f"{galaxy_id}_pure_sed") ## path change
    lyric_file = os.path.join(mass_output, f"{galaxy_id}_pure_sed.lyric")
    os.makedirs(fits_dir, exist_ok=True)

    z_fit = Myfitter.pardict[f"z_{model_name}"]

    for band, flux_mjy, flux_err in zip(bands, fluxes_total, fluxes_err):
        gsutils.photometry_to_img(band=band, flux=flux_mjy, flux_err=flux_err, z=z_fit, outputname=os.path.join(fits_dir,f"{band}.fits"), unit='mJy') ## create mock image !

    genlyric(galid = galaxy_id, lyric_file = lyric_file, fits_dir = fits_dir, bands=bands, fluxs=fluxes_total, fluxs_err=fluxes_err, z_fit=z_fit)

    return {"status": "success", "result": f"{lyric_file} is generated for pure SED fitting."}