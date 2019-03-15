
# ee-outliers

```
                               __  ___
  ___  ___        ____  __  __/ /_/ (_)__  __________
 / _ \/ _ \______/ __ \/ / / / __/ / / _ \/ ___/ ___/
/  __/  __/_____/ /_/ / /_/ / /_/ / /  __/ /  (__  )
\___/\___/      \____/\__,_/\__/_/_/\___/_/  /____/

Open-source framework to detect outliers in Elasticsearch events
Developed by NVISO Labs (https://blog.nviso.be - https://twitter.com/NVISO_Labs)
```

<p align="center">
<img alt="Detecting beaconing TLS connections using ee-outliers" src="https://forever.daanraman.com/screenshots/Beaconing%20detection.png?raw=true" width="650"/><br/>
<i>Detecting beaconing TLS connections using ee-outliers</i>
</p>

## Introduction

ee-outliers is a framework to detect outliers in events stored in an Elasticsearch cluster.
The framework was developed for the purpose of detecting anomalies in security events, however it could just as well be used for the detection of outliers in other types of data.


The framework makes use of statistical models that are easily defined by the user in a configuration file. In case the models detect an outlier, the relevant Elasticsearch events are enriched with additional outlier fields. These fields can then be dashboarded and visualized using the tools of your choice (Kibana or Grafana for example).

The possibilities of the type of anomalies you can spot using ee-outliers is virtually limitless. A few examples of types of outliers we have detected ourselves using ee-outliers during threat hunting activities include:

-	Detect beaconing (DNS, TLS, HTTP, etc.)
-	Detect geographical improbable activity
-	Detect obfuscated & suspicious command execution
-	Detect fileless malware execution
-	Detect malicious authentication events
-	Detect processes with suspicious outbound connectivity
-	Detect malicious persistence mechanisms (scheduled tasks, auto-runs, etc.)
-	Detect fraud is credit cards transactions
-	…

Checkout the screenshots at the end of this readme for a few examples.
Continue reading if you would like to get started with outlier detection in Elasticsearch yourself!

## Core features
- Create your own custom outlier detection use cases specifically for your own needs
- Send automatic e-mail notifications in case one of your outlier use cases hit
- Automatic tagging of asset fields to quickly spot the most interesting assets to investigate
- Fine-grained control over which historical events are checked for outliers
- ...and much more!

## Requirements
- Docker to build and run ee-outliers
- Internet connectivity to build ee-outliers (internet is not required to run ee-outliers)

## Getting started

### Configuring ee-outliers

ee-outliers makes use of a single configuration file, in which both technical parameters (such as connectivity with your Elasticsearch cluster, logging, etc.) are defined as well as the detection use cases.

An example configuration file with all required configuration sections and parameters, along with an explanation, can be found in ``defaults/outliers.conf``. We recommend starting from this file when running ee-outliers yourself.
Continue reading for all the details on how to define your own outlier detection use cases.

### Running in interactive mode
In this mode, ee-outliers will run once and finish. This is the ideal run mode to use when testing ee-outliers straight from the command line.

Running ee-outliers in interactive mode:

```
# Build the image
docker build -t "outliers-dev" .

# Allow docker to spawn GUI windows
xhost +local:docker

# Run the image
docker run --network="host" -v "$PWD/defaults:/mappedvolumes/config" -v "$PWD/shared:/shared" -v "$PWD/plots:/plots" -v "$PWD/defaults:/defaults" -v "$PWD/app:/app" -i  outliers-dev:latest python3 outliers.py interactive --config /mappedvolumes/config/outliers.conf
```

### Running in daemon mode
In this mode, ee-outliers will continuously run based on a cron schedule defined in the outliers configuration file.

Example from the default configuration file which will run ee-outliers at 00:00 each night:

```
[daemon]
schedule=0 0 * * *
```

Running ee-outliers in daemon mode:

```
# Build the image
docker build -t "outliers-dev" .

# Allow docker to spawn windows
xhost +local:docker

# Run the image
docker run --network="host" -v /tmp/.X11-unix:/tmp/.X11-unix -v "$PWD/shared:/shared" -e DISPLAY -v "$PWD/defaults:/mappedvolumes/config" -i  outliers-dev:latest python3 outliers.py interactive --config /mappedvolumes/config/outliers.conf
```

### Customizing your Docker run parameters

The following modifications might need to be made to the above commands for your specific situation:
- The name of the docker network through which the Elasticsearch cluster is reachable (``--network``)
- The mapped volumes so that your configuration file can be found (``-v``). By default, the default configuration file in ``/defaults`` is mapped to ``/mappedvolumes/config``
- The path of the configuration file (``--config``)

## Configuring outlier detection models

The different detection use cases can be configured in the configuration file, passed to ee-outliers. In this section we discuss all the different detection mechanisms that are available, and the options they provide to the analyst.

The different types of detection models that can be configured are listed below.

- **simplequery models**: this model will simply run an Elasticsearch query and tag all the matching events as outliers. No additional statistical analysis is done. Example use case: tag all the events that contain the string "mimikatz" as outliers.

- **metrics models**: the metrics model looks for outliers based on a calculated metric of a specific field of events. These metrics include the length of a field, its entropy, and more. Example use case: tag all events that represent Windows processes that were launched using a high number of base64 encoded parameters in order to detect obfuscated fileless malware.

- **terms models**:  the terms model looks for outliers by calculting rare combinations of a certain field(s) in combination with other field(s). Example use case: tag all events that represent Windows network processes that are rarely observed across all reporting endpoints in order to detect C2 phone home activity.

- **word2vec models (BETA)**: the word2vec model is the first Machine Learning model defined in ee-outliers. It allows the analyst to train a model based on a set of features that are expected to appear in the same context. After initial training, the model is then able to spot anomalies in unexected combinations of the trained features. Example use case: train a model to learn which usernames, workstations and user roles are expected to appear together in order to alert on breached Windows accounts that are used to laterally move in the network.

- **autoencoder**: this model used the reconstruction score of the autoencoder to detect outliers. Outliers will have a bigger reconstruction error ! (works only for numeric fields).

- **decision tree**: this model is not useful to detect outlier, but can be used to know which feature is the most linked to another one.

- **sentence prediction**: this model use neural network to detect abnormal sentences. The sentences will be split into words, and words will be one hot encoded. Then the NN will be trained to predict the sentence from the label. We use the prediction error to detect abnormal sentences.

- **string K-Means**: this model will one hot encode words, and then apply K-Means on these vectors.

- **duration**: this model measures the duration between two events (and also the start moment and the end moment), and uses this duration as metric for outlier detection. They are two types of outliers detection, within aggregator and across aggregator.
	- Within aggregator metrics
		- start_minute
		- start_hour
		- start_day
		- start_month
		- start_year
		- start_timestamp
		- end_minute
		- end_hour
		- end_day
		- end_month
		- end_year
		- end_timestamp
		- duration
		- log_duration
	- Across aggregator metrics
		- number_of_events
		- events_per_minute
		- max_duration
		- min_duration
		- mean_duration

### General model parameters
**es_query_filter**

Each model starts with an Elasticsearch query which selects which events the model should consider for analysis.
The best way of testing if the query is valid is by copy-pasting it from a working Kibana query.

**trigger_method**, **trigger_sensitivity** and **n_neighbors**

Possible ``trigger_method`` values:

- ``mad``: Median Average Deviation. ``trigger_sensitivity`` defines the total number of deviations ``[0-inf]``
- ``mad_low``: Trigger only on low value
- ``mad_high``: Trigger only on high value
- ``z_score``: Similar to MAD. ``trigger_sensitivity`` defines the total number of deviations ``[0-inf]``.
- ``stdev``: Standard Deviation. ``trigger_sensitivity`` defines the total number of deviations ``[0-inf]``.
- ``stdev_low``: Trigger only on low value
- ``stdev_high``: Trigger only on high value
- ``lof``: Local Outliers Factor. ``trigger_sensitivity`` percantage of outliers in data ``[0-100]``. ``n_neighbors``: Minimal size of a cluster ``[1-inf]``.
- ``lof_stdev``: Apply STDEV on LOF. ``trigger_sensitivity`` defines the total number of deviations ``[0-inf]``. ``n_neighbors``: Minimal size of a cluster ``[1-inf]``.
- ``isolation_forest``: Isolation forest. ``trigger_sensitivity`` defines the total number of deviations ``[0-inf]``.
- ``less_than_sensitivity``: Trigger everything less than ``trigger_sensitivity``.
- ``pct_of_avg_value_low``: percentage of average value, trigger only on low value. ``trigger_sensitivity`` ranges from ``0-100``.
- ``pct_of_avg_value_high``: percentage of average value, trigger only on high value. ``trigger_sensitivity`` ranges from ``0-100``.

**outlier_type**

Freetext field which will be added to the outlier event as new field named ``outliers.outlier_type``.
For example: encoded commands

**outlier_reason**

Freetext field which will be added to the outlier event as new field named ``outliers.reason``.
For example: base64 encoded command line arguments

**outlier_summary**

Freetext field which will be added to the outlier event as new field named ``outliers.summary``.
For example: base64 encoded command line arguments for process {OsqueryFilter.name}

**should_notify**

Switch to enable / disable notifications for the model

**plot_graph**
Plot outliers and normal data. If we will plot too many graphs, they are saved in ``/shared``.

## simplequery models

This model will simply run an Elasticsearch query and tag all the matching events as outliers. No additional statistical analysis is done. Example use case: tag all the events that represent hidden powershell processes as outliers.

Each metrics model section in the configuration file should be prefixed by ``simplequery_``.

**Example model**
```
#######################################################
# SIMPLEQUERY - POWERSHELL EXECUTION IN HIDDEN WINDOW #
#######################################################
[simplequery_powershell_execution_hidden_window]
es_query_filter=tags:endpoint AND "powershell.exe" AND (OsqueryFilter.cmdline:"-W hidden" OR OsqueryFilter.cmdline:"-WindowStyle Hidden")

outlier_type=powershell
outlier_reason=powershell execution in hidden window
outlier_summary=powershell execution in hidden window

run_model=1
test_model=0
```

**Parameters**

All required options are visible in the example, and are required.

## metrics models

The metrics model looks for outliers based on a calculated metric of a specific field of events. These metrics include the length of a field, its entropy, and more. Example use case: tag all events that represent Windows processes that were launched using a high number of base64 encoded parameters in order to detect obfuscated fileless malware.

Each metrics model section in the configuration file should be prefixed by ``metrics_``.

**Example model**

```
###################################################
# METRICS - BASE64 ENCODED COMMAND LINE ARGUMENTS #
###################################################
[metrics_base64_encoded_cmdline]
es_query_filter=_exists_:OsqueryFilter.name AND _exists_:OsqueryFilter.cmdline

aggregator=OsqueryFilter.name
target=OsqueryFilter.cmdline

metric=base64_encoded_length

trigger_method=mad
trigger_sensitivity=3

outlier_type=encoded commands
outlier_reason=base64 encoded command line arguments
outlier_summary=base64 encoded command line arguments for process {OsqueryFilter.name} - {OsqueryFilter.cmdline}

batch_size=50000
```

**How it works**

The metrics model looks for outliers based on a calculated metric of a specific field of events. These metrics include the following:
- ``numerical_value``: use the numerical value of the target field as metric. Example: numerical_value("2") => 2
- ``length``: use the target field length as metric. Example: length("outliers") => 8
- ``entropy``: use the entropy of the field as metric. Example: entropy("houston") => 2.5216406363433186
- ``hex_encoded_length``: calculate total length of hexadecimal encoded substrings in the target and use this as metric.
- ``base64_encoded_length``: calculate total length of base64 encoded substrings in the target and use this as metric. Example: base64_encoded_length("houston we have a cHJvYmxlbQ==") => base64_decoded_string: problem, base64_encoded_length: 7
- ``regex_len_<regex_here>``: extract the first match and return its length. For example, to extract the URL length, we can write ``regex_len_http(s?):\/\/[a-zA-Z0-9\.\/-]+``. The model will extract the URL from the target value and use its length as metric. Example: ("why don't we go http://www.dance.com") => extracted_urls_length: 20, extracted regex: http://www.dance.com
- ``regex_count_match_<regex_here>``: count the number of matches and use it as a metric. For example, you can extract the number of URLs in a text ``regex_count_match_http(s?):\/\/[a-zA-Z0-9\.\/-]+``.
Example: "Do you prefer https://www.newbiecontest.org or https://www.root-me.org" => 2 URLs
- ``regex_sum_len_``: extract all matches and return the total length.
Example: ``regex_count_match_http(s?):\/\/[a-zA-Z0-9\.\/-]+``("Do you prefer https://www.newbiecontest.org or https://www.root-me.org") => 52

The metrics model works as following:

 1. The model starts by taking into account all the events defined in the ``es_query_filter``
 parameter. This should be a valid Elasticsearch query. The best way of testing if the query is valid is by copy-pasting it from a working Kibana query.
 
 2. The model then calculates the selected metric (``base64_encoded_length`` in the example) for each encountered value of the ``target`` field (``OsqueryFilter.cmdline`` in the example). These values are the checked for outliers in buckets defined by the values of the ``aggregator`` field (``OsqueryFilter.name`` in the example). Sensitivity for deciding if an event is an outlier is done based on the ``trigger_method`` (MAD or Mean Average Deviation in this case) and the ``trigger_sensitivity`` (in this case 3 standard deviations).

3. Outlier events are tagged with a range of new fields, all prefixed with ``outliers.<outlier_field_name>``. 

## terms models

The terms model looks for outliers by calculting rare combinations of a certain field(s) in combination with other field(s). Example use case: tag all events that represent Windows network processes that are rarely observed across all reporting endpoints in order to detect C2 phone home activity.

Each metrics model section in the configuration file should be prefixed by ``terms_``.

**Example model**
```
##########################
# TERMS - RARE PROCESSES #
##########################
[terms_rare_processes]
es_query_filter=meta.command.name: "get_all_processes_enriched"

aggregator=OsqueryFilter.name
target=meta.hostname

target_count_method=across_aggregators
trigger_method=mad_low
trigger_sensitivity=1

outlier_type=Rare process
outlier_reason=Rare process
outlier_summary=Rare process: {OsqueryFilter.name}

batch_size=10000
```

**How it works**

The terms model looks for outliers by calculting rare combinations of a certain field(s) in combination with other field(s).It works as following:

1. The model starts by taking into account all the events defined in the ``es_query_filter`` parameter. This should be a valid Elasticsearch query. The best way of testing if the query is valid is by copy-pasting it from a working Kibana query.
 
2. The model will then count all unique instances of the ``target`` field, for each individual ``aggregator``field. In the example above, the ``OsqueryFilter.name`` field represents the process name. The target field ``meta.hostname`` represents the total number of hosts that are observed for that specific aggregator (meaning: how many hosts are observed to be running that process name which is communicating with the outside world?).

3. Outlier events are tagged with a range of new fields, all prefixed with ``outliers.<outlier_field_name>``. 

The ``target_count_method`` parameter can be used to define if the analysis should be performed across all values of the aggregator at the same time, or for each value of the aggregator separately. 


## duration model
The duration model measures the duration between two events and uses it to detect outliers.

This model can perform within aggregator analysis or across aggregator analysis, depending on the ``target`` parameter.

Here are the possible values for ``target``,
- Within aggregator metrics
	- start_minute
	- start_hour
	- start_day
	- start_month
	- start_year
	- start_timestamp
	- end_minute
	- end_hour
	- end_day
	- end_month
	- end_year
	- end_timestamp
	- duration
	- log_duration
- Across aggregator metrics
	- number_of_events
	- events_per_minute
	- max_duration
	- min_duration
	- mean_duration

**Example model**
```
###############################
# DURATION - Abnormal session #
###############################
[duration_abnormal_session_duration]
es_query_filter=(EventID:4624 OR EventID:4634) AND _exists_:LogonID AND _exists_:LogHost

aggregator=LogonType
fields_value_to_correlate=LogonID,LogHost

start_end_field=EventID
# Logon event
start_value=4624
# Logoff event
end_value=4634

outlier_reason=Strange session duration
outlier_type=Strange session duration
outlier_summary={LogonType} - {UserName} - Session duration: <target>

batch_eval_size=20000

target=log_duration

trigger_method=lof_stdev
trigger_sensitivity=2
```

**How it works**
The parameter ``fields_value_to_correlate`` can be used to determine which ``start event`` corresponds to which ``end event``. Here we use the session ID and host name.

The parameter ``start_end_field`` specifies the field to be used to identify whether the event is a ``start event`` or an ``end event`` (with ``start_value`` and ``end_value``).

The ``target`` parameter defines the value to be extracted (``duration``, ``start_hour``,....).
It will also define whether the analysis is done within the aggregator or at the aggregator level.

## autoencoder
Autoencoder is a type of neural network which reconstructs the input.

We use the reconstruction error as a score to detect outliers (outlier will have a bigger reconstruction score).

Actually, this model works only with numeric fields !

![autoencoder_image](https://cdn-images-1.medium.com/max/1600/1*iDcAplzGhttLcYI56MIMxQ.png)

**Example model**
```
############################################
# AUTOENCODER - Credicards fraud detection #
############################################
[autoencoder]

fields=V1,V2,V3,V4,V5,V6,V7,V8,V9,V10,V11,V12,V13,V14,V15,V16,V17,V18,V19,V20,V21,V22,V23,V24,V25,V26,V27,V28

# Show these fields if the item is an anomaly
output_fields=Class,Amount
number_of_elements_displayed=30 

outlier_reason=Fraud
outlier_type=Fraud
outlier_summary=This transaction seems to be a fraud... Pay attention !

# Network configuration
layers=28,50,10,50,28
epochs=2

# To test the model, if the data is labelised (1: Outlier, 0: Normal)
test_the_model=1
test_label=Class
number_of_points_plotted=1000
```

**How it works**
The ``fields`` parameter defines which fields we have to put in the input of the neural network.

The ``output_fields`` define which fields we will show if the document is abnormal.

You can change the configuration of the neural network with the parameter ``layers``, and also the number of epochs for training with the parameter ``epochs``.

If ``test_the_model`` is set to 1, that means that we have a label, we know which item is an outlier, and so we want to test our model. The ``test_label`` parameter defines which field is the label (1 for outlier, 0 for normal), and you can choose how many points you want in your graph with ``number_of_points_plotted``.

## Whitelisting

ee-outliers provides support for whitelisting of certain outliers. By whitelisting an outlier, you prevent them from being tagged and stored in Elasticsearch.

For events that have already been enriched and that match a whitelist later, the ``es_wipe_all_whitelisted_outliers`` flag can be used in order to remove them.
The whitelist will then be checked for hits periodically as part of the housekeeping work, as defined in the parameter ``housekeeping_interval_seconds``.

Two different whitelists are defined in the configuration file:

### Literals whitelist

This whitelist will only hit for outlier events that contain an exact whitelisted string as one of its event field values.
The whitelist is checked against all the event fields, not only the outlier fields!

Example:
```
[whitelist_literals]
slack_connection=rare outbound connection: Slack.exe
```


### Regular expression whitelist

This whitelist will hit for all outlier events that contain a regular expression match against one of its event field values.
The whitelist is checked against all the event fields, not only the outlier fields!

Example:
```
[whitelist_regexps]
scheduled_task_user_specific_2=^.*rare scheduled task:.*-.*-.*-.*-.*$
autorun_user_specific=^.*rare autorun:.*-.*-.*-.*-.*$
```

## Developing and debugging ee-outliers

ee-outliers supports additional run modes (in addition to interactive and daemon) that can be useful for developing and debugging purposes.

### Running in test mode
In this mode, ee-outliers will run all unit tests and finish, providing feedback on the test results.

Running outliers in tests mode:

```
# Build the image
docker build -t "outliers-dev" .

# Run the image
docker run -v "$PWD/defaults:/mappedvolumes/config" -i outliers-dev:latest python3 outliers.py tests --config /mappedvolumes/config/outliers.conf
```

### Running in profiler mode
In this mode, ee-outliers will run a performance profile (``py-spy``) in order to give feedback to which methods are using more or less CPU and memory. This is especially useful for developers of ee-outliers.

Running outliers in profiler mode:

```
# Build the image
docker build -t "outliers-dev" .

# Run the image
docker run --cap-add SYS_PTRACE -t --network=sensor_network -v "$PWD/defaults:/mappedvolumes/config" -i  outliers-dev:latest py-spy -- python3 outliers.py interactive --config /mappedvolumes/config/outliers.conf
```

### Checking code style and PEP8 compliance
In this mode, flake8 is used to check potential issues with style and PEP8.

Running outliers in this mode:

```
# Build the image
docker build -t "outliers-dev" .

# Run the image
docker run -v "$PWD/defaults:/mappedvolumes/config" -i outliers-dev:latest flake8 /app
```

You can also provide additional arguments to flake8, for example to ignore certain checks (such as the one around long lines):

```
docker run -v "$PWD/defaults:/mappedvolumes/config" -i outliers-dev:latest flake8 /app "--ignore=E501"
```

## Screenshots

<p align="center"> 
<img alt="Detecting beaconing TLS connections using ee-outliers" src="https://forever.daanraman.com/screenshots/Beaconing%20detection.png?raw=true" width="650"/><br/>
<i>Detecting beaconing TLS connections using ee-outliers</i>
</p>
<br/><br/>  
<p align="center"> 
<img alt="Configured use case to detect beaconing TLS connections" src="https://forever.daanraman.com/screenshots/Configuration%20use%20case.png?raw=true" width="450"/><br/>
<i>Configured use case to detect beaconing TLS connections</i>
</p>
<br/><br/>
<p align="center"> 
<img alt="Detected outlier events are enriched with new fields in Elasticsearch" src="https://forever.daanraman.com/screenshots/Enriched%20outlier%20event%202.png?raw=true" width="650"/><br/>
<i>Detected outlier events are enriched with new fields in Elasticsearch</i>
</p>

## License

See the [LICENSE](LICENSE) file for details

## Contact

You can reach out to the developers of ee-outliers by creating an issue in github.
For any other communication, you can reach out by sending us an e-mail at research@nviso.be.

Thank you for using ee-outliers and we look forward to your feedback! 🐀
