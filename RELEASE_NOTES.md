# ConnecTUM Release Notes - Version 1 (presentation)

## Release Information
- **Version**: 1.0.0 (presentation)
- **Release Name**: Version 1 (presentation)
- **Based on Tag**: v1.2-stable
- **Commit**: 569eb2978b43382f470984380b227fd4f426b877
- **Release Date**: [To be set when release is created]

## Overview
This release represents the stable version of ConnecTUM as presented in the final project presentation. ConnecTUM is a computer vision-based Connect 4 game implementation that combines physical game detection with AI gameplay.

## What's New
- Complete Connect 4 game implementation with computer vision
- Last move indicator in CLI interface (latest feature in this release)
- Web-based frontend interface
- REST API backend for game management
- Real-time camera-based game board detection

## Key Features
### Core Functionality
- **Computer Vision**: Real-time detection of Connect 4 game board and pieces
- **AI Algorithm**: Connect 4 solver with configurable difficulty levels
- **Web Interface**: Modern Next.js frontend for game interaction
- **API Backend**: FastAPI-based backend with game state management
- **Hardware Integration**: Raspberry Pi camera support and GPIO controls

### Technical Components
- **Frontend**: Next.js application with React components
- **Backend**: Python FastAPI server with game logic
- **Computer Vision**: OpenCV-based image processing
- **AI Engine**: C++ Connect 4 solver with Python bindings
- **Hardware**: Raspberry Pi integration with camera and mechanical controls

## Installation & Usage
Please refer to the README.md file for detailed installation and usage instructions.

### Quick Start
```bash
# Install system dependencies
sudo apt install libcap-dev python3-picamera2 gnome-terminal

# Set up Python environment
python -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt

# Start backend
uvicorn api:app --reload

# Start frontend (in another terminal)
cd connectum-frontend
pnpm install
pnpm dev
```

## Assets Included
- Complete source code
- Installation scripts
- Configuration files
- Final presentation PDF (presentation/connecTUM_Final_Presentation.pdf)
- Documentation and README

## Known Limitations
- Due to GitHub's repository size limitations, precomputed lookup tables for the game algorithm are not included in this repository
- The algorithm will run slower than the full version as a result
- The complete repository with all files is available at the [LRZ GitLab Instance](https://gitlab.lrz.de/00000000014BAEC1/connectum)

## System Requirements
- Python 3.8+
- Node.js and npm/pnpm
- OpenCV dependencies
- Raspberry Pi (for hardware integration)
- Compatible camera module

## Contributors
- Project developed as part of CPS Course at TUM-HN
- See git commit history for detailed contributor information

## Links
- [Project Final Presentation](presentation/connecTUM_Final_Presentation.pdf)
- [Demo Video](https://tumde-my.sharepoint.com/:v:/g/personal/alexandros_stathakopoulos_tum_de/EU2jDR5xKNdJrphORsgSyrABKzXtXDRAS3JFElj_Iw2Pwg)
- [Full Repository (LRZ GitLab)](https://gitlab.lrz.de/00000000014BAEC1/connectum)

---

## For Release Creation
This release should be created from tag `v1.2-stable` with the title "Version 1 (presentation)".

**Manual Release Creation Steps:**
1. Navigate to GitHub repository releases page
2. Click "Create a new release"
3. Select existing tag: `v1.2-stable`
4. Set release title: `Version 1 (presentation)`
5. Copy the above content as release description
6. Mark as stable release (not pre-release)
7. Publish release