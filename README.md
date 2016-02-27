SuperFlyer United Airlines Utility
================================

- Search united.com for fare class availability, including award and upgrade buckets.
- Set a cron job to check for availability and send yourself email when seats become available.
- Mileage run option allows querying of multiple segments over a date range
- Also includes a web interface for interactive querying.

This documentation is intentionally sparse, so use at your own risk.

Setup
----------------------
1. Get a united.com account and set it to Expert Mode.
2. Get a gmail account.
3. Enter the account parameters in ual/ual.config (not included in this repo)
4. Enter your alerts in alerts/alert_defs.txt.
5. Enter your aggregate alerts in alerts/agg_alert_defs.txt (to search the same route over a range of days).
6. Enter your mileage run alerts in alerts/mr_search.txt (to search a multi-segment route over a range of days).
7. Run <code>python ual.py --help</code> to see command-line options.
8. Run <code>python ual_webserver --help</code> to see options for the webserver.  The webserver runs on port 8080 by default.

Notes
----------------------
- Fare class descriptions can be found here: http://cwsi.net/united.htm
- For classes O, I, R, X there is separate inventory for elites (ON/IN/RN/XN).  The tool searches both at once: a search for I returning I37 means I=3, IN=7.
