import re
import pandas as pd
import numpy as np

class SpeedProcessor:
    MPH_TO_KMPH = 1.60934
    
    SPEED_DEFAULTS = {
        "motorway": 110,
        "motorway_link": 110,
        "trunk": 90,
        "trunk_link": 90,
        "primary": 70,
        "primary_link": 70,
        "secondary": 60,
        "secondary_link": 60,
        "tertiary": 50,
        "tertiary_link": 50,
        "residential": 30,
        "living_street": 30,
        "service": 20,
        "unclassified": 40,
        "road": 40,
    }
    
    @staticmethod
    def predict_maxspeed(highway):
        """Predict speed based on highway type."""
        if isinstance(highway, list):
            highway = highway[0]
        highway = str(highway).lower() if highway else ""
        return SpeedProcessor.SPEED_DEFAULTS.get(highway, 50)
    
    @staticmethod
    def fix_speed_format(df):
        """Convert speed values to km/h format."""
        speed_parts = df['maxspeed'].astype(str).str.extract(
            r'(\d+\.?\d*)\s*(mph|km/h|kmh|kph)?',
            flags=re.IGNORECASE
        )
        
        df['speed_value'] = pd.to_numeric(speed_parts[0], errors='coerce')
        df['speed_unit'] = speed_parts[1].str.lower()
        df['maxspeed'] = df['speed_value'].copy()
        
        df.loc[df['speed_unit'] == 'mph', 'maxspeed'] = (
            df['speed_value'] * SpeedProcessor.MPH_TO_KMPH
        )
        
        return df.drop(columns=['speed_value', 'speed_unit'])
    
    @staticmethod
    def process_speeds(edges_df, highway_col='highway'):
        """Process and fill missing speeds."""
        edges_df = SpeedProcessor.fix_speed_format(edges_df)
        edges_df['maxspeed'] = edges_df.apply(
            lambda row: (
                SpeedProcessor.predict_maxspeed(row[highway_col])
                if pd.isna(row['maxspeed'])
                else row['maxspeed']
            ),
            axis=1
        )
        edges_df['maxspeed'] = edges_df['maxspeed'].astype(float)
        return edges_df
