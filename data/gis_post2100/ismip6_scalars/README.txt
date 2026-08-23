This archive provides the ice sheet model outputs produced as part of the publication "Payne et al. 2021 Future sea level change under CMIP5 and CMIP6 scenarios from the Greenland and Antarctic ice sheets", published in GRL

Contact: Tony Payne a.j.payne@bristol.ac.uk, Sophie Nowicki sophien@buffalo.edu, ismip6@gmail.com 


Further information on ISMIP6 can be found here:
http://www.climate-cryosphere.org/activities/targeted/ismip6
http://www.climate-cryosphere.org/wiki/index.php?title=ISMIP6-Projections-Antarctica
http://www.climate-cryosphere.org/wiki/index.php?title=ISMIP6-Projections-Greenland

Data usage notice:
If you use any of these results, please acknowledge the work of the people involved in the process producing this data set. Acknowledgements should have language similar to the below (if you only use CMIP5 forcing, remove CMIP6 and vice versa).

“We thank the Climate and Cryosphere (CliC) effort, which provided support for ISMIP6 through sponsoring of workshops, hosting the ISMIP6 website and wiki, and promoted ISMIP6. We acknowledge the World Climate Research Programme, which, through it's Working Group on Coupled Modelling, coordinated and promoted CMIP5 and CMIP6. We thank the climate modeling groups for producing and making available their model output, the Earth System Grid Federation (ESGF) for archiving the CMIP data and providing access, the University at Buffalo for ISMIP6 data distribution and upload, and the multiple funding agencies who support CMIP5 and CMIP6 and ESGF. We thank the ISMIP6 steering committee, the ISMIP6 model selection group and ISMIP6 dataset preparation group for their continuous engagement in defining ISMIP6."

You should also refer to and cite the following papers:

For Greenland datasets 

Heiko Goelzer, Sophie Nowicki, Anthony Payne, Eric Larour, Helene Seroussi, William H. Lipscomb, Jonathan Gregory, Ayako Abe-Ouchi, Andy Shepherd, Erika Simon, Cecile Agosta, Patrick Alexander, Andy Aschwanden, Alice Barthel, Reinhard Calov, Christopher Chambers, Youngmin Choi, Joshua Cuzzone, Christophe Dumas, Tamsin Edwards, Denis Felikson, Xavier Fettweis, Nicholas R. Golledge, Ralf Greve, Angelika Humbert, Philippe Huybrechts, Sebastien Le clec'h, Victoria Lee, Gunter Leguy, Chris Little, Daniel P. Lowry, Mathieu Morlighem, Isabel Nias, Aurelien Quiquet, Martin Rückamp, Nicole-Jeanne Schlegel, Donald Slater, Robin Smith, Fiamma Straneo, Lev Tarasov, Roderik van de Wal, and Michiel van den Broeke: The future sea-level contribution of the Greenland ice sheet: a multi-model ensemble study of ISMIP6 , The Cryosphere, 2020. doi:10.5194/tc-2019-319

Slater, D. A., Felikson, D., Straneo, F., Goelzer, H., Little, C. M., Morlighem, M., Fettweis, X., and Nowicki, S.: Twenty-first century ocean forcing of the Greenland ice sheet for modelling of sea level contribution , The Cryosphere, 14, 985–1008, https://doi.org/10.5194/tc-14-985-2020, 2020.

Sophie Nowicki, Antony Payne, Heiko Goelzer, Helene Seroussi, William Lipscomb, Ayako Abe-Ouchi, Cecile Agosta, Patrick Alexander, Xylar Asay-Davis, Alice Barthel, Thomas Bracegirdle, Richard Cullather, Denis Felikson, Xavier Fettweis, Jonathan Gregory, Tore Hatterman, Nicolas Jourdain, Peter Kuipers Munneke, Eric Larour, Christopher Little, Mathieu Morlinghem, Isabel Nias, Andrew Shepherd, Erika Simon, Donald Slater, Robin Smith, Fiammetta Straneo, Luke Trusel, Michiel van den Broeke, and Roderik van de Wal: 
Experimental protocol for sea level projections from ISMIP6 standalone ice sheet models, The Cryosphere, doi:10.5194/tc-2019-322, 2020.

For Antarctica datasets

Seroussi, H., Nowicki, S., Simon, E., Abe-Ouchi, A., Albrecht, T., Brondex, J., Cornford, S., Dumas, C., Gillet-Chaulet, F., Goelzer, H., Golledge, N. R., Gregory, J. M., Greve, R., Hoffman, M. J., Humbert, A., Huybrechts, P., Kleiner, T., Larour, E., Leguy, G., Lipscomb, W. H., Lowry, D., Mengel, M., Morlighem, M., Pattyn, F., Payne, A. J., Pollard, D., Price, S. F., Quiquet, A., Reerink, T. J., Reese, R., Rodehacke, C. B., Schlegel, N.-J., Shepherd, A., Sun, S., Sutter, J., Van Breedam, J., van de Wal, R. S. W., Winkelmann, R., and Zhang, T.: initMIP-Antarctica: an ice sheet model initialization experiment of ISMIP6, The Cryosphere, 13, 1441–1471, https://doi.org/10.5194/tc-13-1441-2019, 2019.

Jourdain, N. C., Asay-Davis, X., Hattermann, T., Straneo, F., Seroussi, H., Little, C. M., and Nowicki, S.: A protocol for calculating basal melt rates in the ISMIP6 Antarctic ice sheet projections, The Cryosphere, 14, 3111–3134, https://doi.org/10.5194/tc-14-3111-2020, 2020.


Sophie Nowicki, Antony Payne, Heiko Goelzer, Helene Seroussi, William Lipscomb, Ayako Abe-Ouchi, Cecile Agosta, Patrick Alexander, Xylar Asay-Davis, Alice Barthel, Thomas Bracegirdle, Richard Cullather, Denis Felikson, Xavier Fettweis, Jonathan Gregory, Tore Hatterman, Nicolas Jourdain, Peter Kuipers Munneke, Eric Larour, Christopher Little, Mathieu Morlinghem, Isabel Nias, Andrew Shepherd, Erika Simon, Donald Slater, Robin Smith, Fiammetta Straneo, Luke Trusel, Michiel van den Broeke, and Roderik van de Wal: 
Experimental protocol for sea level projections from ISMIP6 standalone ice sheet models, The Cryosphere, doi:10.5194/tc-2019-322, 2020.



------------------------------------------------------------------------------------
GREENLAND
------------------------------------------------------------------------------------
About the CMIP6 forced Greenland data:
- The results are based on model output regridded conservatively to a 5x5 km regular ISMIP6 grid unless this is already the native grid. 
- The results are calculated over the ice-covered area of Greenland, map projection error corrected, ice sheet model specific densities taken into account.
- The contribution of peripheral glaciers and ice caps has been removed, by considering their area-coverage in each grid cell.
- The results for the projections 'exp*' are all calculated as differences to the control experiment ctrl_proj (suffix cr in filename for control removed).
- The data was prepared by Heiko Goelzer using the same codes as the CMIP5 forced Datasets presented in Goelzer et al. (2020), which are available from https://doi.org/10.5281/zenodo.3939037
- The CMIP6 integrated atmosphere and ocean datasets were presented in Nowicki et al. (2020) and Slater et al. (2020). The integrated measures were computed from full datasets that available from input4MIP https://esgf-node.llnl.gov/projects/input4mips/

Directory structure:
Atmosphere
 smb_GrIS_cmipmodel_scenario.nc
 st_GrIS_cmipmodel_scenario.nc
 ...
cmipmodel correspond to:
ACCESS1_3, CESM2, CNRM-CM6-1,  CNRM-ESM2-1, CSIRO_Mk3_6_0, HadGEM2_ES, IPSL_CM5A_MR, MIROC5, NorESM1_M, UKESM1-0-LL

Scenario correspond to: rcp26, rcp85, ssp126, ssp585  

Smb variable correspond to surface mass balance
St variable correspond to surface temperature

Ocean
 tfanom_GrIS_cmipmodel_scenario.nc
 ...
cmipmodel correspond to:
ACCESS1_3, CESM2, CNRM-CM6-1,  CNRM-ESM2-1, CSIRO_Mk3_6_0, HadGEM2_ES, IPSL_CM5A_MR, MIROC5, NorESM1_M, UKESM1-0-LL

Scenario correspond to: rcp26, rcp85, ssp126, ssp585  

tfanom variable is thermal forcing

Ice
   scalars_mm_cr_GIS_groupname1_modelname1_expid.nc
        ...

expid correspond to:
Expb01:CNRM-CM6-1_ssp585, standard protocol for ocean forcing 
Expb02:CNRM-CM6-1_ssp126, standard protocol for ocean forcing 
Expb03:UKESM1-0-LL_ssp585, standard protocol for ocean forcing   
Expb04:CESM2_ssp585, standard protocol for ocean forcing  
Expb05:CNRM-ESM2-1_ssp585, standard protocol for ocean forcing 
Expb06:CNRM-CM6-1_ssp585, open protocol for ocean forcing 	
Expb07:CNRM-CM6-1_ssp126, open protocol for ocean forcing 
Expb08:UKESM1-0-LL_ssp585, open protocol for ocean forcing 
Expb09:CESM2_ssp585, open protocol for ocean forcing 
Expb10:CNRM-ESM2-1_ssp585, open protocol for ocean forcing 

Description of Greenland Variables:

scalars_mm_cr_GIS ----------------- Greenland wide numbers 

oarea - assumed ocean area [m2]
rhof - model specific freshwater density [kg m-3]
rhoi - model specific ice density [kg m-3]
rhow - model specific ocean water density [kg m-3]

time - time, typically in days since X
iarea - Fraction of grid cell covered by land ice [1]
iareagr - Fraction of grid cell covered by grounded ice sheet
iareafl - Fraction of grid cell covered by ice sheet flowing over seawater

ivol - ice volume [m3]
ivolgr - grounded ice volume [m3]
ivolfl - floating ice volume [m3]
ivaf - ice volume above flotation [m3]

lim - ice mass [kg]
limgr - grounded ice mass [kg]
limfl - floating ice mass [kg]
limaf - ice mass above flotation [kg]

sle - sea-level equivalent mass [m] !! decreases with mass loss !! 
smb - spatially integrated surface mass balance anomaly [kg s-1]




-------------------------------------------------------------------------------------
ANTARCTICA 
-------------------------------------------------------------------------------------
About the CMIP6 forced dataset:
- The results are based on ice sheet model output computed from the ISMIP6 native grids that vary between models. 
- The results are calculated over the ice-covered area of Antarctica, corrected for map projection errors, and ice sheet model specific densities are taken into account.
- Results for the experiments 'exp*' are provided both as raw results and calculated as differences to the control experiment (ctrl_proj_open or ctrl_proj_std depending on the experiment). The later files are named with "minus_ctrl_proj" to indicate that the control run is subtracted.
- The data was prepared by Helene Seroussi using the same codes as the CMIP5 forced Datasets presented in Seroussi et al. (2020), which are available from https://doi.org/10.5281/zenodo.3940765
- The CMIP6 integrated atmosphere and ocean datasets were presented in Nowicki et al. (2020) and Jourdain et al. (2020). The integrated measures were computed from full datasets that available from input4MIP https://esgf-node.llnl.gov/projects/input4mips/
------------------------------------------------

Directory structure:
Atmosphere
 smb_AIS_cmipmodel_scenario.nc
 st_AIS_cmipmodel_scenario.nc
 ...

cmipmodel correspond to:
CCSM4, CESM2, CNRM-CM6-1,  CNRM-ESM2-1, CSIRO_Mk3_6_0, HadGEM2_ES, IPSL_CM5A_MR, MIROC-ESM-CHEM, NorESM1_M, UKESM1-0-LL

Scenario correspond to: rcp26, rcp85, ssp126, ssp585  

Smb variable correspond to surface mass balance
St variable correspond to surface temperature

Ocean
 tfanom_region_cmipmodel_scenario.nc
 ...

cmipmodel correspond to:
CCSM4, CESM2, CNRM-CM6-1,  CNRM-ESM2-1, CSIRO_Mk3_6_0, HadGEM2_ES, IPSL_CM5A_MR, MIROC-ESM-CHEM, NorESM1_M, UKESM1-0-LL

Scenario correspond to: rcp26, rcp85, ssp126, ssp585  

tfanom variable correspond to thermal forcing


Ice
 computed_limnsw_minus_ctrl_proj_AIS_groupname1_modelname1_expid.nc
 ...

expid correspond to:
Expb01:CNRM-CM6-1_ssp585, open protocol for ocean forcing 
Expb02:CNRM-CM6-1_ssp126, open protocol for ocean forcing 
Expb03:UKESM1-0-LL_ssp585, open protocol for ocean forcing   
Expb04:CESM2_ssp585, open protocol for ocean forcing  
Expb05:CNRM-ESM2-1_ssp585, open protocol for ocean forcing 
Expb06:CNRM-CM6-1_ssp585, standard protocol for ocean forcing (PIGL gamma calibration, Medium)
Expb07:CNRM-CM6-1_ssp126, standard protocol for ocean forcing (PIGL gamma calibration, Medium)
Expb08:UKESM1-0-LL_ssp585,standard protocol for ocean forcing (PIGL gamma calibration, Medium)
Expb09:CESM2_ssp585, standard protocol for ocean forcing (PIGL gamma calibration, Medium)
Expb10:CNRM-ESM2-1_ssp585, standard protocol for ocean forcing (PIGL gamma calibration, Medium) 

-------------------------------------------------
Description of Antarctic variables:

limnsw - ice sheet mass above floatation [Gt]

time - time in years

[variable] - global variable integrated over the Antarctica ice sheet
[variable]_region_1 - variable integrated over West Antarctica 
[variable]_region_2 - variable integrated over East Antarctica 
[variable]_region_3 - variable integrated over the Antarctic Peninsula
[variable]_sector_X - variable integrated over the X sector of the Antarctic ice sheet (18 sectors, from 1 to 18)

