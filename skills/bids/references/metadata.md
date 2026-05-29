# BIDS Metadata Reference — JSON Sidecar Fields

## MRI — Anatomical (anat/)

### Required
*(No fields strictly required for anat in BIDS 1.x, but these are highly recommended)*

### Recommended
| Field | Type | Example |
|-------|------|---------|
| `MagneticFieldStrength` | number | `3.0` |
| `Manufacturer` | string | `"Siemens"` |
| `ManufacturersModelName` | string | `"Prisma"` |
| `DeviceSerialNumber` | string | `"ABC123"` |
| `StationName` | string | `"SCANNER1"` |
| `SoftwareVersions` | string | `"syngo MR E11"` |
| `HardcopyDeviceSoftwareVersion` | string | — |
| `ReceiveCoilName` | string | `"HeadNeck_64"` |
| `ReceiveCoilActiveElements` | string | `"HEA;HEP"` |
| `RepetitionTime` | number | `2.3` (seconds) |
| `EchoTime` | number | `0.005` (seconds) |
| `InversionTime` | number | `0.9` (seconds) |
| `FlipAngle` | number | `9` (degrees) |
| `PartialFourier` | number | `0.75` |
| `PartialFourierDirection` | string | `"PHASE"` |
| `MultibandAccelerationFactor` | integer | `2` |
| `ParallelReductionFactorInPlane` | number | `2.0` |
| `PixelBandwidth` | number | `180` (Hz/pixel) |
| `PhaseEncodingDirection` | string | `"j"`, `"j-"`, `"i"`, `"i-"` |
| `EffectiveEchoSpacing` | number | `0.00059` (seconds) |
| `TotalReadoutTime` | number | `0.047` (seconds) |
| `SliceTiming` | array | `[0, 0.5, 1.0, ...]` |
| `NumberOfSlices` | integer | `64` |
| `NonlinearGradientCorrection` | boolean | `true` |
| `ImageOrientationPatientDICOM` | array | — |

---

## MRI — Functional BOLD (func/)

### Required
| Field | Type | Example |
|-------|------|---------|
| `RepetitionTime` | number | `2.0` (seconds) |
| `TaskName` | string | `"rest"`, `"nback"`, `"facerecognition"` |

### Required (if echo entity)
| Field | Type | Example |
|-------|------|---------|
| `EchoTime` | number | `0.03` (seconds) |

### Recommended (all MRI fields apply +)
| Field | Type | Example |
|-------|------|---------|
| `SliceTiming` | array | `[0, 0.065, 0.13, ...]` |
| `PhaseEncodingDirection` | string | `"j-"` |
| `EffectiveEchoSpacing` | number | `0.000590` |
| `TotalReadoutTime` | number | `0.047` |
| `TaskDescription` | string | `"Resting state with eyes open"` |
| `Instructions` | string | `"Keep eyes open and focus on the cross"` |
| `CogAtlasID` | string | — |
| `CogPOID` | string | — |
| `NumberOfVolumesDiscardedByScanner` | integer | `4` |
| `NumberOfVolumesDiscardedByUser` | integer | `0` |
| `DelayTime` | number | `0` |
| `AcquisitionDuration` | number | `600` (seconds) |

---

## MRI — Diffusion (dwi/)

### Required
| Field | Type | Example |
|-------|------|---------|
*(JSON sidecar required; b-values in `.bval`, gradients in `.bvec`)*

### Recommended
| Field | Type | Example |
|-------|------|---------|
| `PhaseEncodingDirection` | string | `"j-"` |
| `EffectiveEchoSpacing` | number | `0.000590` |
| `TotalReadoutTime` | number | `0.0474` |
| `EchoTime` | number | `0.092` |
| `RepetitionTime` | number | `8.4` |
| `NumberOfVolumesDiscardedByScanner` | integer | `0` |
| `MultibandAccelerationFactor` | integer | `2` |
| `ParallelReductionFactorInPlane` | number | `2` |

---

## MRI — Field Maps (fmap/)

### For phasediff (EchoTime pair)
| Field | Type | Required |
|-------|------|----------|
| `EchoTime1` | number | **Yes** |
| `EchoTime2` | number | **Yes** |
| `IntendedFor` | string/array | Recommended — path(s) relative to dataset root |

Example:
```json
{
  "EchoTime1": 0.00492,
  "EchoTime2": 0.00738,
  "IntendedFor": [
    "ses-01/func/sub-01_ses-01_task-rest_bold.nii.gz"
  ]
}
```

### For EPI field maps
| Field | Type | Required |
|-------|------|----------|
| `PhaseEncodingDirection` | string | **Yes** |
| `TotalReadoutTime` | number | **Yes** |
| `IntendedFor` | string/array | Recommended |

```json
{
  "PhaseEncodingDirection": "j",
  "TotalReadoutTime": 0.0474,
  "IntendedFor": "func/sub-01_task-rest_bold.nii.gz"
}
```

---

## EEG — `*_eeg.json`

### Required
| Field | Type | Example |
|-------|------|---------|
| `SamplingFrequency` | number | `2400` (Hz) |
| `PowerLineFrequency` | number | `50` or `60` (Hz) |

### Recommended
| Field | Type | Example |
|-------|------|---------|
| `TaskName` | string | `"rest"` |
| `TaskDescription` | string | `"5-minute resting state, eyes open"` |
| `Instructions` | string | `"Look at fixation cross"` |
| `EEGReference` | string | `"Cz"`, `"average"`, `"linked mastoids"` |
| `EEGGround` | string | `"AFz"` |
| `EEGChannelCount` | integer | `64` |
| `EOGChannelCount` | integer | `4` |
| `ECGChannelCount` | integer | `1` |
| `EMGChannelCount` | integer | `0` |
| `MiscChannelCount` | integer | `0` |
| `TriggerChannelCount` | integer | `1` |
| `RecordingDuration` | number | `300` (seconds) |
| `RecordingType` | string | `"continuous"` or `"epoched"` |
| `EpochLength` | number | `2.0` (seconds, if epoched) |
| `SubjectArtefactDescription` | string | `"Chewing artifact on channels FC1-FC2"` |
| `SoftwareFilters` | object | `{"Anti-aliasing filter": {"half-amplitude cutoff (Hz)": 500}}` |
| `HardwareFilters` | object | `{"ADC's decimation filter (hardware bandwidth limit)": {"Cutoff (Hz)": 0}}` |
| `Manufacturer` | string | `"Brain Products"` |
| `ManufacturersModelName` | string | `"actiCHamp Plus"` |
| `DeviceSerialNumber` | string | `"ABC123"` |
| `CapManufacturer` | string | `"EasyCap"` |
| `CapManufacturersModelName` | string | `"M10"` |
| `EEGPlacementScheme` | string | `"10-20"` |
| `CRLFChannelCount` | integer | `0` |

### channels.tsv required columns (EEG)
| Column | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Channel name, e.g. `Fp1` |
| `type` | Yes | `EEG`, `EOG`, `ECG`, `EMG`, `MISC`, `STIM`, `TRIG`, `HEOG`, `VEOG` |
| `units` | Yes | `µV`, `mV`, `V` |
| `sampling_frequency` | Recommended | Sampling rate in Hz |
| `low_cutoff` | Recommended | High-pass filter in Hz |
| `high_cutoff` | Recommended | Low-pass filter in Hz |
| `notch` | Recommended | Notch filter frequency |
| `reference` | Recommended | Reference electrode name |
| `description` | Optional | Free-text channel description |
| `status` | Optional | `good` or `bad` |
| `status_description` | Optional | Reason for bad status |

---

## MEG — `*_meg.json`

### Required
| Field | Type | Example |
|-------|------|---------|
| `SamplingFrequency` | number | `600` (Hz) |

### Required (if applicable)
| Field | Type | Example |
|-------|------|---------|
| `PowerLineFrequency` | number | `50` or `60` |
| `DewarPosition` | string | `"upright"` or `"supine"` |
| `DigitizedLandmarks` | boolean | `true` |
| `DigitizedHeadPoints` | boolean | `true` |

### Recommended
| Field | Type | Example |
|-------|------|---------|
| `MEGChannelCount` | integer | `248` |
| `MEGREFChannelCount` | integer | `23` |
| `EEGChannelCount` | integer | `0` |
| `EOGChannelCount` | integer | `2` |
| `ECGChannelCount` | integer | `1` |
| `EMGChannelCount` | integer | `0` |
| `RecordingDuration` | number | `1200` |
| `RecordingType` | string | `"continuous"` |
| `ContinuousHeadLocalization` | boolean | `false` |
| `HeadCoilFrequency` | array | `[293, 307, 314]` |
| `MaxMovement` | number | `0.5` (mm) |
| `TaskName` | string | `"rest"` |
| `Manufacturer` | string | `"Elekta"` |
| `ManufacturersModelName` | string | `"Neuromag-122"` |
| `SoftwareVersions` | string | `"MaxFilter 2.2.15"` |
| `SoftwareFilters` | object | — |

### coordsystem.json required fields (MEG)
```json
{
  "MEGCoordinateSystem": "ElektaNeuromag",
  "MEGCoordinateUnits": "m",
  "MEGCoordinateSystemDescription": "RAS with origin at ear canal midpoint",
  "HeadCoilCoordinates": {
    "NAS": [0.003, 0.08, 0.012],
    "LPA": [-0.074, 0.0, -0.021],
    "RPA": [0.07, 0.0, -0.021]
  },
  "HeadCoilCoordinateUnits": "m",
  "HeadCoilCoordinateSystem": "CTF"
}
```

---

## iEEG — `*_ieeg.json`

### Required
| Field | Type | Example |
|-------|------|---------|
| `SamplingFrequency` | number | `30000` (Hz) |
| `PowerLineFrequency` | number | `60` (Hz) |

### Recommended
| Field | Type | Example |
|-------|------|---------|
| `iEEGReference` | string | `"intracranial"`, `"mastoid"` |
| `iEEGChannelCount` | integer | `96` |
| `ECOGChannelCount` | integer | `64` |
| `SEEGChannelCount` | integer | `32` |
| `DCSChannelCount` | integer | `0` |
| `EEGChannelCount` | integer | `0` |
| `EOGChannelCount` | integer | `0` |
| `ECGChannelCount` | integer | `1` |
| `EMGChannelCount` | integer | `0` |
| `MiscChannelCount` | integer | `0` |
| `TriggerChannelCount` | integer | `2` |
| `RecordingDuration` | number | `3600` |
| `RecordingType` | string | `"continuous"` |
| `ElectrodeManufacturer` | string | `"AdTech"` |
| `ElectrodeManufacturersModelName` | string | `"64-channel HD ECoG"` |
| `Manufacturer` | string | `"Blackrock Neurotech"` |
| `ManufacturersModelName` | string | `"Neuroport"` |
| `SubjectArtefactDescription` | string | — |

### electrodes.tsv required columns
| Column | Required |
|--------|----------|
| `name` | Yes |
| `x` | Yes |
| `y` | Yes |
| `z` | Yes |
| `size` | Recommended |
| `material` | Recommended |
| `manufacturer` | Recommended |
| `group` | Recommended |
| `hemisphere` | Recommended |
| `type` | Recommended (`seeg`, `ecog`, `dbs`) |

---

## PET — `*_pet.json`

### Required
| Field | Type | Example |
|-------|------|---------|
| `Manufacturer` | string | `"Siemens"` |
| `ManufacturersModelName` | string | `"Biograph mMR"` |
| `BodyPart` | string | `"Brain"` |
| `TracerName` | string | `"[11C]raclopride"` |
| `TracerRadionuclide` | string | `"C11"` |
| `InjectedRadioactivity` | number | `200` (MBq) |
| `InjectedRadioactivityUnits` | string | `"MBq"` |
| `InjectedMass` | number | `0.5` |
| `InjectedMassUnits` | string | `"nmol"` |
| `SpecificRadioactivity` | number | — |
| `SpecificRadioactivityUnits` | string | — |
| `TimeZero` | string | `"13:00:00"` (HH:MM:SS) |
| `ScanStart` | number | `0` (seconds since TimeZero) |
| `InjectionStart` | number | `-30` (seconds since TimeZero) |
| `FrameTimesStart` | array | `[0, 10, 20, ...]` (seconds) |
| `FrameDuration` | array | `[10, 10, 20, ...]` (seconds) |
| `AcquisitionMode` | string | `"list mode"`, `"dynamic"`, `"static"` |
| `ImageDecayCorrected` | boolean | `true` |
| `ImageDecayCorrectionTime` | number | `0` |
| `ReconMethodName` | string | `"OSEM 3D"` |
| `ReconMethodParameterLabels` | array | `["iterations", "subsets"]` |
| `ReconMethodParameterValues` | array | `[4, 21]` |
| `ReconFilterType` | string | `"Gaussian"` |
| `ReconFilterSize` | number | `5` (mm FWHM) |
| `AttenuationCorrection` | string | `"MR-based attenuation correction"` |

---

## Events.tsv

### Required columns
| Column | Type | Description |
|--------|------|-------------|
| `onset` | number | Start time in seconds from scan start |
| `duration` | number | Duration in seconds (`n/a` if unknown) |

### Recommended columns
| Column | Type | Description |
|--------|------|-------------|
| `trial_type` | string | Category of event |
| `response_time` | number | Reaction time in seconds |
| `stim_file` | string | Relative path to stimulus file |
| `value` | number/string | Event marker value |
| `HED` | string | HED tag annotation |

Example:
```tsv
onset	duration	trial_type	response_time	correct
1.500	2.000	face	0.823	1
3.800	2.000	house	0.741	0
6.200	2.000	scrambled	n/a	n/a
```

### events.json (column descriptions)
```json
{
  "onset": {"Description": "Stimulus onset in seconds from start of acquisition"},
  "duration": {"Description": "Stimulus duration in seconds"},
  "trial_type": {
    "Description": "Category of stimulus",
    "Levels": {
      "face": "Human face photograph",
      "house": "House photograph",
      "scrambled": "Phase-scrambled image"
    }
  },
  "response_time": {
    "Description": "Reaction time in seconds from stimulus onset",
    "Units": "s"
  },
  "correct": {
    "Description": "Whether response was correct",
    "Levels": {"0": "incorrect", "1": "correct"}
  }
}
```

---

## scans.tsv

```tsv
filename	acq_time
anat/sub-01_T1w.nii.gz	2020-06-15T10:23:45
func/sub-01_task-rest_bold.nii.gz	2020-06-15T10:25:12
eeg/sub-01_task-rest_eeg.edf	2020-06-15T11:00:00
```

Use ISO 8601 format for `acq_time`. Use `n/a` when time is unknown.
Must be located at `sub-<label>/scans.tsv` or `sub-<label>/ses-<label>/scans.tsv`.
