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
| `-q` | Disables output to stdout |

You can also edit `config.yml` and specify other parameters there, like passwords to attempt, cookies and output directory. The script looks for the config file in the same directory as `main.py`.
