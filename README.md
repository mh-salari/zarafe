# Zarafe <img src="https://github.com/mh-salari/zarafe/raw/main/resources/app_icon.ico" alt="zarafe" width="30" height="30">

Zarafe is a video annotation tool designed for marking time events in eye tracking videos with gaze data visualization.

<p align="center">
<img src="https://github.com/mh-salari/zarafe/raw/main/resources/app.png" alt="EyE Annotation Tool Main Page" width="800">
</p>

## Overview

This tool allows users to:
- Load directories containing worldCamera.mp4 recordings and gazeData.tsv files
- View eye tracking videos with gaze position overlays
- Create, mark and manage time-based event annotations
- Save annotations to CSV files for further analysis

## Data Preparation

**Important**: Before using Zarafe, you need to convert your eye tracking data:

Zarafe uses [glassesValidator](https://github.com/dcnieho/glassesValidator) to import your eye tracking data. Some eye trackers require preprocessing before importing:

- **Pupil Labs**: Export from Pupil/Neon Player (disable World Video Exporter) or Pupil Cloud
- **Meta Project Aria Gen 1**: Process in Aria Studio with MPS eye gaze run, then use provided export script
- **SMI ETG**: Export raw data and scene video from BeGaze with specific settings

For detailed preprocessing instructions for your specific eye tracker, see the [glassesValidator preprocessing guide](https://github.com/dcnieho/glassesValidator?tab=readme-ov-file#eye-trackers).

The import process will generate the required worldCamera.mp4 and gazeData.tsv files.

Zarafe expects a specific directory structure with each recording in its own folder containing both files.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/mh-salari/zarafe.git
   cd zarafe
   ```

2. Install dependencies (choose one method):

   **Option A: Using uv (recommended)**
   ```bash
   # Install uv from https://docs.astral.sh/uv/getting-started/installation/

   # Install dependencies
   uv sync
   ```

   **Option B: Using pip**
   ```bash
   pip install -e .
   ```

3. Run the application:
   ```bash
   # With uv
   uv run python main.py

   # With pip
   python main.py
   ```

## Notes

Zarafe was developed by Mohammadhossein Salari with assistance from Claude 3.7 Sonnet, an AI assistant developed by Anthropic. Please be aware that this software is primarily for internal purposes and is not thoroughly documented. 


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments


Zarafe uses glassesValidator for data import. If you use this functionality, please cite:

Niehorster, D.C., Hessels, R.S., Benjamins, J.S., Nyström, M. and Hooge, I.T.C. (2023). GlassesValidator: A data quality tool for eye tracking glasses. *Behavior Research Methods*. [doi: 10.3758/s13428-023-02105-5](https://doi.org/10.3758/s13428-023-02105-5)


This project has received funding from the European Union's Horizon Europe research and innovation funding program under grant agreement No 101072410, Eyes4ICU project.

<p align="center">
<img src="https://github.com/mh-salari/zarafe/raw/main/resources/Funded_by_EU_Eyes4ICU.png" alt="Funded by EU Eyes4ICU" width="500">
</p>

Giraffe icon downloaded from <a href="https://www.flaticon.com/free-icons/giraffe" title="giraffe icons">Flaticon, created by smalllikeart</a>