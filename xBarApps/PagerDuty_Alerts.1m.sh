#!/usr/bin/env zsh

# This wrapper is needed to execute Python scripts because the default path
# on MacOS does NOT include paths added in profile, or .zshrc files.

# Configure these two scripts for your environment.
folder="PythonScripts"
script="PagerDuty_Alerts.py"

# Code begins here.
error_msg=""
if [[ -d ${folder} ]]; then
	cd ${folder}
	if [[ -f ${script} ]]; then
		# Add Homebrew ARM64 and AMD64 paths ahead of systme incase installed.
		export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"
		# Capture output incase something goes wrong, we can return a readable error in xBar.
		output="$(./${script})"
		if [[ $? == 0 ]]; then
			echo "${output}"
			exit 0
		else
			error_msg="Failed to execute script successfully ${script}."
		fi
	else
		error_msg="Failed to find script ${script}."
	fi
else
	error_msg="Failed to find folder ${folder}."
fi

echo "☠️"
echo "---"
echo "${error_msg}"
