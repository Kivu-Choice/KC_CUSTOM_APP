app_name = "kc_custom_app"
app_title = "KC Custom App"
app_publisher = "Kivu Choice"
app_description = "Custom implementation for Kivu Choice"
app_email = "huwizera@kivuchoice.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kc_custom_app",
# 		"logo": "/assets/kc_custom_app/logo.png",
# 		"title": "KC Custom App",
# 		"route": "/kc_custom_app",
# 		"has_permission": "kc_custom_app.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kc_custom_app/css/kc_custom_app.css"
# app_include_js = "/assets/kc_custom_app/js/kc_custom_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/kc_custom_app/css/kc_custom_app.css"
# web_include_js = "/assets/kc_custom_app/js/kc_custom_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kc_custom_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kc_custom_app/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kc_custom_app.utils.jinja_methods",
# 	"filters": "kc_custom_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kc_custom_app.install.before_install"
# after_install = "kc_custom_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kc_custom_app.uninstall.before_uninstall"
# after_uninstall = "kc_custom_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kc_custom_app.utils.before_app_install"
# after_app_install = "kc_custom_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kc_custom_app.utils.before_app_uninstall"
# after_app_uninstall = "kc_custom_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kc_custom_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # "Purchase Order": {
    #     "on_update": "kc_custom_app.notifications.po_pending_approval.send_po_approved_notification"
    # },
	"Purchase Invoice": {
		"on_submit": "kc_custom_app.custom_scripts.server_scripts.purchase_invoice.on_submit"
	},
	"Delivery Note": {
		"on_submit": "kc_custom_app.custom_scripts.server_scripts.delivery_note.on_submit"
	}

	# "*": {
	# 	"on_update": "method",
	# 	"on_cancel": "method",
	# 	"on_trash": "method"
	# }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    # "cron": {
    #     "0 12 * * *": [
    #         "kc_custom_app.notifications.po_pending_approval.send_pending_po_notifications"
    #     ]
    # }
	# "all": [
	# 	"kc_custom_app.tasks.all"
	# ],
	# "daily": [
	# 	"kc_custom_app.tasks.daily"
	# ],
	# "hourly": [
	# 	"kc_custom_app.tasks.hourly"
	# ],
	# "weekly": [
	# 	"kc_custom_app.tasks.weekly"
	# ],
	# "monthly": [
	# 	"kc_custom_app.tasks.monthly"
	# ],
}


fixtures = [
    "Client Script",
    "Server Script",
    "Custom Field",
    "Property Setter",
    {"dt": "Client Script", "filters": [["module", "like", "KC Custom App"]]},
    {"dt": "Server Script", "filters": [["module", "like", "KC Custom App"]]},
    {"dt": "Custom Field", "filters": [["module", "like", "KC Custom App"]]},
    {"dt": "Property Setter", "filters": [["module", "like", "KC Custom App"]]},
]
# Testing
# -------

# before_tests = "kc_custom_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "erpnext.stock.doctype.material_request.material_request.make_purchase_order":
        "kc_custom_app.custom_scripts.server_scripts.material_request.make_purchase_order"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kc_custom_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kc_custom_app.utils.before_request"]
# after_request = ["kc_custom_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["kc_custom_app.utils.before_job"]
# after_job = ["kc_custom_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kc_custom_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

