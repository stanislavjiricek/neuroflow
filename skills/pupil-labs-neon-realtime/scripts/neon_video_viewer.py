"""
Pupil Labs Real-time API - Scene Camera with Gaze Overlay
Shows live video feed from Neon glasses with gaze position overlay
"""

import cv2
from pupil_labs.realtime_api.simple import discover_one_device


def main():
    print("=" * 70)
    print("Pupil Labs Neon - Scene Camera with Gaze Overlay")
    print("=" * 70)
    print("\nLooking for Neon device...")
    print("(Make sure Neon Companion app is running)")
    
    # Discover and connect to device
    device = discover_one_device(max_search_duration_seconds=10)
    
    if device is None:
        print("No device found.")
        return
    
    print(f"\n✓ Connected to device: {device.serial_number_glasses}")
    print(f"  Phone: {device.phone_name}")
    print(f"  IP: {device.phone_ip}")
    print("\n" + "=" * 70)
    print("Video streaming started!")
    print("Press 'q' to quit")
    print("=" * 70 + "\n")
    
    try:
        frame_count = 0
        
        while True:
            # Receive matched scene video frame and gaze data
            matched = device.receive_matched_scene_video_frame_and_gaze()
            
            # Get the frame and gaze data
            frame = matched.frame.bgr_pixels
            gaze = matched.gaze
            
            frame_count += 1
            
            # Draw gaze point on frame
            if gaze is not None:
                # Gaze coordinates are in pixels
                gaze_x = int(gaze.x)
                gaze_y = int(gaze.y)
                
                # Draw gaze circle (red)
                cv2.circle(frame, (gaze_x, gaze_y), 30, (0, 0, 255), 3)
                cv2.circle(frame, (gaze_x, gaze_y), 5, (0, 0, 255), -1)
                
                # Draw crosshair
                cv2.line(frame, (gaze_x - 40, gaze_y), (gaze_x + 40, gaze_y), (0, 0, 255), 2)
                cv2.line(frame, (gaze_x, gaze_y - 40), (gaze_x, gaze_y + 40), (0, 0, 255), 2)
                
                # Display gaze info
                worn_text = "WORN" if gaze.worn else "NOT WORN"
                info_text = f"Gaze: ({gaze.x:.1f}, {gaze.y:.1f}) | {worn_text}"
                cv2.putText(frame, info_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                # No gaze data available
                cv2.putText(frame, "No gaze data", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Display frame count
            cv2.putText(frame, f"Frame: {frame_count}", (10, frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('Neon Scene Camera with Gaze', frame)
            
            # Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nQuitting...")
                break
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        # Clean up
        cv2.destroyAllWindows()
        device.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
