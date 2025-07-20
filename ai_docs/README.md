# HFE Pose Analysis System - Technical Documentation

## Overview

This directory contains comprehensive technical documentation for the HFE (Human Factors Engineering) Pose Analysis System - a web-based application that analyzes human posture from uploaded images using MediaPipe and provides ergonomic scoring.

## Documentation Index

### 📋 [01_system_architecture.md](./01_system_architecture.md)
**System Architecture Documentation**
- High-level system overview and component interactions
- Technology stack details (Nuxt.js, Flask, MediaPipe)
- Data flow and processing pipeline
- Directory structure and configuration
- Security and performance characteristics

### 🧠 [02_mediapipe_pose_analysis.md](./02_mediapipe_pose_analysis.md)
**MediaPipe Pose Analysis Algorithm**
- Detailed pose detection and analysis algorithm
- Mathematical functions for angle calculations
- Ergonomic scoring system and risk assessment
- Bilateral arm analysis methodology
- Visualization and annotation techniques

### 🔌 [03_api_endpoints.md](./03_api_endpoints.md)
**API Endpoints and Data Structures**
- REST API specification and request/response formats
- Complete data structure definitions
- Error handling and status codes
- CORS configuration and integration examples
- Performance considerations and rate limiting

### 🎨 [04_frontend_components.md](./04_frontend_components.md)
**Frontend Components and Functionality**
- Vue.js/Nuxt.js component architecture
- Reactive state management and user interactions
- UI layout structure and responsive design
- Image handling and modal functionality
- Accessibility and user experience features

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Frontend | Nuxt.js | 3.13+ | Web interface framework |
| UI Library | PrimeVue | 4.2+ | Component library |
| Styling | Tailwind CSS | Latest | Utility-first CSS |
| Backend | Flask | Latest | REST API server |
| API Framework | Flask-AppBuilder | 4.8+ | API scaffolding |
| Pose Detection | MediaPipe | 0.10+ | Computer vision ML |
| Image Processing | OpenCV | 4.8+ | Image manipulation |
| Computing | NumPy | 1.24+ | Numerical computations |

## Research Background

The pose analysis algorithm is based on established ergonomic research principles:

- **RULA (Rapid Upper Limb Assessment)**: Industry-standard ergonomic evaluation
- **NIOSH Guidelines**: Occupational safety and health standards
- **ISO 11228**: International standards for manual handling
- **MediaPipe Research**: Google's state-of-the-art pose estimation

## Contributing

### Documentation Updates
1. **Edit Source**: Modify relevant `.md` files in this directory
2. **Validate Links**: Ensure internal references work correctly
3. **Update Index**: Modify this README if adding new documents
4. **Version Control**: Commit changes with descriptive messages

### Code Documentation
- **API Changes**: Update `03_api_endpoints.md` for endpoint modifications
- **Algorithm Updates**: Revise `02_mediapipe_pose_analysis.md` for scoring changes
- **UI Updates**: Modify `04_frontend_components.md` for interface changes

## Support and Resources

### Internal Resources
- **Source Code**: `/web/backend/` and `/web/frontend/` directories
- **Research Code**: `/code/pose_score_from_image.ipynb`
- **Configuration**: Environment and config files in respective directories

### External Resources
- **MediaPipe Documentation**: https://mediapipe.dev/
- **Vue.js Guide**: https://vuejs.org/guide/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Nuxt.js Documentation**: https://nuxt.com/docs

### Community Support
- **GitHub Issues**: Report bugs and feature requests
- **Stack Overflow**: Technical questions with appropriate tags
- **Research Papers**: Ergonomics and computer vision literature

---
*Documentation Generated: 2025-01-20*
*System Version: v1.0*
*Last Updated: 2025-01-20*

**Note**: This documentation reflects the current state of the HFE Pose Analysis System. For the most up-to-date information, please refer to the source code and configuration files.
