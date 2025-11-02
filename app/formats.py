from datetime import datetime
import random
from typing import Dict, Any
from .proto.track_pb2 import DistributionTrack

def iso8601z() -> str:
    """Return current time in ISO8601 format with Z suffix"""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def build_xml_heartbeat() -> str:
    """Create XML heartbeat message"""
    return f'<heartbeat ts="{iso8601z()}"/>'

def build_json_heartbeat() -> Dict[str, str]:
    """Create JSON heartbeat message"""
    return {"type": "heartbeat", "ts": iso8601z()}

def sample_track() -> Dict[str, Any]:
    """Generate a sample track with reasonable values"""
    track = {
        "uniqueid": f"TRACK_{random.randint(1000, 9999)}",
        "trackid": random.randint(1, 1000),
        "senderid": random.randint(1, 100),
        "channelid": random.randint(1, 4),
        "speedmps": round(random.uniform(0, 30), 2),
        "coursedegrees": round(random.uniform(0, 360), 2),
        "classification": random.choice([1, 2, 4, 8, 16, 32]),
        "classificationprobability": round(random.uniform(0.5, 1.0), 3),
        "xposition": round(random.uniform(-1000, 1000), 2),
        "yposition": round(random.uniform(-1000, 1000), 2),
        "latitude": round(random.uniform(-90, 90), 6),
        "longitude": round(random.uniform(-180, 180), 6),
        "tag": "DATA",
        "sizeinaz": round(random.uniform(0, 10), 2),
        "sizeinrange": round(random.uniform(0, 10), 2),
        "seen": random.randint(1, 100),
        "coasts": random.randint(0, 5),
        "laneuserid": random.randint(1, 10),
        "sectionuserid": random.randint(1, 10),
        "carriagewayname": f"LANE_{random.randint(1, 4)}"
    }
    return track

def build_xml_track(track: Dict[str, Any]) -> str:
    """Convert track data to XML format"""
    attrs = ' '.join(f'{k}="{v}"' for k, v in track.items())
    return f'<track {attrs}/>'

def build_json_track(track: Dict[str, Any]) -> Dict[str, Any]:
    """Convert track data to JSON format"""
    return {"type": "track", **track}

def build_protobuf_track(track: Dict[str, Any]) -> bytes:
    """Convert track data to Protobuf message"""
    pb_track = DistributionTrack()
    for key, value in track.items():
        setattr(pb_track, key, value)
    return pb_track.SerializeToString()

def build_protobuf_heartbeat() -> bytes:
    """Create a Protobuf heartbeat message"""
    pb_track = DistributionTrack()
    pb_track.tag = "HEARTBEAT"
    pb_track.trackid = 0
    pb_track.uniqueid = f"HB_{int(datetime.utcnow().timestamp())}"
    return pb_track.SerializeToString()