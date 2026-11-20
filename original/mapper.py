#!/usr/bin/env python
import sys
import csv
import datetime

# This mapper will handle three tasks based on the given dataset
for line in sys.stdin:
    try:
        # Read each line and split it into columns using CSV reader
        reader = csv.reader([line])
        for row in reader:
            if row[0] != 'Airline':  # Skip the header row
                # Extract necessary columns
                airline = row[0]  # Airline column
                journey_date = row[1]  # Date_of_Journey column
                source = row[2]  # Source column
                destination = row[3]  # Destination column
                price = row[10]  # Price column
                
                # Task 1: Output Airline and Price for average price calculation
                if price:
                    print(f"AveragePrice\t{airline}\t{price}")

                # Task 2: Output Route and 1 for frequency calculation
                route = f"{source}-{destination}"
                print(f"RouteFrequency\t{route}\t1")

                # Task 3: Output Date and Price for distribution analysis
                date_format = datetime.datetime.strptime(journey_date, "%d/%m/%Y").date()
                print(f"PriceDistribution\t{date_format}\t{price}")

    except Exception as e:
        sys.stderr.write(f"Error processing line: {line} - {e}\n")
