#!/usr/bin/env python3
"""
Smart Log Analyzer
=================

A comprehensive log analysis tool that can parse various log formats including:
- System logs (syslog, journalctl)
- Application logs (JSON, plain text)
- Web server logs (Apache, Nginx combined format)

Features:
- Memory-efficient streaming processing for large log files
- Automatic log format detection
- Error and warning pattern recognition
- Performance metrics extraction
- Structured JSON output with insights

Usage:
    python smart_log_analyzer.py /path/to/logfile.log
    python smart_log_analyzer.py --format nginx /path/to/access.log
    cat logfile.log | python smart_log_analyzer.py -
"""

import argparse
import json
import re
import sys
import gzip
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Optional


class LogAnalyzer:
    def __init__(self):
        self.error_patterns = [
            r'(?i)error',
            r'(?i)exception',
            r'(?i)fail',
            r'(?i)critical',
            r'(?i)fatal',
            r'(?i)panic',
            r'(?i)segfault',
            r'(?i)timeout',
            r'(?i)connection refused',
            r'(?i)50[0-9] ',
            r'(?i)40[0-9] '
        ]
        
        self.warning_patterns = [
            r'(?i)warn',
            r'(?i)warning',
            r'(?i)deprecated',
            r'(?i)slow',
            r'(?i)high latency',
            r'(?i)memory usage',
            r'(?i)disk full',
            r'(?i)cpu usage'
        ]
        
        # Common log format regex patterns
        self.log_formats = {
            'syslog': r'^(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+(?P<host>\S+)\s+(?P<service>\S+):\s+(?P<message>.*)$',
            'nginx': r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+(?P<size>\S+)\s+"(?P<referrer>[^"]*)"\s+"(?P<user_agent>[^"]*)"$',
            'apache': r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+(?P<size>\S+)(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?$',
            'json': r'^\{.*\}$'
        }
    
    def detect_format(self, line: str) -> str:
        """Detect the log format of a given line."""
        if re.match(self.log_formats['json'], line.strip()):
            return 'json'
        
        for format_name, pattern in self.log_formats.items():
            if format_name != 'json' and re.match(pattern, line):
                return format_name
        
        return 'unknown'
    
    def parse_line(self, line: str, detected_format: str) -> Dict[str, Any]:
        """Parse a single log line based on its detected format."""
        if detected_format == 'json':
            try:
                return json.loads(line.strip())
            except json.JSONDecodeError:
                return {'raw': line.strip(), 'format': 'json_parse_error'}
        
        elif detected_format in ['syslog', 'nginx', 'apache']:
            match = re.match(self.log_formats[detected_format], line)
            if match:
                return match.groupdict()
            else:
                return {'raw': line.strip(), 'format': f'{detected_format}_parse_error'}
        
        else:
            return {'raw': line.strip(), 'format': 'unknown'}
    
    def analyze_log_file(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze log file and return structured insights."""
        stats = {
            'total_lines': 0,
            'errors': 0,
            'warnings': 0,
            'error_samples': [],
            'warning_samples': [],
            'status_codes': Counter(),
            'response_times': [],
            'top_paths': Counter(),
            'top_ips': Counter(),
            'format_distribution': Counter(),
            'hourly_activity': defaultdict(int)
        }
        
        # Determine input source
        if file_path and file_path != '-':
            if file_path.endswith('.gz'):
                file_handle = gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
            else:
                file_handle = open(file_path, 'r', encoding='utf-8', errors='ignore')
        else:
            file_handle = sys.stdin
        
        try:
            for line_num, line in enumerate(file_handle, 1):
                line = line.rstrip('\n\r')
                if not line:
                    continue
                
                stats['total_lines'] += 1
                
                # Detect format and parse
                detected_format = self.detect_format(line)
                stats['format_distribution'][detected_format] += 1
                
                parsed_data = self.parse_line(line, detected_format)
                
                # Extract timestamp for hourly activity
                if 'timestamp' in parsed_data:
                    try:
                        # Handle different timestamp formats
                        if detected_format in ['nginx', 'apache']:
                            # Apache/Nginx format: 04/Feb/2026:08:15:30 +0800
                            hour = parsed_data['timestamp'].split(':')[1]
                            stats['hourly_activity'][hour] += 1
                        elif detected_format == 'syslog':
                            # Syslog format: Feb  4 08:15:30
                            hour = parsed_data['timestamp'].split()[2].split(':')[0]
                            stats['hourly_activity'][hour] += 1
                    except (IndexError, ValueError):
                        pass
                
                # Check for errors and warnings
                message_text = ''
                if detected_format == 'json':
                    message_text = json.dumps(parsed_data)
                elif 'message' in parsed_data:
                    message_text = parsed_data['message']
                elif 'raw' in parsed_data:
                    message_text = parsed_data['raw']
                
                # Count errors
                for pattern in self.error_patterns:
                    if re.search(pattern, message_text):
                        stats['errors'] += 1
                        if len(stats['error_samples']) < 10:
                            stats['error_samples'].append({
                                'line_number': line_num,
                                'content': message_text[:200],
                                'format': detected_format
                            })
                        break
                
                # Count warnings
                for pattern in self.warning_patterns:
                    if re.search(pattern, message_text):
                        stats['warnings'] += 1
                        if len(stats['warning_samples']) < 10:
                            stats['warning_samples'].append({
                                'line_number': line_num,
                                'content': message_text[:200],
                                'format': detected_format
                            })
                        break
                
                # Extract web server specific metrics
                if detected_format in ['nginx', 'apache']:
                    if 'status' in parsed_data:
                        stats['status_codes'][parsed_data['status']] += 1
                    
                    if 'path' in parsed_data:
                        stats['top_paths'][parsed_data['path']] += 1
                    
                    if 'ip' in parsed_data:
                        stats['top_ips'][parsed_data['ip']] += 1
                
                # Progress indicator for large files
                if line_num % 10000 == 0:
                    print(f"Processed {line_num} lines...", file=sys.stderr)
        
        finally:
            if file_handle != sys.stdin:
                file_handle.close()
        
        # Calculate insights
        insights = {
            'summary': {
                'total_lines_processed': stats['total_lines'],
                'error_count': stats['errors'],
                'warning_count': stats['warnings'],
                'error_rate': round(stats['errors'] / max(stats['total_lines'], 1) * 100, 2),
                'warning_rate': round(stats['warnings'] / max(stats['total_lines'], 1) * 100, 2)
            },
            'format_analysis': dict(stats['format_distribution']),
            'error_analysis': {
                'samples': stats['error_samples'],
                'most_common_errors': self._get_common_patterns(stats['error_samples'])
            },
            'warning_analysis': {
                'samples': stats['warning_samples'],
                'most_common_warnings': self._get_common_patterns(stats['warning_samples'])
            },
            'web_server_metrics': {
                'status_code_distribution': dict(stats['status_codes']),
                'top_requested_paths': dict(stats['top_paths'].most_common(10)),
                'top_client_ips': dict(stats['top_ips'].most_common(10))
            },
            'temporal_analysis': {
                'hourly_activity': dict(stats['hourly_activity'])
            },
            'recommendations': self._generate_recommendations(stats)
        }
        
        return insights
    
    def _get_common_patterns(self, samples: List[Dict]) -> List[str]:
        """Extract common patterns from error/warning samples."""
        if not samples:
            return []
        
        # Simple pattern extraction - could be enhanced with more sophisticated NLP
        patterns = []
        for sample in samples[:5]:  # Limit to first 5 samples
            content = sample['content'].lower()
            if 'timeout' in content:
                patterns.append('Timeout issues')
            elif 'connection' in content:
                patterns.append('Connection problems')
            elif 'memory' in content or 'ram' in content:
                patterns.append('Memory pressure')
            elif 'disk' in content or 'storage' in content:
                patterns.append('Storage issues')
            elif 'cpu' in content:
                patterns.append('High CPU usage')
        
        return list(set(patterns))[:3]  # Return unique patterns, max 3
    
    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if stats['errors'] > 0:
            recommendations.append("Investigate error patterns - consider implementing better error handling")
        
        if stats['warnings'] > 0:
            recommendations.append("Address warning messages to prevent potential issues")
        
        # Check for high error rate
        error_rate = stats['errors'] / max(stats['total_lines'], 1)
        if error_rate > 0.05:  # More than 5% errors
            recommendations.append("High error rate detected (>5%) - immediate investigation recommended")
        
        # Check for problematic status codes
        bad_status_codes = [code for code in stats['status_codes'] if code.startswith(('4', '5'))]
        if bad_status_codes:
            recommendations.append("HTTP 4xx/5xx errors detected - check application health")
        
        # Check for suspicious IP activity
        if stats['top_ips']:
            top_ip, count = stats['top_ips'].most_common(1)[0]
            if count > stats['total_lines'] * 0.1:  # Single IP making >10% of requests
                recommendations.append(f"Suspicious activity from IP {top_ip} - possible bot or attack")
        
        return recommendations if recommendations else ["No critical issues detected - system appears healthy"]


def main():
    parser = argparse.ArgumentParser(description='Smart Log Analyzer')
    parser.add_argument('logfile', nargs='?', default='-', 
                       help='Path to log file (use "-" for stdin)')
    parser.add_argument('--format', choices=['auto', 'syslog', 'nginx', 'apache', 'json'],
                       default='auto', help='Force specific log format')
    parser.add_argument('--output', choices=['json', 'text'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer()
    
    try:
        insights = analyzer.analyze_log_file(args.logfile)
        
        if args.output == 'json':
            print(json.dumps(insights, indent=2, ensure_ascii=False))
        else:
            # Text output
            print("=== SMART LOG ANALYSIS ===")
            summary = insights['summary']
            print(f"Total lines processed: {summary['total_lines_processed']}")
            print(f"Errors: {summary['error_count']} ({summary['error_rate']}%)")
            print(f"Warnings: {summary['warning_count']} ({summary['warning_rate']}%)")
            
            print("\n=== RECOMMENDATIONS ===")
            for rec in insights['recommendations']:
                print(f"- {rec}")
            
            if insights['error_analysis']['samples']:
                print(f"\n=== ERROR SAMPLES (showing {len(insights['error_analysis']['samples'])}) ===")
                for sample in insights['error_analysis']['samples']:
                    print(f"Line {sample['line_number']}: {sample['content']}")
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()