---
name: pupil-labs-neon-realtime
description: Connect to Pupil Labs Neon eye-tracking glasses and collect real-time data streams (video, gaze, IMU, events). Use when working with Neon hardware via the Real-time API for live data visualization, data collection, or eye-tracking applications requiring device discovery, multi-threaded streaming, or hardware troubleshooting.
---

# Pupil Labs Neon Real-time Development

Connect to Pupil Labs Neon eye-tracking glasses and implement multi-threaded real-time data collection.

## Environment Setup

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Run scripts
uv run python neon_video_viewer.py
uv run python neon_realtime_monitor.py
```

### Dependencies

Required packages (Python 3.11+):
```toml
pupil-labs-realtime-api>=1.7.3  # Neon device communication
opencv-python>=4.12.0.88         # Video display
matplotlib>=3.10.7               # Plotting (use Agg backend)
numpy                            # Array operations
```

For manual pip install:
```bash
pip install pupil-labs-realtime-api opencv-python matplotlib numpy
```

## Device Connection

### Discovery Pattern

Auto-discover device on local network (no manual IP needed):

```python
from pupil_labs.realtime_api.simple import discover_one_device

device = discover_one_device(max_search_duration_seconds=10)
if device is None:
    print("No device found.")
    return

print(f"Connected: {device.serial_number_glasses}")
print(f"Phone: {device.phone_name} @ {device.phone_ip}")
```

### Prerequisites Checklist

Before running any script:
1. **Network setup**: 
   - Create a WiFi hotspot on your computer
   - Connect the Neon Companion phone to this hotspot
   - Both devices must be on the same network for discovery to work
2. **Neon Companion app must be running** on paired phone
3. **Feature enablement** (in Companion app settings):
   - Enable "Compute eye state" for eyelid aperture data
   - Enable "Compute fixations" for eye event detection

### Connection Troubleshooting

**10-second timeout with no output**: Check network connectivity and Companion app status.

**Device found but data streams empty**: Feature not enabled in Companion app (not API-configurable).

**Intermittent disconnects**: Use `try/except TimeoutError` on all receive methods.

## Multi-threaded Data Collection

**Why threading is required**: All `receive_*()` methods block until data arrives or timeout expires. Single-threaded code would miss data from other streams while waiting. Threading enables parallel collection from multiple streams without blocking.

### Thread Architecture Pattern

Create dedicated thread per data stream with priority-based sleep strategy:

```python
def data_collection_thread(self, data_type):
    """Separate thread per data type."""
    while self.running:
        try:
            if data_type == 'video':
                self.receive_video()
                # NO sleep - maximum FPS (highest priority)
            elif data_type == 'gaze':
                self.receive_gaze()
                time.sleep(0.01)  # 10ms - yield CPU
            elif data_type == 'events':
                self.receive_events()
                time.sleep(0.01)  # 10ms
            elif data_type == 'imu':
                self.receive_imu()
                time.sleep(0.005)  # 5ms - higher frequency than gaze
        except Exception as e:
            if self.running:
                print(f"Error in {data_type}: {e}")
            time.sleep(0.001)

# Start as daemon threads (exit when main program exits)
thread = threading.Thread(target=self.data_collection_thread, 
                         args=('video',), daemon=True)
thread.start()
```

**Critical sleep strategy**:
- **Video: NO sleep** - Maximize frame rate, highest priority
- **IMU: 5ms sleep** - Higher frequency motion data
- **Gaze/Events: 10ms sleep** - Lower priority, yield CPU
- **Rationale**: Video frames are time-critical; other data can tolerate slight delays

### Thread-Safe Data Access

Always use locks when sharing data between collection and rendering threads:

```python
self.data_lock = threading.Lock()

# Collection thread
with self.data_lock:
    self.latest_frame = frame.copy()

# Rendering thread
with self.data_lock:
    if self.latest_frame is not None:
        display = self.latest_frame.copy()
```

### Starting Threads

Start video threads first with priority, allow initialization, then start data threads:

```python
# Create threads
video_thread = threading.Thread(target=self.data_collection_thread, 
                                args=('video',), daemon=True)
gaze_thread = threading.Thread(target=self.data_collection_thread,
                               args=('gaze',), daemon=True)
imu_thread = threading.Thread(target=self.data_collection_thread,
                              args=('imu',), daemon=True)

# Start video first (highest priority)
video_thread.start()
time.sleep(0.1)  # Let video thread initialize

# Then start data collection threads
gaze_thread.start()
imu_thread.start()
```

**Why this order matters**: Video initialization can be slow; starting it first prevents other threads from overwhelming the system during startup.

## Data Stream APIs

### Scene Video

```python
frame_data = device.receive_scene_video_frame(timeout_seconds=0.0001)
if frame_data:
    frame = frame_data.bgr_pixels  # OpenCV-ready BGR numpy array
```

### Gaze Data

Returns different classes based on Companion app settings:

```python
gaze = device.receive_gaze_datum(timeout_seconds=0.001)

# Always available
x, y = gaze.x, gaze.y  # Pixel coordinates
worn = gaze.worn  # Boolean

# With "Compute eye state" enabled
if hasattr(gaze, 'eyelid_aperture_left'):
    # Aperture range: 0-10mm, normalize to 0-1
    openness = min(1.0, gaze.eyelid_aperture_left / 10.0)
```

### Eye Events

Requires "Compute fixations" enabled:

```python
event = device.receive_eye_events(timeout_seconds=0.001)

if hasattr(event, 'event_type'):
    if event.event_type == 4:  # Blink
        duration = (event.end_time_ns - event.start_time_ns) / 1e9
    elif event.event_type == 0:  # Saccade
        amplitude = event.amplitude_angle_deg
    elif event.event_type == 1:  # Fixation
        duration = (event.end_time_ns - event.start_time_ns) / 1e9
```

### IMU Data

```python
imu = device.receive_imu_datum(timeout_seconds=0.001)

# Accelerometer (linear motion) in g
accel_x = imu.accel_data.x
accel_y = imu.accel_data.y
accel_z = imu.accel_data.z

# Gyroscope (rotational motion) in rad/s
gyro_x = imu.gyro_data.x
gyro_y = imu.gyro_data.y
gyro_z = imu.gyro_data.z

# Orientation quaternion (w, x, y, z)
quaternion = imu.quaternion
```

### Matched Video + Gaze

Get temporally synchronized frame and gaze:

```python
matched = device.receive_matched_scene_video_frame_and_gaze()
frame = matched.frame.bgr_pixels
gaze = matched.gaze
```

## Timeout Strategy

All receive methods accept `timeout_seconds`:
- **0.0001**: Non-blocking check (video threads)
- **0.001**: Fast check (1ms for data threads)
- **None/omitted**: Blocks indefinitely (avoid in threaded code)

Always wrap in try/except:

```python
try:
    data = device.receive_gaze_datum(timeout_seconds=0.001)
except TimeoutError:
    pass  # No data available yet
```

## Graceful Shutdown

```python
self.running = False
time.sleep(0.5)  # Let threads finish current operations
device.close()
```

## Common Pitfalls

1. **Feature enablement**: Data streams depend on Companion app settings, not API configuration
2. **No sleep in video threads**: Causes dropped frames if video processing blocks
3. **Missing locks**: Race conditions when multiple threads access shared data
4. **Infinite blocking**: Always use timeout_seconds in threaded code
5. **Runtime data types**: Check `hasattr()` for optional attributes (eyelid, event details)

## Reference Scripts

Two complete working implementations provided:

**[scripts/neon_video_viewer.py](scripts/neon_video_viewer.py)** - Minimal starter (100 lines)
- Simple device connection
- Matched video + gaze streaming
- OpenCV gaze overlay (circle + crosshair)
- Single-threaded, easy to understand

**[scripts/neon_realtime_monitor.py](scripts/neon_realtime_monitor.py)** - Full dashboard (750 lines)
- Multi-threaded architecture
- All data streams (video, gaze, events, IMU)
- Matplotlib plots with OpenCV integration
- 3D head rotation visualization
- Production-ready error handling

Run directly or use as templates for custom applications.
