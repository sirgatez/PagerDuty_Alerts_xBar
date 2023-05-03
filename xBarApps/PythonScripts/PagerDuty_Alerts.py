#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
import json
import os
import pprint
import pytz
import requests
import subprocess
from pytz import timezone
from sys import platform, version_info, modules, stderr
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Support Darwin and Linux to post notifications without failing to load.
# If library is unavailable continue silently. Feature not required.
if platform == "darwin":
    try:
        import Foundation
        import objc
        import AppKit
        NSUserNotification = objc.lookUpClass("NSUserNotification")
        NSUserNotificationCenter = objc.lookUpClass("NSUserNotificationCenter")
    except Exception:
        # If we fail to load we won't do popup notifications.
        pass
elif platform == "linux2":
    try:
        # If we fail to load we won't do popup notifications.
        from gi.repository import Notify
    except Exception:
        pass
else:
    pass

# Pretty Printer for debugging
pp = pprint.PrettyPrinter(indent=4)

# Configure default retry count on error.
rs = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
rs.mount("https://", HTTPAdapter(max_retries=retries))

APP = os.path.basename(__file__).split(".")[0]
ROOT = "/".join([os.path.dirname(os.path.abspath(__file__)), "config"])


def notify(title, subtitle, info_text, sound=False, userinfo={}):
    if platform == "darwin":
        if "Foundation" in modules:
            notification = NSUserNotification.alloc().init()
            notification.setTitle_(title)
            notification.setSubtitle_(subtitle)
            notification.setInformativeText_(info_text)
            # Unused by default, pass in userinfo to re-enable
            if userinfo:
                # This does not work for some reason. Keeping until we can figure out why.
                # notification.setUserInfo_({"action": "open_url", "value": "https://www.google.com"})
                notification.setUserInfo_(userinfo)
                notification.setHasActionButton_(True)
                notification.setActionButtonTitle_("Open URL")
            else:
                # Display an Ok button for now. Clicking clears the popup. It does not ack the alert.
                notification.setHasActionButton_(True)
                notification.setActionButtonTitle_("Ok")
            if sound:
                notification.setSoundName_("NSUserNotificationDefaultSoundName")
            NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)
        else:
            pass
    # osascript can also be used to post a notification by executing the following.
    # osascript -e 'display notification "Lorem ipsum dolor sit amet" with title "Title" sound name "Hero"'
    elif platform == "linux2" and "gi" in modules:
        Notify.init(notification)
        notification = Notify.Notification.new(notification, msg)  # Add third arg icon if you have file
        notification.show()
    else:
        # ToDo: Add support for notifications on "win32"
        pass


def play_alert_sound(soundfile):
    if os.path.isfile(soundfile):
        try:
            if platform == "darwin":
                subprocess.check_output(["afplay", soundfile])
            elif platform == "linux2":
                # sudo apt install sox libsox-fmt-mp3
                subprocess.check_output(["play", soundfile])
            else:
                # ToDo: Add support for notifications on "win32"
                pass
        except Exception:
            # Not notable, if we fail sound simply doesn't play.
            pass


def fetch_pagerduty_incidents(dev_token, user_id):
    return requests.get("https://api.pagerduty.com/incidents"
                        "?user_ids[]={0}&limit=50&statuses[]=triggered&statuses[]=acknowledged".format(user_id),
                        headers={"Accept": "application/vnd.pagerduty+json;version=2",
                                 "Authorization": "Token token={0}".format(dev_token),
                                 "Content-Type": "application/json"})


def fetch_pagerduty_oncall_schedule(dev_token, user_id):
    return requests.get("https://api.pagerduty.com/oncalls?user_ids[]={0}".format(user_id),
                        headers={"Accept": "application/vnd.pagerduty+json;version=2",
                                 "Authorization": "Token token={0}".format(dev_token),
                                 "Content-Type": "application/json"})


def load_last_pagerduty_reply(filename):
    return json.loads(filename)


def save_last_pagerduty_reply(filename, json_data):
    with open(filename, "w") as file_handle:
        json.dump(json_data, file_handle, ensure_ascii=False)


def get_incidents_from_json(json_data):
    incidents = dict()
    if "incidents" in json_data:
        for pd_incident in json_data["incidents"]:
            incidents[pd_incident["incident_number"]] = {
                "created_at": pd_incident["created_at"],
                "last_status_change_at": pd_incident["last_status_change_at"],
                "status": pd_incident["status"].lower(),
                "urgency": pd_incident["urgency"].lower(),
                "html_url": pd_incident["html_url"],
                "title": pd_incident["title"],
            }
    return incidents


def print_xbar_incidents(incidents):
    print("Triggered | color='{0}'".format(colors["menu"]))
    for incident in incidents:
        if pd_incidents[incident]["status"] == "triggered":
            print("-- {0} - {1}: {2} | color='{3}' href='{4}'".format(
                incident, incidents[incident]["urgency"], incidents[incident]["title"],
                colors[incidents[incident]["urgency"]], incidents[incident]["html_url"]))

    print("Acknowledged | color='{0}'".format(colors["menu"]))
    for incident in incidents:
        if incidents[incident]["status"] == "acknowledged":
            print("-- {0} - {1}: {2} | color='{3}' href='{4}'".format(
                incident, incidents[incident]["urgency"], incidents[incident]["title"],
                colors[incidents[incident]["urgency"]], incidents[incident]["html_url"]))


def notify_incidents(incidents, incidents_last, alert_popup, alert_sound):
    unacked = False
    unacked_last = False
    # notify("Test message", "Subtitle", "This message should appear instantly, with a sound", sound=True)
    if pagerduty_json != pagerduty_json_last and pagerduty_json != "":
        for incident in incidents:
            if incidents[incident]["status"] == "triggered" and incidents[incident]["urgency"] == "high":
                unacked = True

            if incident in pd_incidents_last:
                if incidents[incident]["status"] != incidents_last[incident]["status"]:
                    if alert_popup:
                        notify("Incident {0}: {1} -> {2}".format(
                            incident, incidents_last[incident]["status"], incidents[incident]["status"]), "",
                            "Incident #{0} changed from {1} to {2}.\nUrgency: {3}\nCreated: {4}\nUpdated: {5}\n\n{6}".format(
                                incident, incidents_last[incident]["status"], incidents[incident]["status"],
                                incidents[incident]["urgency"], incidents[incident]["created_at"],
                                incidents[incident]["last_status_change_at"], incidents[incident]["title"]
                            ), sound=alert_sound)
            else:
                # check if in old list
                if incident not in pd_incidents_last:
                    if incidents[incident]["status"] == "triggered" and incidents[incident]["urgency"] == "high":
                        if alert_popup:
                            notify("New Incident triggered: {0}".format(incident), "",
                                   "Incident #{0} triggered\nUrgency: {1}\nCreated: {2}\nUpdated: {5}\n\n{3}".format(
                                    incident, pd_incidents[incident]["status"],
                                    incidents[incident]["urgency"], incidents[incident]["created_at"],
                                    incidents[incident]["last_status_change_at"], incidents[incident]["title"]
                                ), sound=alert_sound)

        for incident in pd_incidents_last:
            if pd_incidents_last[incident]["status"] == "triggered" and \
                    incidents_last[incident]["urgency"] == "high":
                unacked_last = True

            if incident not in pd_incidents:
                if alert_popup:
                    notify("Incident no longer active: {0}".format(incident), "",
                           "Incident #{0} no longer active:\nUrgency: {3}\nCreated: {4}\nUpdated: {5}\n\n{6}".format(
                               incident, pd_incidents_last[incident]["status"], pd_incidents[incident]["status"],
                               pd_incidents[incident]["urgency"], pd_incidents[incident]["created_at"],
                               pd_incidents[incident]["last_status_change_at"], pd_incidents[incident]["title"]
                           ), sound=alert_sound)

    # if you only want 1 audible alert until an ack use "unacked and not unacked_last" not unacked
    # return unacked  # One alert per refresh until all are ACK
    return unacked and not unacked_last  # One audible alert until ACK


def get_oncall_status_from_json(json_data, local_time_fmt, local_time_zone):
    pagerduty_format = "%Y-%m-%dT%H:%M:%SZ"  # PagerDuty time format
    response = {
        "active": False,
        "utc_raw_start": '',
        "utc_raw_end": '',
        "utc_fmt_start": '',
        "utc_fmt_end": '',
        "local_fmt_start": '',
        "local_fmt_end": '',
        "teams": dict()
    }

    for schedule in json_data["oncalls"]:
        if schedule["escalation_level"] == 1:
            utc_raw_start = datetime.strptime(schedule["start"], pagerduty_format)
            utc_raw_end = datetime.strptime(schedule["end"], pagerduty_format)
            response["teams"][schedule["schedule"]["id"]] = {
                "id": schedule["schedule"]["id"],
                "name": schedule["schedule"]["summary"],
                "utc_raw_start": utc_raw_start,
                "utc_raw_end": utc_raw_end,
                "utc_fmt_start": datetime.strptime(schedule["start"], pagerduty_format).strftime(local_time_fmt),
                "utc_fmt_end": datetime.strptime(schedule["end"], pagerduty_format).strftime(local_time_fmt),
                "local_fmt_start": get_local_time_from_utc(utc_raw_start, local_time_fmt, local_time_zone),
                "local_fmt_end": get_local_time_from_utc(utc_raw_end, local_time_fmt, local_time_zone)
            }

            start = datetime.strptime(schedule["start"], pagerduty_format)
            end = datetime.strptime(schedule["end"], pagerduty_format)
            if response["utc_raw_start"] == "" or response["utc_raw_end"] == '':
                response["utc_raw_start"] = start
                response["utc_raw_end"] = end
                response["active"] = True
            else:
                if start < response["utc_raw_start"]:
                    response["utc_raw_start"] = start
                if end > response["utc_raw_end"]:
                    response["utc_raw_end"] = end
            response["utc_fmt_start"] = response["utc_raw_start"].strftime(local_time_fmt)
            response["utc_fmt_end"] = response["utc_raw_end"].strftime(local_time_fmt)
            response["local_fmt_start"] = \
                get_local_time_from_utc(response["utc_raw_start"], local_time_fmt, local_time_zone)
            response["local_fmt_end"] = \
                get_local_time_from_utc(response["utc_raw_end"], local_time_fmt, local_time_zone)
    return response


def print_oncall_status_debug(response, local_time_fmt, local_time_zone):
    if response['active']:
        print()
        print("Original")
        print("Start UTC: {0}".format(response['utc_fmt_start']))
        print("End UTC:  {0}".format(response['utc_fmt_end']))
        print("Now:  {0}".format(datetime.utcnow().strftime(local_time_fmt)))
        print()
        print("Testing")

        print("Start PST: " + response['local_fmt_start'])
        print("End PST: " + response['local_fmt_end'])
        print("Now PST: " + get_local_time_from_utc(datetime.utcnow(), local_time_fmt, local_time_zone))

    if response['active'] and (response['utc_raw_start'] < datetime.utcnow() < response['utc_raw_end']):
        print("You are oncall")
    else:
        print("You are not oncall")


def print_xbar_oncall_status(response, pd_company, pd_user):
    user_url = "https://{0}.pagerduty.com/users/{1}/on-call/month".format(pd_company, pd_user)
    if "active" in response and response["active"]:
        if response['active'] and (response['utc_raw_start'] < datetime.utcnow() < response['utc_raw_end']):
            print("Status: Oncall ☎️ | color='{0}' href='{1}'".format(colors["menu"], user_url))
            print("-- Start: {0} | color='{1}'".format(response['local_fmt_start'], colors["info"]))
            print("--   End: {0} | color='{1}'".format(response['local_fmt_end'], colors["info"]))
            #print("-- Teams: | color='{0}'".format(colors["info"]))  # Looked better without this as a submenu
            print("--")
            for team in response["teams"]:
                team_url = "https://{0}.pagerduty.com/schedules/{1}".format(pd_company, team)
                print("-- {0} | color='{1}' href='{2}'".format(
                    response["teams"][team]["name"], colors["info"], team_url))
                print("---- {0} | color='{1}'".format(response["teams"][team]["local_fmt_start"], colors["info"]))
                print("---- {0} | color='{1}'".format(response["teams"][team]["local_fmt_end"], colors["info"]))
        return
    print("Status: OffCall 💤 | color='{0}' href='{1}'".format(colors["menu"], user_url))


def get_local_time_from_utc(utctime, date_format, time_zone):
    utc_dt = pytz.utc.localize(utctime)
    pst_tz = timezone(time_zone)
    pst_dt = pst_tz.normalize(utc_dt.astimezone(pst_tz))
    return pst_dt.strftime(date_format)


# Define colors globally for easy access.
colors = {"high": "#FFFF00", "low": "#8888FF", "menu": "#666666", "info": "#00CC00"}


if __name__ == '__main__':
    stale_data = False
    pagerduty_unacked = False
    pagerduty_unacked_last = False
    pagerduty_reply = ""
    pagerduty_json = ""
    pagerduty_json_last = ""
    error_msg = ""
    pagerduty_last_reply_file = "pagerduty_alerts.lastreply"  # Stored in same folder as script

    ################################
    ### Begin User Configuration ###
    ################################

    # Authentication and User Config
    PAGER_DUTY_COMPANY = "mycompany"  # mycompany.pagerduty.com
    PAGER_DUTY_TOKEN = "MyDevToken"  # Configure to your Dev Token
    PAGER_DUTY_USER = "MyUserID"  # Configure to your User ID.

    # Data formatting
    # PAGER_DUTY_DATE_FORMAT = "%m/%d/%Y %H:%M:%S %Z"  # Local military time format
    PAGER_DUTY_DATE_FORMAT = "%m/%d/%Y %I:%M:%S%p %Z"  # Local standard time format
    PAGER_DUTY_TIMEZONE = "US/Pacific"

    # Popups / Alert Sounds
    PAGER_DUTY_POPUP_ALERTS = True  # Display popups alerts
    PAGER_DUTY_AUDIBLE_ALERTS = True  # Play alert sounds

    # Sound file to play when new alert is to triggered
    PAGER_DUTY_ALERT_SOUND = "{0}/my_alert_sound.mp3".format(os.environ["HOME"])
    # Check out https://freesound.org

    ##############################
    ### End User Configuration ###
    ##############################

    oncall_response = {"active": False}

    try:
        pagerduty_oncall_schedule = fetch_pagerduty_oncall_schedule(PAGER_DUTY_TOKEN, PAGER_DUTY_USER)
        code = str(pagerduty_oncall_schedule.status_code)[0:1]
        if code == '2':
            oncall_response = get_oncall_status_from_json(
                pagerduty_oncall_schedule.json(), PAGER_DUTY_DATE_FORMAT, PAGER_DUTY_TIMEZONE)
            # print_oncall_status_debug(oncall_response, PAGER_DUTY_DATE_FORMAT, PAGER_DUTY_TIMEZONE)
        elif code == "4":
            error_msg = "{0}: Unauthorized, please double check that your Dev Token is valid.".format(
                pagerduty_reply.status_code)
        elif code == "5":
            error_msg = "{0}: A 5xx server error occurred, please retry the request.".format(
                pagerduty_reply.status_code)
        else:
            error_msg = "{0}: An unknown error has occurred.".format(pagerduty_reply.status_code)
    except Exception:
        pass

    try:
        pagerduty_json_last = load_last_pagerduty_reply(pagerduty_last_reply_file)
    except Exception:
        # Error not notable to report. First run never has a last file.
        pass

    try:
        # Invalid user will not return an error, it just won't have any incidents.
        pagerduty_reply = fetch_pagerduty_incidents(PAGER_DUTY_TOKEN, PAGER_DUTY_USER)
        code = str(pagerduty_reply.status_code)[0:1]
        if code == "2":
            pagerduty_json = pagerduty_reply.json()
            save_last_pagerduty_reply(pagerduty_last_reply_file, pagerduty_json)
        else:
            if code == "4":
                error_msg = "{0}: Unauthorized, please double check that your Dev Token is valid.".format(
                    pagerduty_reply.status_code)
            elif code == "5":
                error_msg = "{0}: A 5xx server error occurred, please retry the request.".format(
                    pagerduty_reply.status_code)
            else:
                error_msg = "{0}: An unknown error has occurred.".format(pagerduty_reply.status_code)
            raise Exception("Unexpected response from server. Loading stale data.")
    except Exception:
        stale_data = True
        pagerduty_json = pagerduty_json_last  # Load last as current if failed to get current.

    pd_incidents = get_incidents_from_json(pagerduty_json)
    pd_incidents_last = get_incidents_from_json(pagerduty_json_last)

    pagerduty_unacked = notify_incidents(
        pd_incidents, pd_incidents_last, PAGER_DUTY_POPUP_ALERTS, PAGER_DUTY_AUDIBLE_ALERTS)

    if pagerduty_unacked:
        print("📟🚨")  # Show unacked alert icon even if offcall
    else:
        if oncall_response["active"]:
            print("📟☎️")  # Show oncall icon
        else:
            print("📟💤")  # Show offcall icon
    print("---")

    print_xbar_oncall_status(oncall_response, PAGER_DUTY_COMPANY, PAGER_DUTY_USER)

    if stale_data:
        print("WARNING: Data is stale, unable to update.")
        if error_msg != "":
            print(error_msg)

    print_xbar_incidents(pd_incidents)

    # Play audible alert for unacked messages last because it will delay before exit.
    if PAGER_DUTY_ALERT_SOUND and pagerduty_unacked:
        play_alert_sound(PAGER_DUTY_ALERT_SOUND)
