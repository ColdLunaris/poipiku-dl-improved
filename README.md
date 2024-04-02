# poipiku-dl

A tool written in Python to download images from poipiku. Tested on Linux.

## Requirements

Some pip modules are needed for poipiku-dl to work. Some of them are already pre-installed on your system. Copy-paste this command and you should be good here:

`pip3 install requests beautifulsoup4`

If you still get an error for missing modules, that's when Google helps you out.

## How to use

Note that none of the arguments below are required
| Argument | Description |
| -------- | ----------- |
| `-u URL` | URL to profile to download. If not specified the script will fetch quiet follows |
| `-p PASS,WORD` | Passwords to be attempted on protected posts. Can be a comma-separated list |
| `-d DIRECTORY` | Output directory. Defaults to working directory |
| `-q` | Disables output to stdout |

For passwords "yes" will always be attempted, so there is no need to supply this
