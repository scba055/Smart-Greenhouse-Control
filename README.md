# Smart Greenhouse Control
### Machine Learning-Assisted Hydroponic pH Regulation

A mechatronics engineering capstone project exploring the integration of embedded systems, IoT-based environmental monitoring, automated pH dosing, machine learning, and evolutionary optimisation in a controlled hydroponic greenhouse.

The project combines Raspberry Pi and Arduino-based hardware with a Python data-processing pipeline, a Random Forest regression model, and a Genetic Algorithm (GA) to investigate how historical greenhouse data can support improved automated pH regulation.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Hardware](#hardware)
- [Technology Stack](#technology-stack)
- [Data Collection and Processing](#data-collection-and-processing)
- [Machine Learning](#machine-learning-random-forest-regression)
- [Genetic Algorithm Optimisation](#genetic-algorithm-controller-optimisation)
- [Automated pH Regulation](#automated-ph-regulation)
- [Results](#results-and-key-findings)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [Skills Demonstrated](#skills-demonstrated)
- [Project Context](#project-context-and-attribution)

## Overview

Hydroponic systems require careful management of nutrient solution chemistry to maintain suitable growing conditions. Changes in pH can affect nutrient availability, while environmental conditions and previous dosing events influence reservoir behaviour.

Conventional threshold-based controllers react to current sensor readings using manually configured operating limits and dosing intervals. This project investigates whether historical operational data can be used to develop predictive models and optimise controller parameters, reducing reliance on manually selected thresholds.

### Project Objectives

- Monitor hydroponic reservoir conditions and greenhouse environmental variables using connected sensors.
- Collect and process historical operational data for machine learning.
- Develop a Random Forest model to predict future reservoir pH.
- Implement a Genetic Algorithm to optimise pH trigger thresholds and dosing cooldown intervals.
- Integrate optimised controller parameters into the existing automated dosing system.

## System Architecture

The project integrates physical sensing, embedded hardware, data acquisition, predictive modelling, optimisation, and automated actuation.

```text
Hydroponic Greenhouse
        |
        v
Environmental and Water Sensors
        |
        v
Arduino / Seeeduino XIAO
        |
        v
Raspberry Pi 4B
        |
        +--------------------------+
        |                          |
        v                          v
Sensor Data Logging         Python Data Processing
        |                          |
        v                          v
Google Sheets / CSV         Random Forest Model
                                   |
                                   v
                           Genetic Algorithm
                                   |
                                   v
                         Optimised Parameters
                            (JSON via Git)
                                   |
                                   v
                         Raspberry Pi Controller
                                   |
                                   v
                         MOSFET Driver and Pumps
                                   |
                                   v
                          Reservoir pH Regulation
```

*This is a simplified representation of the project architecture. The Random Forest predictions support the optimisation process, while the deployed real-time controller uses the resulting optimised parameters to determine when corrective dosing occurs.*

## Hardware

| Component | Purpose |
|---|---|
| Raspberry Pi 4B | Main computing platform, data processing, logging, and controller execution |
| Arduino Uno | Additional pH sensing along the water flow path |
| Seeeduino XIAO | Sensor interfacing and environmental data acquisition |
| DFRobot pH Sensor V1.1 | Reservoir pH measurement |
| Additional pH sensor | Monitoring pH in the water flow path towards the plants |
| SCD30 CO₂ sensor | Carbon dioxide monitoring |
| Temperature and humidity sensors | Environmental monitoring |
| Light sensor | Light condition monitoring |
| Peristaltic dosing pumps | Dispensing pH adjustment solutions |
| MOSFET driver board | Switching the dosing pumps |

The hardware combines low-cost microcontrollers with a Raspberry Pi to support greenhouse monitoring and automated actuation. Multiple pH measurement points allow reservoir conditions to be compared with conditions in the water flowing towards the plants.

## Technology Stack

- **Languages:** Python, Arduino/C++
- **Data processing:** Pandas, NumPy
- **Machine learning:** scikit-learn, Random Forest Regression
- **Optimisation:** Genetic Algorithm
- **Hardware:** Raspberry Pi, Arduino Uno, Seeeduino XIAO
- **Communication:** Serial communication
- **Data storage:** Google Sheets and local CSV files
- **Configuration and deployment:** JSON configuration files and Git

## Data Collection and Processing

Before introducing machine learning-assisted optimisation, the greenhouse operated under conventional rule-based control to establish a historical dataset.

### Dataset Summary

| Parameter | Value |
|---|---|
| Collection period | 1 April – 7 May 2026 |
| Collection duration | Approximately five weeks |
| Sampling interval | 10 minutes |
| Raw samples collected | 4,878 |
| Processed dataset entries | 2,640 |
| Primary storage platform | Google Sheets |
| Offline storage | Local CSV backup |

The Raspberry Pi received sensor data from the microcontroller, parsed incoming measurements, and logged them to Google Sheets when an internet connection was available. During connectivity interruptions, readings were retained locally for subsequent upload.

The data-processing pipeline prepared collected observations for analysis and model training. Processing included:

- Removing invalid or missing measurements.
- Standardising timestamp formats.
- Sorting observations chronologically.
- Preparing features associated with environmental conditions and dosing events.
- Engineering temporal features to represent recent pH behaviour.

Features used by the Random Forest model included:

- Electrical conductivity (EC).
- CO₂ concentration.
- Air temperature.
- Humidity.
- Time since the previous dose.
- Dosing direction.
- Historical pH information in the enhanced feature set.

This pipeline transformed operational greenhouse measurements into a dataset suitable for predictive modelling and controller optimisation.

## Machine Learning: Random Forest Regression

A Random Forest regression model was developed to estimate future reservoir pH from historical greenhouse observations.

The model uses an ensemble of decision trees to learn relationships between environmental conditions, nutrient solution measurements, and dosing activity. Its purpose was to estimate future pH behaviour rather than relying exclusively on instantaneous sensor readings.

### Model Configuration

- Algorithm: Random Forest Regressor.
- Number of trees: 100.
- Random seed: 42.
- Evaluation method: Held-out test subset.
- Target variable: Future reservoir pH.

### Model Evaluation

The final model evaluation reported the following metrics:

| Metric | Result |
|---|---:|
| R² | 0.9552 |
| Mean Absolute Error (MAE) | 0.0427 |
| Root Mean Squared Error (RMSE) | 0.0752 |

### Feature Engineering Comparison

Including temporal pH information improved the reported predictive performance.

| Feature set | R² | MAE | RMSE |
|---|---:|---:|---:|
| Environmental and dosing features | 0.8122 | 0.0625 | 0.0934 |
| Environmental, dosing, and temporal pH features | 0.9552 | 0.0427 | 0.0752 |

These results suggest that recent reservoir behaviour provides useful information for predicting future pH.

However, predictive accuracy alone does not establish that an automated controller will perform better under every operating condition. Further validation using time-based splits and independent operational data would help establish how well the model generalises.

## Genetic Algorithm: Controller Optimisation

A Genetic Algorithm was implemented to identify suitable parameters for the automated pH controller.

Rather than relying exclusively on manually selected trigger thresholds and cooldown intervals, the optimisation process evaluated candidate controller configurations using a fitness function designed to favour desirable control behaviour.

The parameters included:

- **Lower pH trigger:** The lower operating threshold for corrective dosing.
- **Upper pH trigger:** The upper operating threshold for corrective dosing.
- **Cooldown interval:** The minimum waiting period between permitted dosing actions.

The GA used evolutionary operations, including parent selection, crossover, mutation, and elitism, to explore candidate parameter combinations across successive generations.

### Optimisation Workflow

1. Load the processed greenhouse dataset.
2. Train the Random Forest model.
3. Generate pH predictions for the optimisation process.
4. Evaluate candidate controller configurations using the GA fitness function.
5. Evolve candidate configurations over successive generations.
6. Export the selected thresholds and cooldown interval to `ga_params.json`.
7. Make the updated configuration available to the Raspberry Pi through Git.

This approach allows controller parameters to be updated through an offline optimisation workflow without manually rewriting the real-time control logic for each configuration.

## Automated pH Regulation

The real-time controller monitors reservoir pH and applies corrective dosing when configured operating limits are exceeded and the cooldown requirement has elapsed.

The system uses two dosing solutions:

- **pH Up:** Sodium hydroxide (NaOH).
- **pH Down:** Hydrochloric acid (HCl).

The Raspberry Pi controls the appropriate dosing pump through a MOSFET driver board. Cooldown logic helps prevent repeated dosing actions from occurring too frequently.

The original rule-based controller used manually configured thresholds. The GA-assisted configuration replaces these manually selected parameters with values obtained through the optimisation process.

The project's research focus was pH regulation. Although electrical conductivity was monitored and included in the predictive model, automated EC and nutrient-concentration regulation were not fully implemented.

## Results and Key Findings

The project demonstrated the feasibility of combining historical greenhouse data, predictive modelling, and evolutionary optimisation within an automated hydroponic system.

Key findings included:

- A processed dataset of 2,640 observations was obtained from approximately five weeks of greenhouse operation.
- The Random Forest model achieved a reported R² of 0.9552, with an MAE of 0.0427 and RMSE of 0.0752.
- Incorporating temporal pH features improved the reported R² from 0.8122 to 0.9552.
- The Genetic Algorithm identified candidate lower and upper pH thresholds and cooldown intervals through iterative optimisation.
- Optimised controller parameters could be exported and deployed separately from the main real-time control code.
- Local data backup provided a mechanism for retaining sensor observations during internet connectivity interruptions.

These results demonstrate the potential of using historical operational data to support more adaptive greenhouse control systems. Further controlled experiments would be required to quantify improvements in real-world pH stability relative to the original controller.

## Limitations

Several limitations provide opportunities for further engineering development:

- The historical dataset covered approximately five weeks of operation and may not represent all greenhouse conditions.
- Sensor calibration, measurement noise, and differences between reservoir and flow-path pH readings can affect data quality.
- The Random Forest's predictive performance does not guarantee improved physical control performance.
- The GA's effectiveness depends on its fitness function, search space, and optimisation settings.
- The current controller uses GA-optimised thresholds but does not directly use Random Forest predictions to determine each real-time dosing action.
- EC is monitored but is not automatically regulated through dedicated nutrient dosing.
- Additional testing is needed to assess long-term stability, dosing efficiency, and plant growth outcomes.

## Future Improvements

Potential extensions include:

- Implementing predictive control in which future pH estimates directly influence dosing decisions.
- Expanding the dataset and evaluating the model using time-based validation.
- Adding automated EC regulation and nutrient A/B dosing.
- Improving sensor calibration, fault detection, and communication recovery.
- Introducing a relational database such as PostgreSQL for structured sensor telemetry and dosing-event storage.
- Developing automated performance monitoring for model accuracy and controller stability.
- Comparing rule-based and GA-optimised control using consistent metrics, such as time within the target pH range, pH variability, overshoot frequency, and dosing frequency.

## Skills Demonstrated

- Embedded systems integration.
- Sensor data acquisition and processing.
- Python development.
- Machine learning and regression modelling.
- Feature engineering and model evaluation.
- Evolutionary optimisation.
- Automated control systems.
- Serial communication and hardware troubleshooting.
- Data logging and connectivity resilience.
- Configuration management and deployment workflows.

## Project Context and Attribution

This repository showcases software and engineering work associated with a mechatronics engineering capstone project at Auckland University of Technology (AUT).

I was responsible for developing the machine learning components and automation systems, modifying the existing database to meet my project’s requirements, and testing individual components to identify and troubleshoot faults. The remaining components were developed by Matthew and Jackson.

The project was developed in an academic team setting. The original repository is private, hence why it is not linked here.

## Disclaimer

This project is an academic prototype and research investigation. It is not a validated commercial agricultural control system. Any physical deployment should include appropriate sensor calibration, dosing safeguards, and independent verification of controller behaviour.
