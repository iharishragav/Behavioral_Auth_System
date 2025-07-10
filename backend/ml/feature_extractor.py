# feature_extractor.py
import numpy as np
from scipy import stats
from scipy.signal import find_peaks
import pandas as pd

class BehavioralFeatureExtractor:
    def __init__(self):
        self.keystroke_features = {}
        self.mouse_features = {}
    
    def extract_keystroke_features(self, keystroke_data):
        """Extract features from keystroke dynamics"""
        features = {}
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(keystroke_data)
        
        # Filter for keyup events with dwell time
        keyup_events = df[df['type'] == 'keyup'].copy()
        
        if len(keyup_events) < 5:
            return self.get_default_keystroke_features()
        
        # Dwell time features
        dwell_times = keyup_events['dwellTime'].values
        features['dwell_mean'] = np.mean(dwell_times)
        features['dwell_std'] = np.std(dwell_times)
        features['dwell_median'] = np.median(dwell_times)
        features['dwell_skew'] = stats.skew(dwell_times)
        features['dwell_kurtosis'] = stats.kurtosis(dwell_times)
        
        # Flight time features (time between keystrokes)
        timestamps = keyup_events['timestamp'].values
        flight_times = np.diff(timestamps)
        
        features['flight_mean'] = np.mean(flight_times)
        features['flight_std'] = np.std(flight_times)
        features['flight_median'] = np.median(flight_times)
        
        # Typing rhythm features
        features['typing_speed'] = len(keyup_events) / (timestamps[-1] - timestamps[0]) * 1000
        
        # Key frequency analysis
        key_counts = keyup_events['key'].value_counts()
        features['unique_keys'] = len(key_counts)
        features['most_frequent_key_ratio'] = key_counts.iloc[0] / len(keyup_events) if len(key_counts) > 0 else 0
        
        # Digraph analysis (two-key combinations)
        digraphs = []
        for i in range(len(keyup_events) - 1):
            digraph = keyup_events.iloc[i]['key'] + keyup_events.iloc[i+1]['key']
            digraphs.append(digraph)
        
        if digraphs:
            unique_digraphs = len(set(digraphs))
            features['digraph_diversity'] = unique_digraphs / len(digraphs)
        else:
            features['digraph_diversity'] = 0
        
        return features
    
    def extract_mouse_features(self, mouse_data):
        """Extract features from mouse dynamics"""
        features = {}
        
        df = pd.DataFrame(mouse_data)
        
        if len(df) < 5:
            return self.get_default_mouse_features()
        
        # Mouse movement features
        move_events = df[df['type'] == 'mousemove'].copy()
        
        if len(move_events) > 1:
            # Calculate velocities
            move_events['velocity_x'] = np.gradient(move_events['x'])
            move_events['velocity_y'] = np.gradient(move_events['y'])
            move_events['velocity_magnitude'] = np.sqrt(
                move_events['velocity_x']**2 + move_events['velocity_y']**2
            )
            
            # Velocity features
            features['velocity_mean'] = np.mean(move_events['velocity_magnitude'])
            features['velocity_std'] = np.std(move_events['velocity_magnitude'])
            features['velocity_max'] = np.max(move_events['velocity_magnitude'])
            
            # Acceleration features
            accelerations = np.gradient(move_events['velocity_magnitude'])
            features['acceleration_mean'] = np.mean(accelerations)
            features['acceleration_std'] = np.std(accelerations)
            
            # Movement patterns
            features['movement_efficiency'] = self.calculate_movement_efficiency(move_events)
            features['direction_changes'] = self.count_direction_changes(move_events)
            
        else:
            features.update(self.get_default_mouse_features())
        
        # Click features
        click_events = df[df['type'] == 'click'].copy()
        
        if len(click_events) > 1:
            click_intervals = np.diff(click_events['timestamp'])
            features['click_interval_mean'] = np.mean(click_intervals)
            features['click_interval_std'] = np.std(click_intervals)
            features['click_rate'] = len(click_events) / (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]) * 1000
        else:
            features['click_interval_mean'] = 0
            features['click_interval_std'] = 0
            features['click_rate'] = 0
        
        return features
    
    def calculate_movement_efficiency(self, move_events):
        """Calculate how efficiently the mouse moves (straight line vs actual path)"""
        if len(move_events) < 2:
            return 0
        
        start_x, start_y = move_events.iloc[0]['x'], move_events.iloc[0]['y']
        end_x, end_y = move_events.iloc[-1]['x'], move_events.iloc[-1]['y']
        
        # Straight line distance
        straight_distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        # Actual path distance
        actual_distance = 0
        for i in range(1, len(move_events)):
            dx = move_events.iloc[i]['x'] - move_events.iloc[i-1]['x']
            dy = move_events.iloc[i]['y'] - move_events.iloc[i-1]['y']
            actual_distance += np.sqrt(dx**2 + dy**2)
        
        if actual_distance == 0:
            return 0
        
        return straight_distance / actual_distance
    
    def count_direction_changes(self, move_events):
        """Count how many times the mouse changes direction"""
        if len(move_events) < 3:
            return 0
        
        direction_changes = 0
        prev_dx = move_events.iloc[1]['x'] - move_events.iloc[0]['x']
        prev_dy = move_events.iloc[1]['y'] - move_events.iloc[0]['y']
        
        for i in range(2, len(move_events)):
            dx = move_events.iloc[i]['x'] - move_events.iloc[i-1]['x']
            dy = move_events.iloc[i]['y'] - move_events.iloc[i-1]['y']
            
            # Check if direction changed significantly
            if abs(dx - prev_dx) > 5 or abs(dy - prev_dy) > 5:
                direction_changes += 1
            
            prev_dx, prev_dy = dx, dy
        
        return direction_changes
    
    def get_default_keystroke_features(self):
        """Return default keystroke features when insufficient data"""
        return {
            'dwell_mean': 0, 'dwell_std': 0, 'dwell_median': 0,
            'dwell_skew': 0, 'dwell_kurtosis': 0,
            'flight_mean': 0, 'flight_std': 0, 'flight_median': 0,
            'typing_speed': 0, 'unique_keys': 0, 'most_frequent_key_ratio': 0,
            'digraph_diversity': 0
        }
    
    def get_default_mouse_features(self):
        """Return default mouse features when insufficient data"""
        return {
            'velocity_mean': 0, 'velocity_std': 0, 'velocity_max': 0,
            'acceleration_mean': 0, 'acceleration_std': 0,
            'movement_efficiency': 0, 'direction_changes': 0,
            'click_interval_mean': 0, 'click_interval_std': 0, 'click_rate': 0
        }
