# Findings – TTC Delay Analysis

This document summarizes early insights from exploratory queries.

## General Patterns
- Subway lines show more frequent but shorter delays.
- Bus delays tend to be longer, with larger headway gaps.
- Streetcars show higher variability, especially during rush hours.

## Peak Hours
- Morning (7–9 AM) and evening (4–6 PM) delays are consistently above daily averages.
- Station-level heatmaps reveal congestion at downtown transfer points.

## Causes
- Mechanical issues (`MUSAN`) are the most frequent overall.
- Signal-related issues (`MTSAN`) dominate in subway delays.
- Weather-related codes spike seasonally (e.g., winter storms).

## Cross-Service Comparison
- Average delay (minutes): Bus > Subway > Streetcar
- Headway irregularities are most severe for buses.

## Limitations
- Cause code mapping requires full TTC documentation.
- Some vehicle IDs are missing or inconsistent across files.