#!/usr/bin/env python3
"""
System Monitor Tool
Monitors server resources and generates reports
"""

import psutil
import datetime
import json
import os

def get_system_info():
    """Get comprehensive system information"""
    info = {
        'timestamp': datetime.datetime.now().isoformat(),
        'cpu': {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count()
        },
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent
        }
    }
    return info

def save_report(info, filename=None):
    """Save system report to file"""
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_report_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(info, f, indent=2)
    
    return filename

def main():
    """Main function"""
    print("📊 System Monitor Tool")
    print("Collecting system information...")
    
    info = get_system_info()
    filename = save_report(info)
    
    print(f"✅ Report saved to: {filename}")
    print(f"CPU Usage: {info['cpu']['percent']}%")
    print(f"Memory Usage: {info['memory']['percent']}%")
    print(f"Disk Usage: {info['disk']['percent']}%")

if __name__ == "__main__":
    main()