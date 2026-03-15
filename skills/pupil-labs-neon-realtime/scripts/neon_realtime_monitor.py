"""
Pupil Labs Neon - Comprehensive Real-time Monitor
==================================================
Shows all real-time data from Neon glasses:
- Scene video with gaze overlay
- Time series: Eyelid openness (30s window)
- Time series: Eye events (fixations, saccades, blinks) with duration visualization
- Time series: IMU data (accelerometer, gyroscope)
- 3D visualization: Head orientation from quaternion with motion vectors
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_agg import FigureCanvasAgg
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
from datetime import datetime, timedelta
import time
import threading
from pupil_labs.realtime_api.simple import discover_one_device


class NeonRealtimeMonitor:
    def __init__(self, time_window=30):
        """Initialize the real-time monitor."""
        self.device = None
        self.time_window = time_window  # seconds
        
        # Data storage
        self.eyelid_times = deque()
        self.eyelid_left = deque()
        self.eyelid_right = deque()
        
        self.events = []  # List of (start_time, end_time, event_type, details)
        
        # IMU data storage
        self.imu_times = deque()
        self.accel_x = deque()
        self.accel_y = deque()
        self.accel_z = deque()
        self.gyro_x = deque()
        self.gyro_y = deque()
        self.gyro_z = deque()
        self.quaternion_data = None  # Latest quaternion for 3D head viz
        
        # Latest video frame
        self.latest_frame = None
        self.latest_gaze = None
        self.latest_eye_frame = None  # For eye camera
        self.display_frame = None  # Cached display frame with overlays
        self.frame_count = 0
        
        # Threading locks
        self.data_lock = threading.Lock()
        
        # Setup matplotlib figure (using Agg backend) - compact size to fit screen
        self.fig = plt.figure(figsize=(10, 9))
        gs = self.fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, 1], width_ratios=[2, 2, 1], 
                                   hspace=0.3, wspace=0.25)
        
        # Create subplots
        self.ax_eyelid = self.fig.add_subplot(gs[0, 0:2])  # Top left, spans 2 columns
        self.ax_events = self.fig.add_subplot(gs[1, 0:2])  # Second row left, spans 2 columns
        self.ax_accel = self.fig.add_subplot(gs[2, 0:2])   # Third row left, spans 2 columns
        self.ax_gyro = self.fig.add_subplot(gs[3, 0:2])    # Bottom left, spans 2 columns
        self.ax_3d_rotation = self.fig.add_subplot(gs[:, 2], projection='3d')  # Right side - head rotation
        
        # Setup eyelid plot
        self.ax_eyelid.set_xlim(0, time_window)
        self.ax_eyelid.set_ylim(0, 1.1)
        self.ax_eyelid.set_xlabel('Time (seconds)', fontsize=8)
        self.ax_eyelid.set_ylabel('Eyelid Openness', fontsize=8)
        self.ax_eyelid.set_title('Eyelid Openness (0=closed, 1=open)', fontsize=10, fontweight='bold')
        self.ax_eyelid.grid(True, alpha=0.3)
        
        self.line_left, = self.ax_eyelid.plot([], [], 'b-', linewidth=1.5, label='Left Eye')
        self.line_right, = self.ax_eyelid.plot([], [], 'r-', linewidth=1.5, label='Right Eye')
        self.ax_eyelid.legend(loc='upper right', fontsize=7)
        
        # Setup events plot
        self.ax_events.set_xlim(0, time_window)
        self.ax_events.set_ylim(-0.5, 2.5)
        self.ax_events.set_xlabel('Time (seconds)', fontsize=8)
        self.ax_events.set_ylabel('Event Type', fontsize=8)
        self.ax_events.set_title('Eye Events (Real-time)', fontsize=10, fontweight='bold')
        self.ax_events.set_yticks([0, 1, 2])
        self.ax_events.set_yticklabels(['Blinks', 'Saccades', 'Fixations'], fontsize=7)
        self.ax_events.grid(True, alpha=0.3, axis='x')
        
        # Setup Accelerometer plot (will auto-scale)
        self.ax_accel.set_xlim(0, time_window)
        self.ax_accel.set_xlabel('Time (seconds)', fontsize=8)
        self.ax_accel.set_ylabel('Acceleration (g)', fontsize=8)
        self.ax_accel.set_title('Accelerometer (Linear Motion)', fontsize=10, fontweight='bold')
        self.ax_accel.grid(True, alpha=0.3)
        
        self.line_accel_x, = self.ax_accel.plot([], [], 'r-', linewidth=1.5, label='Accel X (Left/Right)', alpha=0.8)
        self.line_accel_y, = self.ax_accel.plot([], [], 'g-', linewidth=1.5, label='Accel Y (Front/Back)', alpha=0.8)
        self.line_accel_z, = self.ax_accel.plot([], [], 'b-', linewidth=1.5, label='Accel Z (Up/Down)', alpha=0.8)
        self.ax_accel.legend(loc='upper right', ncol=3, fontsize=7)
        
        # Setup Gyroscope plot (will auto-scale)
        self.ax_gyro.set_xlim(0, time_window)
        self.ax_gyro.set_xlabel('Time (seconds)', fontsize=8)
        self.ax_gyro.set_ylabel('Angular Velocity (rad/s)', fontsize=8)
        self.ax_gyro.set_title('Gyroscope (Rotational Motion)', fontsize=10, fontweight='bold')
        self.ax_gyro.grid(True, alpha=0.3)
        
        self.line_gyro_x, = self.ax_gyro.plot([], [], 'r--', linewidth=1.5, label='Gyro X (Nod Up/Down)', alpha=0.8)
        self.line_gyro_y, = self.ax_gyro.plot([], [], 'g--', linewidth=1.5, label='Gyro Y (Lean Left/Right)', alpha=0.8)
        self.line_gyro_z, = self.ax_gyro.plot([], [], 'b--', linewidth=1.5, label='Gyro Z (Turn Left/Right)', alpha=0.8)
        self.ax_gyro.legend(loc='upper right', ncol=3, fontsize=7)
        
        # Status text
        self.status_text = self.fig.text(0.02, 0.98, '', fontsize=8, family='monospace', 
                                         verticalalignment='top')
        
        plt.tight_layout()
        
        # Canvas for rendering to image
        self.canvas = FigureCanvasAgg(self.fig)
        
        # Control flags
        self.running = False
        self.start_time = None
        self.eyelid_available = None  # None=unknown, True=available, False=not available
        self.imu_available = None
        
        # Thread objects
        self.threads = []
        
    def data_collection_thread(self, data_type):
        """Separate thread for collecting specific data type."""
        while self.running:
            try:
                if data_type == 'video_gaze':
                    # This gets scene, eye video, and gaze all together - highest priority
                    self.receive_video_and_gaze()
                    # No sleep for video thread - get frames as fast as possible
                elif data_type == 'events':
                    self.receive_events()
                    time.sleep(0.01)  # Lower priority
                elif data_type == 'gaze':
                    self.receive_gaze_data()
                    time.sleep(0.01)  # Lower priority
                elif data_type == 'imu':
                    self.receive_imu_data()
                    time.sleep(0.005)  # Lower priority
            except Exception as e:
                if self.running:
                    print(f"Error in {data_type} thread: {e}")
                time.sleep(0.001)
    
    def video_rendering_thread(self):
        """Separate thread for rendering video with overlays."""
        while self.running:
            try:
                # Check if frame is available and copy it
                frame = None
                gaze = None
                
                with self.data_lock:
                    if self.latest_frame is not None:
                        frame = self.latest_frame.copy()
                        gaze = self.latest_gaze
                
                # If no frame available, wait and continue
                if frame is None:
                    time.sleep(0.001)  # Very short sleep
                    continue
                
                # Draw gaze overlay on scene (simplified for performance)
                if gaze is not None:
                    gaze_x, gaze_y = int(gaze.x), int(gaze.y)
                    
                    # Simple gaze circle (less drawing = faster)
                    cv2.circle(frame, (gaze_x, gaze_y), 20, (0, 0, 255), 2)
                    cv2.circle(frame, (gaze_x, gaze_y), 3, (0, 0, 255), -1)
                
                self.frame_count += 1
                
                # Store processed frame
                with self.data_lock:
                    self.display_frame = frame
                    
            except Exception as e:
                if self.running:
                    print(f"Video rendering error: {e}")
                time.sleep(0.001)
        
    def connect_device(self):
        """Connect to Neon device."""
        print("=" * 70)
        print("Neon Real-time Monitor")
        print("=" * 70)
        print("\nLooking for Neon device...")
        print("(Make sure Neon Companion app is running)")
        print("(Enable 'Compute eye state' and 'Compute fixations' in settings)")
        
        self.device = discover_one_device(max_search_duration_seconds=10)
        
        if self.device is None:
            print("\n❌ No device found.")
            return False
        
        print(f"\n✓ Connected to device: {self.device.serial_number_glasses}")
        print(f"  Phone: {self.device.phone_name}")
        print(f"  IP: {self.device.phone_ip}")
        
        return True
    
    def receive_video_and_gaze(self):
        """Get latest scene video and gaze (called from thread)."""
        try:
            # Use scene video only for maximum performance
            frame_data = self.device.receive_scene_video_frame(timeout_seconds=0.0001)
            if frame_data:
                with self.data_lock:
                    self.latest_frame = frame_data.bgr_pixels.copy()
                        
                # Also try to get gaze
                try:
                    gaze = self.device.receive_gaze_datum(timeout_seconds=0.0001)
                    if gaze:
                        with self.data_lock:
                            self.latest_gaze = gaze
                except:
                    pass
                    
                return True
        except TimeoutError:
            pass
        except Exception as e:
            pass
        return False
    
    def receive_events(self):
        """Get eye events (called from main loop)."""
        try:
            event = self.device.receive_eye_events(timeout_seconds=0.001)
            current_time = time.time() - self.start_time
            
            # Process different event types
            if hasattr(event, 'event_type'):
                with self.data_lock:
                    if event.event_type == 4:  # Blink
                        duration = (event.end_time_ns - event.start_time_ns) / 1e9
                        event_start = current_time - duration
                        self.events.append((event_start, current_time, 'blink', f"{duration:.3f}s"))
                    
                    elif event.event_type == 0:  # Saccade
                        duration = (event.end_time_ns - event.start_time_ns) / 1e9
                        event_start = current_time - duration
                        amplitude = getattr(event, 'amplitude_angle_deg', 0)
                        self.events.append((event_start, current_time, 'saccade', f"{amplitude:.1f}°"))
                    
                    elif event.event_type == 1:  # Fixation
                        duration = (event.end_time_ns - event.start_time_ns) / 1e9
                        event_start = current_time - duration
                        self.events.append((event_start, current_time, 'fixation', f"{duration:.2f}s"))
            return True
        except TimeoutError:
            pass
        except Exception:
            pass
        return False
    
    def receive_gaze_data(self):
        """Get gaze data with eye state (called from main loop)."""
        try:
            gaze = self.device.receive_gaze_datum(timeout_seconds=0.001)
            
            # Skip if gaze is None
            if gaze is None:
                return False
                
            current_time = time.time() - self.start_time
            
            # Check if gaze data includes eyelid information
            # EyestateEyelidGazeData has eyelid_aperture_left/right, not eyelid_left/right
            if hasattr(gaze, 'eyelid_aperture_left') and hasattr(gaze, 'eyelid_aperture_right'):
                if self.eyelid_available is None:
                    self.eyelid_available = True
                    print(f"✓ Eyelid data available (type: {type(gaze).__name__})")
                    
                self.eyelid_times.append(current_time)
                # Normalize aperture to 0-1 range (aperture is typically 0-10mm)
                self.eyelid_left.append(min(1.0, gaze.eyelid_aperture_left / 10.0))
                self.eyelid_right.append(min(1.0, gaze.eyelid_aperture_right / 10.0))
                
                # Remove old data outside time window
                with self.data_lock:
                    while self.eyelid_times and self.eyelid_times[0] < current_time - self.time_window:
                        self.eyelid_times.popleft()
                        self.eyelid_left.popleft()
                        self.eyelid_right.popleft()
                return True
            else:
                if self.eyelid_available is None:
                    self.eyelid_available = False
                    print(f"⚠ Eyelid data NOT available (type: {type(gaze).__name__})")
                    print("  Enable 'Compute eye state' in Neon Companion")
        except TimeoutError:
            pass
        except Exception as e:
            pass
        return False
    
    def receive_imu_data(self):
        """Get IMU data (called from main loop)."""
        try:
            imu = self.device.receive_imu_datum(timeout_seconds=0.001)
            
            # Skip if IMU is None
            if imu is None:
                return False
                
            current_time = time.time() - self.start_time
            
            if hasattr(imu, 'accel_data') and hasattr(imu, 'gyro_data') and hasattr(imu, 'quaternion'):
                if self.imu_available is None:
                    self.imu_available = True
                    print(f"✓ IMU data available")
                
                with self.data_lock:
                    self.imu_times.append(current_time)
                    self.accel_x.append(imu.accel_data.x)
                    self.accel_y.append(imu.accel_data.y)
                    self.accel_z.append(imu.accel_data.z)
                    self.gyro_x.append(imu.gyro_data.x)
                    self.gyro_y.append(imu.gyro_data.y)
                    self.gyro_z.append(imu.gyro_data.z)
                    self.quaternion_data = imu.quaternion                # Remove old data outside time window
                with self.data_lock:
                    while self.imu_times and self.imu_times[0] < current_time - self.time_window:
                        self.imu_times.popleft()
                        self.accel_x.popleft()
                        self.accel_y.popleft()
                        self.accel_z.popleft()
                        self.gyro_x.popleft()
                        self.gyro_y.popleft()
                        self.gyro_z.popleft()
                return True
            else:
                if self.imu_available is None:
                    self.imu_available = False
                    print(f"⚠ IMU data NOT available")
        except TimeoutError:
            pass
        except Exception:
            pass
        return False
    
    def quaternion_to_rotation_matrix(self, q):
        """Convert quaternion to rotation matrix."""
        w, x, y, z = q.w, q.x, q.y, q.z
        
        R = np.array([
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z, 2*x*z + 2*w*y],
            [2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
            [2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]
        ])
        return R
    
    def draw_3d_rotation(self):
        """Draw 3D head rotation visualization (quaternion orientation only)."""
        self.ax_3d_rotation.clear()
        self.ax_3d_rotation.set_xlim(-2, 2)
        self.ax_3d_rotation.set_ylim(-2, 2)
        self.ax_3d_rotation.set_zlim(-2, 2)
        self.ax_3d_rotation.set_xlabel('X', fontsize=8)
        self.ax_3d_rotation.set_ylabel('Z', fontsize=8)
        self.ax_3d_rotation.set_zlabel('Y', fontsize=8)
        self.ax_3d_rotation.set_title('Head Rotation\n(Quaternion)', fontsize=10, fontweight='bold')
        self.ax_3d_rotation.set_box_aspect([1,1,1])
        
        if self.quaternion_data is None:
            self.ax_3d_rotation.text(0, 0, 0, 'No IMU data', ha='center', va='center')
            return
        
        # Get rotation matrix from quaternion
        R = self.quaternion_to_rotation_matrix(self.quaternion_data)
        
        # Head at origin (no movement, just rotation)
        head_pos = np.array([0.0, 0.0, 0.0])
        
        # Define head coordinate system axes (facing toward viewer initially)
        # Swapped orientation: X=right, Y=toward viewer, Z=up
        forward = np.array([0, -1.2, 0])  # Toward viewer (negative Y)
        right = np.array([1.2, 0, 0])     # Right
        up = np.array([0, 0, 1.2])        # Up
        
        # Rotate axes by current orientation
        forward_rot = R @ forward
        right_rot = R @ right
        up_rot = R @ up
        
        # Draw coordinate axes from head position (thicker and more visible)
        self.ax_3d_rotation.quiver(*head_pos, *right_rot, color='red', arrow_length_ratio=0.2, linewidth=4, label='Right (X)', alpha=0.9)
        self.ax_3d_rotation.quiver(*head_pos, *forward_rot, color='green', arrow_length_ratio=0.2, linewidth=4, label='Forward (Y)', alpha=0.9)
        self.ax_3d_rotation.quiver(*head_pos, *up_rot, color='blue', arrow_length_ratio=0.2, linewidth=4, label='Up (Z)', alpha=0.9)
        
        # Create better head shape (larger)
        u = np.linspace(0, 2 * np.pi, 20)  # Reduced from 30 for performance
        v = np.linspace(0, np.pi, 20)  # Reduced from 30 for performance
        
        # Main head (ellipsoid) - Y and Z swapped
        scale = 1.3
        x_head = scale * 0.4 * np.outer(np.cos(u), np.sin(v))
        y_head = scale * 0.5 * np.outer(np.ones(np.size(u)), np.cos(v))  # Was Z
        z_head = scale * 0.45 * np.outer(np.sin(u), np.sin(v))  # Was Y
        
        # Rotate head shape and translate to head position
        x_head_rot = np.zeros_like(x_head)
        y_head_rot = np.zeros_like(y_head)
        z_head_rot = np.zeros_like(z_head)
        
        for i in range(len(x_head)):
            for j in range(len(x_head[0])):
                point = np.array([x_head[i,j], y_head[i,j], z_head[i,j]])
                rotated = R @ point
                x_head_rot[i,j] = rotated[0] + head_pos[0]
                y_head_rot[i,j] = rotated[2] + head_pos[2]  # Use rotated Z for Y axis
                z_head_rot[i,j] = rotated[1] + head_pos[1]  # Use rotated Y for Z axis
        
        # Draw main head
        self.ax_3d_rotation.plot_surface(x_head_rot, y_head_rot, z_head_rot, alpha=0.5, color='peachpuff', edgecolor='none')
        
        # With Y/Z swap: viewer looks from positive X, face points toward +X
        # Y axis is toward viewer, Z axis is up
        # Nose should extend along +X axis
        nose_base = np.array([0, 0, 0])  # At head center
        nose_tip = np.array([0.4, 0, -0.05])  # Extend along +X toward viewer, slightly down in Z
        nose_base_rot = R @ nose_base + head_pos
        nose_tip_rot = R @ nose_tip + head_pos
        
        # Draw nose as a thicker line (swap Y and Z for display)
        self.ax_3d_rotation.plot([nose_base_rot[0], nose_tip_rot[0]], 
                       [nose_base_rot[2], nose_tip_rot[2]],  # Y display gets Z value
                       [nose_base_rot[1], nose_tip_rot[1]],  # Z display gets Y value
                       'k-', linewidth=4)
        
        # Add eyes on the face (on the +X face of the head)
        # With Y/Z swap: eyes at same X, Z controls up/down position, Y unused (face is at Y=face depth)
        eye_left_pos = np.array([0.35, 0, 0.15])   # Left eye: Z=up position
        eye_right_pos = np.array([0.35, 0, -0.15])  # Right eye: Z=down position (actually, need to think in terms of left/right)
        
        # Actually, with proper Y/Z swap for face orientation:
        # X = left/right on face, Y = depth (toward viewer), Z = up/down
        # Eyes should be side-by-side (different X) and at same height (same Z)
        eye_left_pos = np.array([0.35, 0, 0.2])   # Left eye (higher Z in swapped coords = left in original)
        eye_right_pos = np.array([0.35, 0, -0.2])  # Right eye (lower Z in swapped coords = right in original)
        
        eye_left_rot = R @ eye_left_pos + head_pos
        eye_right_rot = R @ eye_right_pos + head_pos
        
        # Draw eyes (swap Y and Z for display)
        self.ax_3d_rotation.scatter(eye_left_rot[0], eye_left_rot[2], eye_left_rot[1], color='black', s=100)
        self.ax_3d_rotation.scatter(eye_right_rot[0], eye_right_rot[2], eye_right_rot[1], color='black', s=100)
        
        # Add ears (small ellipsoids on sides) - scaled up
        ear_scale = scale * 0.12
        for side in [-1, 1]:  # left and right
            ear_center = np.array([side * 0.42, 0, 0])
            
            # Small ellipsoid for ear (Y and Z swapped)
            u_ear = np.linspace(0, 2 * np.pi, 6)  # Reduced from 10
            v_ear = np.linspace(0, np.pi, 6)  # Reduced from 10
            x_ear = ear_scale * np.outer(np.cos(u_ear), np.sin(v_ear)) + ear_center[0]
            y_ear = ear_scale * np.outer(np.ones(np.size(u_ear)), np.cos(v_ear)) + ear_center[1]  # Was Z
            z_ear = ear_scale * 0.5 * np.outer(np.sin(u_ear), np.sin(v_ear)) + ear_center[2]  # Was Y
            
            # Rotate ear and translate (swap Y and Z in display)
            for i in range(len(x_ear)):
                for j in range(len(x_ear[0])):
                    point = np.array([x_ear[i,j], y_ear[i,j], z_ear[i,j]])
                    rotated = R @ point
                    x_ear[i,j] = rotated[0] + head_pos[0]
                    y_ear[i,j] = rotated[2] + head_pos[2]  # Y display gets Z value
                    z_ear[i,j] = rotated[1] + head_pos[1]  # Z display gets Y value
            
            self.ax_3d_rotation.plot_surface(x_ear, y_ear, z_ear, alpha=0.5, color='peachpuff', edgecolor='none')
        
        # Add gyro vector if available (show rotational motion)
        if len(self.gyro_x) > 0:
            gyro_vec = np.array([self.gyro_x[-1], self.gyro_y[-1], self.gyro_z[-1]]) * 0.5
            if np.linalg.norm(gyro_vec) > 0.01:
                self.ax_3d_rotation.quiver(*head_pos, *gyro_vec, color='orange', arrow_length_ratio=0.15, 
                                linewidth=3.5, alpha=0.95, label='Gyro (rot)')
        
        self.ax_3d_rotation.legend(loc='upper left', fontsize=7)
        self.ax_3d_rotation.view_init(elev=10, azim=-90)
    
    def update_plots(self):
        """Update matplotlib plots and return as image."""
        current_time = time.time() - self.start_time
        
        # Update eyelid plot (with lock for thread-safe access)
        with self.data_lock:
            eyelid_times_copy = list(self.eyelid_times)
            eyelid_left_copy = list(self.eyelid_left)
            eyelid_right_copy = list(self.eyelid_right)
        
        if len(eyelid_times_copy) > 0:
            times_relative = [t - (current_time - self.time_window) for t in eyelid_times_copy]
            self.line_left.set_data(times_relative, eyelid_left_copy)
            self.line_right.set_data(times_relative, eyelid_right_copy)
        elif self.eyelid_available is False:
            # Show message that eyelid data is not available
            self.ax_eyelid.text(0.5, 0.5, 'Eyelid data not available\nEnable "Compute eye state" in Neon Companion app',
                              ha='center', va='center', transform=self.ax_eyelid.transAxes,
                              fontsize=12, color='red', fontweight='bold')
        
        # Update events plot (with lock)
        self.ax_events.clear()
        self.ax_events.set_xlim(0, self.time_window)
        self.ax_events.set_ylim(-0.5, 2.5)
        self.ax_events.set_yticks([0, 1, 2])
        self.ax_events.set_yticklabels(['Blinks', 'Saccades', 'Fixations'], fontsize=7)
        self.ax_events.set_xlabel('Time (seconds)', fontsize=8)
        self.ax_events.set_ylabel('Event Type', fontsize=8)
        self.ax_events.grid(True, alpha=0.3, axis='x')
        
        # Draw event rectangles
        window_start = current_time - self.time_window
        with self.data_lock:
            events_copy = list(self.events)
        
        for event_start, event_end, event_type, details in events_copy:
            if event_end >= window_start:  # Only show events in current window
                rel_start = max(0, event_start - window_start)
                rel_end = event_end - window_start
                width = rel_end - rel_start
                
                if event_type == 'blink':
                    y_pos = 0
                    color = 'purple'
                elif event_type == 'saccade':
                    y_pos = 1
                    color = 'orange'
                else:  # fixation
                    y_pos = 2
                    color = 'green'
                
                rect = Rectangle((rel_start, y_pos - 0.3), width, 0.6, 
                               facecolor=color, edgecolor='black', alpha=0.7)
                self.ax_events.add_patch(rect)
                
                # Add text label if wide enough
                if width > 1:
                    self.ax_events.text(rel_start + width/2, y_pos, str(details),
                                      ha='center', va='center', fontsize=8, color='white')
        
        # Clean old events (with lock)
        with self.data_lock:
            self.events = [(s, e, t, d) for s, e, t, d in self.events if e >= window_start]
        
        # Update Accelerometer plot with adaptive scaling (with lock)
        with self.data_lock:
            imu_times_copy = list(self.imu_times)
            accel_x_copy = list(self.accel_x)
            accel_y_copy = list(self.accel_y)
            accel_z_copy = list(self.accel_z)
            gyro_x_copy = list(self.gyro_x)
            gyro_y_copy = list(self.gyro_y)
            gyro_z_copy = list(self.gyro_z)
        
        if len(imu_times_copy) > 0:
            times_relative = [t - (current_time - self.time_window) for t in imu_times_copy]
            self.line_accel_x.set_data(times_relative, accel_x_copy)
            self.line_accel_y.set_data(times_relative, accel_y_copy)
            self.line_accel_z.set_data(times_relative, accel_z_copy)
            
            # Auto-scale y-axis for accelerometer
            accel_values = accel_x_copy + accel_y_copy + accel_z_copy
            if accel_values:
                y_min = min(accel_values)
                y_max = max(accel_values)
                y_range = y_max - y_min
                margin = y_range * 0.1 if y_range > 0 else 0.1
                self.ax_accel.set_ylim(y_min - margin, y_max + margin)
        elif self.imu_available is False:
            self.ax_accel.text(0.5, 0.5, 'Accelerometer data not available',
                             ha='center', va='center', transform=self.ax_accel.transAxes,
                             fontsize=12, color='red', fontweight='bold')
        
        # Update Gyroscope plot with adaptive scaling
        if len(imu_times_copy) > 0:
            times_relative = [t - (current_time - self.time_window) for t in imu_times_copy]
            self.line_gyro_x.set_data(times_relative, gyro_x_copy)
            self.line_gyro_y.set_data(times_relative, gyro_y_copy)
            self.line_gyro_z.set_data(times_relative, gyro_z_copy)
            
            # Auto-scale y-axis for gyroscope
            gyro_values = gyro_x_copy + gyro_y_copy + gyro_z_copy
            if gyro_values:
                y_min = min(gyro_values)
                y_max = max(gyro_values)
                y_range = y_max - y_min
                margin = y_range * 0.1 if y_range > 0 else 0.1
                self.ax_gyro.set_ylim(y_min - margin, y_max + margin)
        elif self.imu_available is False:
            self.ax_gyro.text(0.5, 0.5, 'Gyroscope data not available',
                            ha='center', va='center', transform=self.ax_gyro.transAxes,
                            fontsize=12, color='red', fontweight='bold')
        
        # Update 3D visualization
        self.draw_3d_rotation()
        
        # Update status (with lock)
        with self.data_lock:
            eyelid_count = len(self.eyelid_times)
            events_count = len(self.events)
            imu_count = len(self.imu_times)
            gaze_copy = self.latest_gaze
        
        worn_text = ""
        if gaze_copy:
            worn_text = f" | {'WORN' if gaze_copy.worn else 'NOT WORN'}"
        
        self.status_text.set_text(
            f'Device: {self.device.phone_name}{worn_text} | Time: {current_time:.1f}s | '
            f'Eyelid: {eyelid_count} | Events: {events_count} | IMU: {imu_count}'
        )
        
        # Render to image
        self.canvas.draw()
        width, height = self.fig.get_size_inches() * self.fig.get_dpi()
        img = np.frombuffer(self.canvas.buffer_rgba(), dtype='uint8').reshape(int(height), int(width), 4)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        
        return img
    
    def run(self):
        """Start the real-time monitor."""
        if not self.connect_device():
            return
        
        self.running = True
        self.start_time = time.time()
        
        # Start data collection threads (video_gaze gets scene+eye+gaze together)
        video_gaze_thread = threading.Thread(target=self.data_collection_thread, args=('video_gaze',), daemon=True)
        video_render_thread = threading.Thread(target=self.video_rendering_thread, daemon=True)
        events_thread = threading.Thread(target=self.data_collection_thread, args=('events',), daemon=True)
        gaze_thread = threading.Thread(target=self.data_collection_thread, args=('gaze',), daemon=True)
        imu_thread = threading.Thread(target=self.data_collection_thread, args=('imu',), daemon=True)
        
        # Start video threads first with highest priority
        video_gaze_thread.start()
        video_render_thread.start()
        time.sleep(0.1)  # Let video threads initialize
        
        # Start other threads
        events_thread.start()
        gaze_thread.start()
        imu_thread.start()
        
        self.threads = [video_gaze_thread, events_thread, gaze_thread, imu_thread, video_render_thread]
        
        print("\n" + "=" * 70)
        print("Monitor started!")
        print("- Scene Camera: Scene video with gaze overlay (eye camera disabled for speed)")
        print("- Plots: Time series + 3D head rotation")
        print("  * Eyelid openness")
        print("  * Eye events (fixations, saccades, blinks)")
        print("  * Accelerometer (linear motion)")
        print("  * Gyroscope (rotational motion)")
        print("  * 3D head rotation (quaternion orientation)")
        print("Press 'q' in any window or Ctrl+C to quit")
        print("=" * 70 + "\n")
        
        try:
            plot_update_counter = 0
            
            print("Creating OpenCV windows...")
            # Create named windows with NORMAL flag to allow resizing
            cv2.namedWindow('Neon Scene Camera', cv2.WINDOW_NORMAL)
            cv2.namedWindow('Time Series Data', cv2.WINDOW_NORMAL)
            
            # Resize video window to 50% of original size (800x600 from 1600x1200)
            cv2.resizeWindow('Neon Scene Camera', 800, 600)
            
            # Move windows to specific positions
            cv2.moveWindow('Neon Scene Camera', 50, 50)
            cv2.moveWindow('Time Series Data', 870, 50)  # Positioned right next to video (50+800+20)
            
            print("\n*** WINDOWS SHOULD NOW BE VISIBLE ON YOUR SCREEN ***")
            print("*** Position: Scene Camera at (50,50), Plots at (900,50) ***")
            print("*** Press 'q' to quit ***\n")
            
            while self.running:
                # Display pre-rendered video frame from rendering thread (no resizing for speed)
                if self.display_frame is not None:
                    with self.data_lock:
                        display = self.display_frame
                    
                    try:
                        cv2.imshow('Neon Scene Camera', display)
                    except:
                        # Window might have been closed
                        print("Video window closed or error displaying")
                        break
                else:
                    # No frame yet, but keep windows responsive
                    time.sleep(0.001)
                
                # Update plots every frame for maximum smoothness
                plot_update_counter += 1
                if plot_update_counter >= 1:
                    plot_update_counter = 0
                    plot_img = self.update_plots()
                    cv2.imshow('Time Series Data', plot_img)
                
                # MUST call waitKey to keep windows responsive
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\\nUser pressed 'q' - exiting...")
                    break
                    
        except KeyboardInterrupt:
            print("\\n\\nStopping (Ctrl+C)...")
        except Exception as e:
            print(f"\\n\\nError in main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Cleaning up...")
            self.running = False
            time.sleep(0.5)  # Give threads time to finish
            cv2.destroyAllWindows()
            plt.close('all')
            if self.device:
                self.device.close()
            print("Monitor closed.")


def main():
    monitor = NeonRealtimeMonitor(time_window=30)
    monitor.run()


if __name__ == "__main__":
    main()
