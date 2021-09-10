
# Table of Contents
{:toc}

# Basic Project Info

### Project Title
cros-map: learning AD signatures in aging and ~cross-mapping~ them to development

### Brief Project Description
ROS/MAP is a dataset of >1000 healthy and congitively impaired individuals with structural and functional neuroimaging data. A handful also have postmortem neuropathology data. We will use this data to derive autopsy-validated imaging signatures of vulnerability and resilience to neurodegenerative pathology. We will then examine these signatures in a neurodevelopment cohort (RBC) and test whether factors such as SES and education influence the development of regions that later confer resilience or vulnerability to brain pathology.

### Project Lead(s)
Jacob W Vogel

### Faculty Lead(s)
Theodore D Satterthwaite

### Analytic Replicator
Currently not designated

### Collaborators

#### Data acquisition and dataset knowledge
- Chris Gaiteri

#### Data Processing
- Matthew Cieslak
- Sydney Covitz

#### Analysis
TBA

### Project Start Date
September 10, 2020

### Current Project Status
Data preprocessing

### Dataset
- Religions Order Studies / Memory and Aging Project (ROS/MAP)
- Reproducible Brain Charts (RBC)

### Github repo
[link to Github repo](https://github.com/PennLINC/cros-map)

### Path to data on filesystem
Path to BIDS dataset on CUBIC: `/cbica/projects/rosmap_fmri/rosmap/`

### Slack Channel
`#rosmap`

### Trello board
[link to Trello board](https://trello.com/c/u0LrG38M/34-process-ros-map-rsfmri-data)

### Google Drive Folder
None, currently. Maybe one day.

### Zotero library
Coming "soon"

### Current work products
At the moment, zilch.

# Code documentation
## Data Curation and Processing
### Overview
The curation and processing of this dataset follows a Datalad -> BIDS -> fmriprep pipeline, mostly consistent with [the way](https://pennlinc.github.io/docs/TheWay/TheWay/). To be more precise, the dataset was registered with datalad literally at the genesis of the curation effort, and nearly every single command used to get from the archive of raw data to its current (almost) processed form has been registered using `datalad run` commands. The bad news about this is that the process was agonizing and painstaking. The good news is that there is almost complete data provenance. If one were to navigate to the `rosmap_fmri` directory on cubic, or any of its subdirectories, and type `git log`, one would see a log of all changes made to the dataset. This includes timestamps and calls to existing scripts, as well as records of files and file structures at the time of and right after script execution. 

One drawback of this method is that there isn't really room for mistakes. So, if mistakes were made in the curation effort, I had to either a) go back in time (e.g. `git reset --hard`) and correct them, or b) write another script to correct the issue. As often as possible I tried to do a), but because of occasional extremely long run-time of scripts and/or subseqeunt datalad registration, b) would happen sometimes. Luckily, the git logs show the exact order that these scripts were run, and the exact state of the dataset when they were run.

The processing scripts live [here](https://github.com/PennLINC/cros-map/tree/main/bids). I will try to give an account of events that happened during processing, and which scripts were used during each step.

### Curation
#### Dataset information
ROSMAP has data from three sites: Bannockburn (BNK), U Chicago (UC) and Morton Grove (MG). Data has been collected since 2011, and has gone through several protocol changes over the years, which are documented [here](https://www.radc.rush.edu/docs/var/scannerProtocols.htm). When I asked for the data, I received literally every file that, judging by the filename, *might* be BOLD or a BOLD-related fieldmap. So a) I got a lot of junk I didn't need, b) didn't really know what anything was, c) the BNK BOLD data had no jsons, d) I got T1s separately, so some were missing and none had jsons. Needless to say, the curation effort was a journey. 

#### Initial curation effort
The initial archive, which lives in `rosmap/sourcedata`, was unzipped and copied into `rosmap/rawdata` in a BIDS-friendly fashion. What do I mean by BIDS-friendly? See [here](https://bids-specification.readthedocs.io/en/stable/).  This effort used the following scripts:
- rosmap_bidsify.py
- rosmap_postBIDs.py

#### Dealing with mistakes
It was revealed that I was a fraud who knew little about the ways of images. Several rounds of `cubids-validate` (was actually called `bond` at that point instead of `cubids`) revealed my profound lack of understanding in imaging sequences and BIDS specification. Many scripts were written to deal with these mistakes. Also, initially we didn't know what to do with the BNK bold because it had lots of issues, so we quarantined it for a time.
- rosmap_postvalidation.py
- rosmap_postvalidation2.py
- rosmap_postvalidation3_json.py
- rosmap_postvalidation3_nii.py
- rosmap_postvalidation4.py
- quarantine_bnkbold.py
- rosmap_build_template_jsons.py

#### Dealing with trouble and missing data
To move forward, we needed to deal with the missing BNK and T1 jsons. We also needed to quarantine scans that had key missing elements or were repeatedly failing validation.
- unquarantine_bnkbold.py
- rosmap_fix_BNKfMRI_fromscratch.py
- rosmap_import_newbnks.py
- rosmap_quarantine_trouble.py
- rosmap_quarantine_trouble2.py
- rosmap_quarantine_trouble3.py

#### A series of fmap mishaps
After running through apply and doing some exemplar testing, some more issues were revealed with how I had curated some of the fieldmaps. It was also around this time that we decided to add protocol to the acquisition string and to jsons. 
- rosmap_addprotocol.py
- rosmap_postapply_log_update.py
- rosmap_handle_fmap_fmriprep_issue.py
- rosmap_postapply_addPED.py
- rosmap_postapply_add_fmap_2TE.py
- rosmap_postapply_add_fmap_2TE_part2.py
- rosmap_untether_bnk_fmaps.py

#### The UC images weren't missing at all!
Made it all the way through exemplar testing, but afterward we found that there were no UC BOLD (that's right I didn't realize it until we got all the way here), there were several missing T1s, and there was *yet another* fieldmap-related issue. After going back and forth a bit with Chris, it turned out we *did* have the UC BOLD data, I just didn't realize it and assumed it was non-BOLD EPI. So, I had to go back and re-curate that UC BOLD data to make it and its corresponding fieldmaps BIDS-compatible.
- rosmap_move_epis_to_func.py
- rosmap_update_EPI_jsons.py
- rosmap_fmap_to_phasediff2.py

#### And then we suddenly had T1 jsons
Shortly after the UC BOLD debacle, Chris sent over all the T1 data to see if we could find anything missing. Turns out, he also sent the JSONs for all the T1s! So I got to work replacing all the existing T1s and adding jsons.
- rosmap_bidsify_T1s.py
- rosmap_fix_sess_discrep_postT1.py

#### Test-driven data purge
At time of writing, fmriprep is being run on a bit over 200 acquisition group exemplars (e.g. subject sessions that have image and acquisition parameters that are representative of unique sets of subjects). Once we have audited this output (and addressed any lingering issues), we will combine the audit information with the output of `cubids-group` to determine which scans are unnecessary or problematic. These will be deleted or quarantined. After, all remaning subject sessions should have a high likelihood of completing preprocessing steps.

### Pre-processing
Pre-processing will consist of bootstrapped fmriprep runs in executed with scripts from [this repo](https://github.com/PennLINC/TheWay/tree/main/scripts/cubic), following recommendations of [the way](https://pennlinc.github.io/docs/TheWay/RunningDataLadPipelines/). 

At present, we are using fmriprep v20.2.3, which can be found in the `/cbica/projects/rosmap_fmri/software/fmriprep` directory. The following scripts and commands are used to run the preprocessing:
* `bash bootstrap-fmriprep-multises.sh /cbica/projects/rosmap_fmri/rosmap/exemplars /cbica/projects/rosmap_fmri/software/fmriprep/fmriprep`

...to be continued

## Data Analysis
No analysis at the moment. But one day! The general plan is to extract vulnerable and resilient AD networks using ROS/MAP data and project these networks onto developing individuals.