# Outiliers detection tools
Based on ee-outliers

Use SQL query to extract columns from the database, and then apply the metrics on each columns.

Many outlier detection methods are availables

One model to rule them all

# Start

> source ./python-env/bin/activate
> 
> cd app
> 
> python3.7 main.py --mode interactive --config config.yaml


# Detection
Default values are in bold.

| method | sensitivity |trigger_on|n_neighbors|
|:------:|:-----------:|:--------:|:---------:|
|stdev|[0-∞]|[**all**, low, high]| - |
|z_score|[0-∞]|[**all**, low, high]| - |
|mad|[0-∞]|[**all**, low, high]| - |
|lof|[0-100]|[**low**, high]| [0-∞] |
|lof_stdev|[0-∞]|[**low**, high]| [0-∞] |
|less_than_sensitivity|[0-∞]| - | - |
|pct_of_avg_value|[0-100]|[low, high]| - |
|trigger_all| - | - | - |

# Metrics
Metrics are passed as an array.

Each metric will be apply to the corresponding column
```yaml
models:
	-	name: The model name
		sql_query: SELECT name, gain, loss, total 
		metrics: [str, int, int, 'python_eval(row[1] - row[2])']
```
Availables metrics:
- python_eval
	- Expl: 'python_eval(row[0] + row[1] * prev_row[3])'
	- You have access to
		- row: current row (an array)
		- prev_row: previous row
	- Return None if you want to ignore the current row
- b64_encoded: return the biggest B64 valid word
- b64_encoded_len: return the length of the biggest B64 valid word
- b64_decoded: take the biggest B64 valid word, and decode it
- str: convert to string
- int: convert to in
- float: convert to float
- hour
	- if a date, return the hour attribute
	- if an int, convert it to date (as a timestamp) and return the hour

# Plotting
In the model configuration, you can choose if you want to plot graph
```
models:
	- name: My model
	  plotting:
            enable: True
            output: plots
```

Then, you can visualise them on a website
> cd website
> 
> python3 index.py
 