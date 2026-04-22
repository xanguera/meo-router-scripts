#!/usr/bin/env expect

set router "192.168.1.254"
set user   "meo"
set pass   "meo"
set action [lindex $argv 0]

if {$action ne "enable" && $action ne "disable" && $action ne "show"} {
    puts "Usage: $argv0 <enable|disable|show>"
    exit 1
}

spawn telnet $router
expect "Login:"  { send "$user\r" }
expect "Password:" { send "$pass\r" }
expect "/cli>"

if {$action eq "show"} {
    send "lan/bridge-mode/show\r"
    expect "/cli>"
} else {
    send "lan/bridge-mode/config --enable=$action\r"
    expect "/cli>"
    send "lan/bridge-mode/show\r"
    expect "/cli>"
}

# Exit: Ctrl+] drops to telnet prompt, then "quit" closes the connection
send "\x1d"
expect "telnet>"
send "quit\r"
expect eof
