# Example of a SQL query in ES
```
POST /_xpack/sql/translate?format=txt
{
  "query": """
  SELECT LogHost,LogonID,EventID,
         MIN(Time), MAX(Time)
  FROM host_events
  WHERE (EventID=4624 OR EventID=4634)
    AND LogonID IS NOT NULL
  GROUP BY LogonID,LogHost,EventID
  """
}
```

# Terms across_aggregator | Rare process

```
POST /_xpack/sql?format=txt
{
  "query": """
  SELECT COUNT(DISTINCT meta.hostname), 
  COUNT(*), OsqueryFilter.name
  FROM nviso_events
  WHERE OsqueryFilter.name IS NOT NULL
  GROUP BY OsqueryFilter.name
  """
}
```

# Terms within_aggregator | Rare parent process
bucket=OsqueryFilter.name
```
POST /_xpack/sql?format=txt
{
  "query": """
  SELECT COUNT(*) AS n, OsqueryFilter.name, OsqueryFilter.parentname
  FROM nviso_events
  WHERE OsqueryFilter.name IS NOT NULL
        AND meta.command.name LIKE 'get_all_processes_enriched'
  GROUP BY OsqueryFilter.name, OsqueryFilter.parentname
  ORDER BY OsqueryFilter.name
  LIMIT 15
  """
}
```

# Metrics | B64 encoded cmd
```
POST /_xpack/sql?format=txt
{
  "query": """
  SELECT SUBSTRING(OsqueryFilter.cmdline, 0, 80) AS cmdline, OsqueryFilter.name AS process_name
  FROM nviso_events
  WHERE OsqueryFilter.cmdline IS NOT NULL
  ORDER BY OsqueryFilter.name
  LIMIT 30
  """
}
```
bucket=OsqueryFilter.name
metric_cmdline=b64_encoded_string

[...]

# Itemlife | NVISO duration
```
POST /_xpack/sql?format=txt
{
  "query": """
  SELECT meta.hostname,
  MIN(timestamp) AS Start,
  MAX(timestamp) AS End
  FROM nviso_events
  GROUP BY meta.hostname, meta.logged_in_users_details.time
  LIMIT 15
  """
}
```

# Duration model | Bruteforce users sessions
```
POST /_xpack/sql?format=txt
{
  "query": """
  SELECT LogHost, UserName,
  MAX(Time) - MIN(Time) AS Duration,
  COUNT(LogonID) AS Attempts,
  (COUNT(LogonID) - 1) / (MAX(Time) - MIN(Time) + 1) AS AttemptsPerSecond
  FROM host_events_logon_failed
  WHERE EventID=4625 AND LogonID IS NOT NULL
  GROUP BY LogHost, UserName
  LIMIT 15
  """
}
```


# Duration model | Users sessions duration
```
POST /_xpack/sql?format=txt
{
  "query": """
    SELECT LogHost, LogonID,
    CAST(EventID=4624 AS INT) * Time AS Start,
    CAST(EventID=4634 AS INT) * Time AS End,
    (EventID=4624) AS IsStart
    FROM host_events
    WHERE (EventID=4624 OR EventID=4634)
          AND LogonID IS NOT NULL
    ORDER BY LogHost, LogonID, not IsStart
    LIMIT 15
  """
}
```

# Metrics
- numeric field
- hex decoded length
- b64 decoded length
- regex_len<regex>
- regex_count<regex>
- Date
  - Hour of the day
  - Day of the week
- python_eval(python code) !
  -> Expl: python_eval((cols[1] + math.cos(cols[0])) * cols[2])
  -> Expl: python_eval(cols[0] - prev_cols[0])
  -> Expl: python_eval(None if not cols[0] % 2 else cols[0])
  -> return "None" to skip the row
  -> you can access to the currant row with the variable "cols"
  -> you can access to the previous row with the variable "prev_cols"


# Parameter example | Users sessions duration

sql_query=SELECT LogHost, LogonID, 
  MIN(Time) AS Start, MAX(Time) AS End,
  -- Drop if unknow end or unknow start
  COUNT(DISTINCT EventID) as nEventID
  FROM host_events
  WHERE (EventID=4624 OR EventID=4634)
        AND LogonID IS NOT NULL
  GROUP BY LogHost, LogonID
  HAVING nEventID >= 2
  ORDER BY LogHost, LogonID
  LIMIT 15

bucket=LogHost,LogonID

metric_0=str
metric_1=str
metric_2=python_eval(cols[2].hour())
metric_3=str

target=2

outlier_reason=Strange start hour
outlier_summary=LogHost: {0} LogonID: {1} Hour = {2}
