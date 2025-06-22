#!/usr/bin/env python3
import argparse
from tracker import ProcurementTracker

def main():
    parser = argparse.ArgumentParser(description="Track and download procurement files")
    parser.add_argument(
        '-u', '--url',
        default='https://dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych',
        help='Source URL to scrape'
    )
    parser.add_argument(
        '-o', '--output',
        default='./cpv',
        help='Output directory for downloaded files'
    )
    args = parser.parse_args()
    
    tracker = ProcurementTracker(args.output)
    tracker.process_links(args.url)
    tracker.save_state()

if __name__ == "__main__":
    main()
