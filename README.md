# Marui
## A simple python webring application

**!! This is still a work in progress and not yet fully functional !!**

The goal of this is to be a simple, easy-to-config webring app with minimal dependencies outside of python. This means:
* Data is stored as flat JSON files, not in DBs
* Notifications are handled as requests to webhooks, rather than using email

Almost certainly won't scale massively, but this is really designed for webrings under ~100 members anyway :)