#!/usr/bin/env python
import sys

# Initialize variables for all tasks
current_airline = None
current_route = None
current_date = None

# Variables for Task 1: Average Price Calculation
total_price = 0
count = 0

# Variables for Task 2: Route Frequency Calculation
current_route_count = 0

# Variables for Task 3: Price Distribution
price_list = []

for line in sys.stdin:
    line = line.strip()
    # Split the mapper output by type of task, key (airline/route/date), and value (price/count)
    task_type, key, value = line.split('\t')

    if task_type == "AveragePrice":
        # Task 1: Calculate average flight price by airline
        airline = key
        price = float(value)
        
        if current_airline == airline:
            total_price += price
            count += 1
        else:
            if current_airline:
                average_price = total_price / count
                print(f"Average Price for {current_airline}: {average_price:.2f}")
            
            # Reset counters for the new airline
            current_airline = airline
            total_price = price
            count = 1

    elif task_type == "RouteFrequency":
        # Task 2: Calculate frequency of flight routes
        route = key
        route_count = int(value)
        
        if current_route == route:
            current_route_count += route_count
        else:
            if current_route:
                print(f"Frequency of route {current_route}: {current_route_count}")
            
            # Reset counters for the new route
            current_route = route
            current_route_count = route_count

    elif task_type == "PriceDistribution":
        # Task 3: Calculate price distribution over dates
        date = key
        price = float(value)
        
        if current_date == date:
            price_list.append(price)
        else:
            if current_date:
                # Output the distribution for the previous date
                min_price = min(price_list)
                max_price = max(price_list)
                avg_price = sum(price_list) / len(price_list)
                print(f"Price Distribution on {current_date} - Min: {min_price:.2f}, Max: {max_price:.2f}, Avg: {avg_price:.2f}")
            
            # Reset list for new date
            current_date = date
            price_list = [price]

# Output results for the last keys after looping through all input
if current_airline:
    average_price = total_price / count
    print(f"Average Price for {current_airline}: {average_price:.2f}")

if current_route:
    print(f"Frequency of route {current_route}: {current_route_count}")

if current_date:
    min_price = min(price_list)
    max_price = max(price_list)
    avg_price = sum(price_list) / len(price_list)
    print(f"Price Distribution on {current_date} - Min: {min_price:.2f}, Max: {max_price:.2f}, Avg: {avg_price:.2f}")
