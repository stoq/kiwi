#!/bin/sh

#
# TODO - We want these but they require some work
#
# W0302 - Module too long
# W0622 - Redefined built-in variable
# W0222 - Signature differs from overriden method
#
TODO="W0302,W0621,W0622,W0222"

#
# Disabled - We don't like this ones, turn them off
#
# F0202 - Bug in pylint
# F0203 - Bug in pylint (Unable to resolve gtk.XXXX)
# E0201 - Access to undefined member - breaks gtk'
# W0201 - Attribute 'loaded_uis' defined outside __init__
# W0223 - Method 'add' is abstract in class 'xxx' but is not overriden
# W0232 - Class has no __init__ method
# W0511 - FIXME/TODO/XXX
# W0613 - Unused argument
# W0704 - Except doesn't do anything
#
DISABLE="E0201,F0202,F0203,W0201,W0223,W0232,W0511,W0613,W0704"

MSGS="$TODO,$DISABLE"
DIRECTORY="kiwi"

pylint \
  --disable-all \
  --include-ids=y \
  --enable-variables=y \
  --enable-exceptions=y \
  --enable-miscellaneous=y \
  --enable-format=y \
  --enable-classes=y \
  --disable-msg=$MSGS \
  --reports=n \
  --enable-metrics=n \
  $DIRECTORY
