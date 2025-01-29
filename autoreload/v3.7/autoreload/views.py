from silly.modules.webclient_nojs.view import views

views.update({
    "kiwi_list": {
        "type": "list",
        "model": "kiwi",
        "fields": [
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
        ],
        "pagination": {
            "default_page_size": 5,
        },
        "form_view_id": "kiwi_form",
    },
    "kiwi_form": {
        "type": "form",
        "model": "xmlid",
        "fields": [],
        "actions": [],
    },
})
