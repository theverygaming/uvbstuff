from silly.modules.webclient_nojs.view import views

views.update({
    "kiwi_list": {
        "type": "list",
        "model": "kiwi",
        "fields": [
            {
                "name": "ID",
                "field": "id",
            },
            {
                "name": "Active",
                "field": "active",
            },
            {
                "name": "Fallback",
                "field": "fallback",
            },
            {
                "name": "URL",
                "field": "url",
            },
            {
                "name": "Timeout",
                "field": "timeout",
            },
            {
                "name": "Timelimit",
                "field": "timelimit",
            },
            {
                "name": "Start Hour",
                "field": "hour_start",
            },
            {
                "name": "End hour",
                "field": "hour_end",
            },
            {
                "name": "Notes",
                "field": "notes",
            },
            {
                "name": "State: Last Update",
                "field": "state_last_update",
            },
            {
                "name": "State: Is Alive?",
                "field": "state_alive",
            },
            {
                "name": "State: Usage (0-100%)",
                "field": "state_usage",
            },
            {
                "name": "State: SNR",
                "field": "state_snr",
            },
        ],
        "pagination": {
            "default_page_size": 5,
        },
        "form_view_id": "kiwi_form",
    },
    "kiwi_form": {
        "type": "form",
        "model": "kiwi",
        "fields": [
            {
                "name": "Active",
                "field": "active",
                "type": "bool",
            },
            {
                "name": "Fallback",
                "field": "fallback",
                "type": "bool",
            },
            {
                "name": "URL",
                "field": "url",
                "type": "str",
            },
            {
                "name": "Timeout",
                "field": "timeout",
                "type": "int",
            },
            {
                "name": "Timelimit",
                "field": "timelimit",
                "type": "int",
            },
            {
                "name": "Start Hour",
                "field": "hour_start",
                "type": "int",
            },
            {
                "name": "End hour",
                "field": "hour_end",
                "type": "int",
            },
            {
                "name": "Notes",
                "field": "notes",
                "type": "str",
                "widget": {
                    "type": "textarea",
                },
            },
        ],
        "actions": [],
    },
    "kiwi_timeslot_list": {
        "type": "list",
        "model": "kiwi_timeslot",
        "fields": [
            {
                "name": "ID",
                "field": "id",
            },
            {
                "name": "Start Time",
                "field": "start",
            },
            {
                "name": "End Time",
                "field": "end",
            },
            {
                "name": "Related KiwiSDR ID",
                "field": "kiwi",
            },
        ],
        "pagination": {
            "default_page_size": 5,
        },
    },
})
