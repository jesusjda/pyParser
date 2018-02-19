#!/bin/bash

UN=""
UP=""
FORCE=false
LOCAL=false
for i in "$@"; do
    case $i in
	-up|--update)
	    UP="up"
	    UN=""
	    shift
	    ;;
	-un|--uninstall)
	    UP=""
	    UN="un"
	    shift
	    ;;
	-f|--force)
	    FORCE=true
	    shift
	    ;;
	-l|--local)
	    LOCAL=true
	    shift
	    ;;
	*)
	    >&2 cat  <<EOF
ERROR: install.sh [OPTIONS]

[OPTIONS]

    -f | --force )
                   force default values: Install python dependencies,
                   but no install own modules like pyLPi.

    -l | --local )
                   Install local version with local modifications.
                   Otherwise, git repository version will be installed.

    -up | --update )
                   Update or Upgrade all the packages.

    -un | --uninstall )
                   Uninstall all except UNIX packages.

EOF
	    exit -1
            # unknown option
	    ;;
    esac
done


exists(){
    command -v "$1" >/dev/null 2>&1
}


flags=""

# check sudo permission
if [ "$EUID" -ne 0 ]; then
    flags=$flags" --user"
fi

# get base folder
if [ "$(uname -s)" = 'Linux' ]; then
    basedir=$(dirname "$(readlink -f "$0" )")
else
    basedir=$(dirname "$(readlink "$0" )")
fi

if [ "$FORCE" = "true" ]; then
    pdepen=true
else
    pdepen=true
    while true; do
	read -p "Do you want to "$UN"install the standar Python dependencies? [Y/n]" yn
	case $yn in
            [yY][eE][sS]|[yY])
		break;;
	    [nN][oO]|[nN])
		pdepen=false
		break;;
            "")
		break;;
            * ) echo "Invalid option."; echo $yn;;
	esac
    done
fi


install()
{
    lflags=$flags
    if [ "$UN" = "un" ]; then
	lflags=" -y"
    elif [ "$UP" = "up" ]; then
	lflags=$lflags" --upgrade"
    fi
    echo "---------------------------------"
    echo " Installing pyParser on Python 3 "
    echo "---------------------------------"
    if [ "$pdepen" = "true" ]; then
	python3 -m pip $UN"install" $lflags networkx arpeggio pyleri || return -1
    fi

    if [ "$LOCAL" = "true" ]; then
	python3 -m pip $UN"install" $lflags . || return -1
    else
	python3 -m pip $UN"install" $lflags git+https://github.com/jesusjda/pyParser.git#egg=pyParser || return -1
    fi
}

easy_install3 $flags pip
install && echo "Success!" || echo "SOME ERRORS"
